#!/usr/bin/env python

# ./music_background.py --image_path /mnt/c/DAW/REAPER/2026/JMPR\ 2026-05-02/JMPR_detail.jpg --output_path ./output_file.jpg --logo /mnt/c/Users/mhhol/Desktop/More\ Stuff/viking-treble-clef-small.png

import argparse
from dataclasses import dataclass
import pprint
import yaml
from typing import Any

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import sys
import os

IMAGE_HEIGHT = 1080
IMAGE_WIDTH = 1920
LOGO_SIZE = 200
TITLE_FONT_SIZE = 200
GUTTER_SIZE = 10

@dataclass
class geometry :
    width : int
    height : int

    def to_tuple(self) -> tuple :
        return (self.width, self.height)

def _get_text_size(text : str, font : ImageFont.FreeTypeFont) -> geometry:
    img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(img)
    box = draw.multiline_textbbox((0,0), text=text, font=font)
    size = geometry(int(box[2]-box[0]), int(box[3]-box[1]))
    return size

def resize_and_square(config : Any) :
    # Open the image
    output_path = config['output']['path']
    out_image_size = config['image']['size']
    with Image.open(config['input']['path']) as cover_img:
        # Get the original dimensions
        original_width, original_height = cover_img.size

        # We want to 
        # 1. resize the cover so that it is the same height as the output image while keeping the aspect ratio
        # 2. If necessary, crop the cover so that it is square.
        #

        cover_side = out_image_size.height


        # Calculate the new width while keeping the aspect ratio
        new_width = int(cover_side * (original_width / original_height))

        # Resize the image
        cover_img = cover_img.resize((new_width, cover_side))

        # Find the new dimensions
        new_width, _ = cover_img.size

        # Crop the image if necessary
        if new_width > cover_side:
            offset = (new_width - cover_side) // 2
            # Crop for the middle
            cover_img = cover_img.crop((offset, 0, cover_side + offset, cover_side))

        output_img = Image.new("RGB", out_image_size.to_tuple(), (0, 0, 0))
        output_img.paste(cover_img, (0, 0))

        logo_config = config.get('logo', None)

        if logo_config is not None:
            # Open the logo
            with Image.open(logo_config['path']) as logo:
                # Get the logo dimensions
                logo_width, logo_height = logo.size
                needed_size = logo_config['size']

                resized_logo = logo.resize((int(needed_size * (logo_width / logo_height)), needed_size))
                logo_width, logo_height = resized_logo.size

                # Calculate the offset
                width_offset = out_image_size.width - logo_width - GUTTER_SIZE
                height_offset = out_image_size.height - logo_height - GUTTER_SIZE

                # Paste the logo
                output_img.paste(resized_logo, (width_offset, height_offset))

        text_config = config.get('text', None)
        if text_config is not None:
            draw = ImageDraw.Draw(output_img)
            myFont = ImageFont.truetype('DejaVuSans.ttf', TITLE_FONT_SIZE)
            text_size = _get_text_size(text_config['text'], myFont)

            print(f"text_size = {text_size}")

            max_text_width = out_image_size.width - out_image_size.height - (GUTTER_SIZE * 2)
            if (text_size.width > max_text_width):
                # The text is too long, so we need to scale it down
                myFont = ImageFont.truetype('DejaVuSans.ttf', TITLE_FONT_SIZE * (max_text_width / text_size.width))
                text_size = _get_text_size(text_config['text'], myFont)

            draw.text((IMAGE_WIDTH - text_size.width - GUTTER_SIZE, GUTTER_SIZE), 
                      text_config['text'], font=myFont, fill=(255,255,255))

        # Save the image
        output_img.save(output_path)

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_file", "-c", type=str, required=False, default=None)
    parser.add_argument("--image_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--logo", type=str, required=False, default=None)
    parser.add_argument("--logo_size", type=int, default=LOGO_SIZE)
    parser.add_argument("--text", type=str, required=False, default=None)
    return parser

def build_config(args : argparse.Namespace) -> Any:
    if args.config_file is not None:
        with open(args.config_file, "r") as f:
            supplied_config = yaml.safe_load(f)
    else:
        supplied_config = {}

    if 'title' in supplied_config:
        args.text = supplied_config['title'].get('text', args.text)

    if 'logo' in supplied_config:
        l = supplied_config['logo']
        args.logo = l.get('path', args.logo)
        args.logo_size = l.get('size', args.logo_size) 

    retval = { 'image' : { 'size' : geometry(IMAGE_WIDTH, IMAGE_HEIGHT) },
               'input' : { 'path' : args.image_path },
              'output' : { 'path' : args.output_path },
    }

    if args.logo is not None:
        retval['logo'] = { 'path' : args.logo, 'size' : args.logo_size }

    if args.text is not None:
        retval['text'] = {'text' : args.text}

    pprint.pprint(retval)

    return retval

def run() :
    args = build_arg_parser().parse_args()
    if not os.path.isfile(args.image_path):
        print(f"The image file {args.image_path} does not exist.")
        sys.exit(1)

    config = build_config(args)
    resize_and_square(config)

if __name__ == "__main__":
    run()
