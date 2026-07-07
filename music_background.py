#!/usr/bin/env python

# ./music_background.py --image_path /mnt/c/DAW/REAPER/2026/JMPR\ 2026-05-02/JMPR_detail.jpg --output_path ./output_file.jpg --logo /mnt/c/Users/mhhol/Desktop/More\ Stuff/viking-treble-clef-small.png

import argparse

from PIL import Image
import sys
import os

IMAGE_HEIGHT = 1080
IMAGE_WIDTH = 1920
LOGO_SIZE = 200

def resize_and_square(image_path  : str , output_path : str, logo_path : str | None):
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

                resized_logo = logo.resize((int(logo_width * (LOGO_SIZE / logo_height)), LOGO_SIZE))
                logo_width, logo_height = resized_logo.size

                # Calculate the offset
                width_offset = IMAGE_WIDTH - logo_width - 10
                height_offset = IMAGE_HEIGHT - logo_height - 10

                # Paste the logo
                img.paste(resized_logo, (width_offset, height_offset))

        # Save the image
        img.save(output_path)

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--logo", type=str, required=False, default=None)
    return parser

if __name__ == "__main__":
    image_path = sys.argv[1]
    output_path = sys.argv[2]

    parser = build_arg_parser()
    args, _ = parser.parse_known_args()

    if not os.path.isfile(args.image_path):
        print(f"The image file {args.image_path} does not exist.")
        sys.exit(1)

    resize_and_square(args.image_path, args.output_path, args.logo)