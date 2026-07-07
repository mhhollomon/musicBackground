#!/usr/bin/env python

# ./music_background.py --image_path /mnt/c/DAW/REAPER/2026/JMPR\ 2026-05-02/JMPR_detail.jpg --output_path ./output_file.jpg --logo /mnt/c/Users/mhhol/Desktop/More\ Stuff/viking-treble-clef-small.png

import argparse

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import sys
import os

IMAGE_HEIGHT = 1080
IMAGE_WIDTH = 1920
LOGO_SIZE = 200

def _get_text_size(text : str, font : ImageFont.FreeTypeFont):
    img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(img)
    box = draw.multiline_textbbox((0,0), text=text, font=font)
    #offset = (-box[0], -box[1])
    size = (box[2]-box[0], box[3]-box[1])
    return size

def resize_and_square(image_path  : str , output_path : str, logo_path : str | None, logo_size : int):
    # Open the image
    with Image.open(image_path) as img:
        # Get the original dimensions
        original_width, original_height = img.size

        # Calculate the new width while keeping the aspect ratio
        new_width = int(IMAGE_HEIGHT * (original_width / original_height))

        # Resize the image
        img = img.resize((new_width, IMAGE_HEIGHT))

        # Calculate the new dimensions
        new_width, new_height = img.size

        # Calculate the offset
        offset = (new_width - IMAGE_HEIGHT) // 2

        # Crop or extend the image
        if new_width > 1080:
            img = img.crop((offset, 0, IMAGE_HEIGHT + offset, new_height))
        new_image = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), (0, 0, 0))
        new_image.paste(img, (0, 0))
        img = new_image

        if logo_path is not None:
            # Open the logo
            with Image.open(logo_path) as logo:
                # Get the logo dimensions
                logo_width, logo_height = logo.size

                resized_logo = logo.resize((int(logo_width * (logo_size / logo_height)), logo_size))
                logo_width, logo_height = resized_logo.size

                # Calculate the offset
                width_offset = IMAGE_WIDTH - logo_width - 10
                height_offset = IMAGE_HEIGHT - logo_height - 10

                # Paste the logo
                img.paste(resized_logo, (width_offset, height_offset))

        draw = ImageDraw.Draw(img)

        myFont = ImageFont.truetype('DejaVuSans.ttf', 200)
        text_size = _get_text_size("Hello", myFont)

        print(f"text_size = {text_size}")

        draw.text((IMAGE_WIDTH - text_size[0] - 10, 10), "Hello", font=myFont, fill=(255,255,255))

        # Save the image
        img.save(output_path)

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--logo", type=str, required=False, default=None)
    parser.add_argument("--logo_size", type=int, default=LOGO_SIZE)
    return parser

if __name__ == "__main__":
    image_path = sys.argv[1]
    output_path = sys.argv[2]

    parser = build_arg_parser()
    args, _ = parser.parse_known_args()

    if not os.path.isfile(args.image_path):
        print(f"The image file {args.image_path} does not exist.")
        sys.exit(1)

    resize_and_square(args.image_path, args.output_path, args.logo, args.logo_size)