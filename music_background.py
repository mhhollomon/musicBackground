#!/usr/bin/env python

import argparse
from typing import Any

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import sys
import os

from lib.configuration import build_config, geometry


def _get_text_size(text : str, font : ImageFont.FreeTypeFont) -> geometry:
    img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(img)
    box = draw.multiline_textbbox((0,0), text=text, font=font)
    size = geometry(int(box[2]-box[0]), int(box[3]-box[1]))
    return size

def _build_logo(config : Any) -> Image.Image | None :
    logo_config = config.get('logo', None)
    if logo_config is None :
        return None

    logo_path = logo_config['path']

    with Image.open(logo_path) as logo_img:
        logo_width, logo_height = logo_img.size
        needed_size = logo_config['size']

        logo_img = logo_img.resize((int(needed_size * (logo_width / logo_height)), needed_size))

        return logo_img

def build_image(config : Any) :
    # Open the image
    output_path = config['output']['path']
    output_size = config['output']['size']

    if output_path is None:
        print("No output path specified")
        sys.exit(1)

    with Image.open(config['cover']['path']) as cover_img:
        # Get the original dimensions
        original_width, original_height = cover_img.size

        # We want to 
        # 1. resize the cover so that it is the same height as the output image while keeping the aspect ratio
        # 2. If necessary, crop the cover so that it is square.
        #

        cover_side = output_size.height


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

        output_img = Image.new("RGB", output_size.to_tuple(), color=config['output']['color'])
        output_img.paste(cover_img, (0, 0))

        logo_config = config.get('logo', None)

        logo_img = _build_logo(config)
        if logo_img is not None:
            logo_width, logo_height = logo_img.size

            # Calculate the offset
            width_offset = output_size.width - logo_width - config['gutter']
            height_offset = output_size.height - logo_height - config['gutter']

            # Paste the logo
            output_img.paste(logo_img, (width_offset, height_offset))


        title_config = config.get('title', None)
        if title_config is not None and title_config['text'] is not None:
            draw = ImageDraw.Draw(output_img)
            myFont = ImageFont.truetype(title_config['font'], title_config['size'])
            text_size = _get_text_size(title_config['text'], myFont)

            print(f"text_size = {text_size}")

            max_text_width = output_size.width - output_size.height - (config['gutter'] * 2)
            if (text_size.width > max_text_width):
                # The text is too long, so we need to scale it down
                myFont = ImageFont.truetype('DejaVuSans.ttf', title_config['size'] * (max_text_width / text_size.width))
                text_size = _get_text_size(title_config['text'], myFont)

            draw.text((output_size.width - text_size.width - config['gutter'], config['gutter']), 
                      title_config['text'], font=myFont, fill=(255,255,255))

        # Save the image
        output_img.save(output_path)

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_file", "-c", type=str, required=False, default=None,
                        help="yaml file containing the configuration values. Most can then be overridden on the command line.")

    parser.add_argument("--output_path", type=str, required=False, default=None,
                        help="The path and filename ton to which to write the output." 
                        " The extension given on the filename will be used to determine the format.")
    parser.add_argument("--output_size", type=str, required=False, default=None,
                        help="The size of the output image. Must be in the format 'WIDTHxHEIGHT'.")
    parser.add_argument("--output_color", type=str, required=False, default=None,
                        help="The background color of the output image. Must be in the format '#RRGGBB'.")

    parser.add_argument("--cover_path", type=str, required=True,
                        help="The path to the cover image.")

    parser.add_argument("--logo", type=str, required=False, default=None,
                        help="The path to the logo image. If not specified, no logo will be added.")
    parser.add_argument("--logo_size", type=int, default=None, required=False,
                        help="The size of the logo image. If not specified, the logo will be scaled to 200 pixels.")

    parser.add_argument("--title", type=str, required=False, default=None,
                        help="The text to display in the title. If not specified, no title will be added.")
    parser.add_argument("--title_size", type=int, required=False, default=None,
                        help="The size of the title text. If not specified, the title will be scaled to 200 pixels.")
    parser.add_argument("--title_font", type=str, required=False, default=None,
                        help="The font to use for the title text. If not specified, the default font will be used.")

    parser.add_argument("--gutter", type=int, required=False, default=None,
                        help="The size of the gutter between the cover image and the title. If not specified, the gutter will be 10 pixels.")
    return parser


def run() :
    args = build_arg_parser().parse_args()
    if not os.path.isfile(args.cover_path):
        print(f"The image file {args.cover_path} does not exist.")
        sys.exit(1)

    config = build_config(args)
    build_image(config)

if __name__ == "__main__":
    run()
