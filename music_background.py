#!/usr/bin/env python

import argparse
from typing import Any, Tuple

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import sys
import os

from lib.configuration import build_config, geometry, validate_config


def _get_text_size(text : str, font : ImageFont.FreeTypeFont) -> geometry:
    img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(img)
    box = draw.multiline_textbbox((0,0), text=text, font=font)
    size = geometry(int(box[2]-box[0]), int(box[3]-box[1]))
    return size

#--------------------------------------------------------------------------------
# LOGO
#--------------------------------------------------------------------------------

def _build_logo(config : Any) -> Tuple[Image.Image, Image.Image | None] | None :
    logo_config = config.get('logo', None)
    if logo_config is None :
        return None

    logo_path : str = logo_config['path']

    with Image.open(logo_path) as logo_img:

        logo_width, logo_height = logo_img.size
        needed_size : int = logo_config['size']

        if logo_width > logo_height:
            # Landscape
            new_size = (needed_size, int( needed_size * (logo_height / logo_width)))
        else:
            # Portrait
            new_size = (int(needed_size * (logo_width / logo_height)), needed_size)

        logo_img = logo_img.resize(new_size)

        gray_img = logo_img.convert('L')

        if logo_config['mask'] == 'self':
            pass
        elif logo_config['mask'] == 'black':
            gray_img = gray_img.point(lambda x : 0 if x < 10 else 255) # type: ignore
        else :
            gray_img = None

        return (logo_img, gray_img)
    
def _add_logo(config : Any, output_img : Image.Image) -> None :
    logo_img = _build_logo(config)
    if logo_img is not None:
        logo_img, mask_img = logo_img
        logo_width, logo_height = logo_img.size

        # Calculate the offset
        width_offset = config['output']['size'].width - logo_width - config['gutter']
        height_offset = config['output']['size'].height - logo_height - config['gutter']

        # Paste the logo
        if mask_img is not None:
            output_img.paste(logo_img, (width_offset, height_offset), mask=mask_img)
        else:
            output_img.paste(logo_img, (width_offset, height_offset))

#--------------------------------------------------------------------------------
# COVER
#--------------------------------------------------------------------------------

def _landscape_cover_square(cover_img : Image.Image, cover_side : int, crop : str, bg_color : Tuple[int, int, int]) -> Image.Image :
    original_width, original_height = cover_img.size
    aspect_ratio = original_width / original_height

    # Calculate the new width while keeping the aspect ratio
    new_dimension = int(cover_side * aspect_ratio)

    # Resize the image
    cover_img = cover_img.resize((new_dimension, cover_side))

    # Crop the image if necessary
    if new_dimension > cover_side:
        if crop == 'min':
            box = (0, 0, cover_side, cover_side)
        if crop == 'mid':
            offset = (new_dimension - cover_side) // 2
            box = (offset, 0, cover_side + offset, cover_side)
        elif crop == 'max':
            offset = (new_dimension - cover_side)
            box = (offset, 0, cover_side + offset, cover_side)
        cover_img = cover_img.crop(box)

    elif new_dimension < cover_side:
        box_img = Image.new("RGB", (cover_side, cover_side), bg_color)
        if crop == 'min':
            origin = (0, 0)
        if crop == 'mid':
            offset = (cover_side - new_dimension) // 2
            origin = (offset, 0)
        elif crop == 'max':
            offset = (cover_side - new_dimension)
            origin = (offset, 0)
        box_img.paste(box_img, origin)
        cover_img = box_img


    return cover_img

def _portrait_cover_square(cover_img : Image.Image, cover_side : int, crop : str, bg_color : Tuple[int, int, int]) -> Image.Image :
    original_width, original_height = cover_img.size
    aspect_ratio = original_height / original_width

    # Calculate the new width while keeping the aspect ratio
    new_height = int(cover_side * aspect_ratio)

    # Resize the image
    cover_img = cover_img.resize((cover_side, new_height))

    # Crop the image if necessary
    if new_height > cover_side:
        if crop == 'min':
            box = (0, 0, cover_side, cover_side)
        # Crop for the middle
        elif crop == 'mid':
            offset = (new_height - cover_side) // 2
            box = (0, offset, cover_side, cover_side + offset)
        elif crop == 'max':
            offset = (new_height - cover_side)
            box = (0, offset, cover_side, cover_side + offset)

        cover_img = cover_img.crop(box)

    elif new_height < cover_side:
        box_img = Image.new("RGB", (cover_side, cover_side), bg_color)
        if crop == 'min':
            origin = (0, 0)
        if crop == 'mid':
            offset = (cover_side - new_height) // 2
            origin = (0, offset)
        elif crop == 'max':
            offset = (cover_side - new_height)
            origin = (0, offset)
        box_img.paste(box_img, origin)
        cover_img = box_img

    return cover_img

def _landscape_cover_fit(config : Any) -> Image.Image:
    print("-- Landscape cover fit")
    cover_cfg = config['cover']

    required_size = config['output']['size']

    cover_img = Image.open(cover_cfg['path'])

    orig_width, orig_height = cover_img.size
    aspect_ratio = orig_width / orig_height

    # try maxxing width first
    new_width = required_size.width
    new_height = int(new_width / aspect_ratio)
    if new_height < required_size.height:
        new_width = int(required_size.height * aspect_ratio)
        new_height = required_size.height
    
    cover_img = cover_img.resize((new_width, new_height))
    if new_height > required_size.height:
        if cover_cfg['crop'] == 'min':
           height_offset = 0
        elif cover_cfg['crop'] == 'mid':
            height_offset = (new_height - required_size.height) // 2
        elif cover_cfg['crop'] == 'max':
            height_offset = new_height - required_size.height
    else :
        height_offset = 0

    if new_width > required_size.width:
        if cover_cfg['crop'] == 'min':
            width_offset = 0
        elif cover_cfg['crop'] == 'mid':
            width_offset = (new_width - required_size.width) // 2
        elif cover_cfg['crop'] == 'max':
            width_offset = new_width - required_size.width
    else :
        width_offset = 0

    if width_offset != 0 or height_offset != 0:
        box = (width_offset, height_offset, width_offset + required_size.width,
               height_offset + required_size.height)
        cover_img = cover_img.crop(box)

    return cover_img

def _portrait_cover_fit(config : Any) -> Image.Image:
    cover_cfg = config['cover']

    required_size = config['output']['size']

    cover_img = Image.open(cover_cfg['path'])

    orig_width, orig_height = cover_img.size
    aspect_ratio = orig_height / orig_width

    # try maxxing width first
    new_height = required_size.height
    new_width = int(new_height * aspect_ratio)
    if new_width < required_size.width:
        new_height = int(required_size.width / aspect_ratio)
        new_width = required_size.width
    
    cover_img = cover_img.resize((new_width, new_height))
    if new_width > required_size.width:
        if cover_cfg['crop'] == 'min':
           width_offset = 0
        elif cover_cfg['crop'] == 'mid':
            width_offset = (new_width - required_size.width) // 2
        elif cover_cfg['crop'] == 'max':
            width_offset = new_width - required_size.width
    else :
        width_offset = 0

    if new_height > required_size.height:
        if cover_cfg['crop'] == 'min':
            height_offset = 0
        elif cover_cfg['crop'] == 'mid':
            height_offset = (new_height - required_size.height) // 2
        elif cover_cfg['crop'] == 'max':
            height_offset = new_height - required_size.height
    else :
        height_offset = 0

    if width_offset != 0 or height_offset != 0:
        box = (width_offset, height_offset, width_offset + required_size.width,
               height_offset + required_size.height)
        cover_img = cover_img.crop(box)

    return cover_img

def _add_cover(config : Any, output_img : Image.Image) -> None :

    cover_cfg = config['cover']

    with Image.open(cover_cfg['path']) as cover_img:

        output_size = config['output']['size']

        if output_size.is_landscape():
            if cover_cfg['fit'] == 'cover':
                cover_img = _landscape_cover_fit(config)
            else :
                cover_img = _landscape_cover_square(cover_img, output_size.height, 
                                                cover_cfg['crop'], 
                                                config['output']['color'])
        else:
            if cover_cfg['fit'] == 'cover':
                cover_img = _portrait_cover_fit(config)
            else :
                cover_img = _portrait_cover_square(cover_img, output_size.width, 
                                               cover_cfg['crop'], 
                                               config['output']['color'])

        if config['cover']['align'] == 'min':
            position = (0,0)
        elif config['cover']['align'] == 'mid':
            if output_size.is_landscape():
                position = ((output_size.width - cover_img.width) // 2, 0)
            else:
                position = (0, (output_size.height - cover_img.height) // 2)
        elif config['cover']['align'] == 'max':
            if output_size.is_landscape():
                position = (output_size.width - cover_img.width, 0)
            else:
                position = (0, output_size.height - cover_img.height)
        else:
            raise Exception(f"Invalid cover alignment: {config['cover']['align']}")

        # Paste the cover
        output_img.paste(cover_img, position)

def build_image(config : Any) :
    # Open the image
    output_path = config['output']['path']
    output_size = config['output']['size']

    output_img = Image.new("RGB", output_size.to_tuple(), color=config['output']['color'])

    _add_cover(config, output_img)

    _add_logo(config, output_img)

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
                        help="yaml file containing configuration values. Most can then be overridden on the command line.")

    parser.add_argument("--output_path", type=str, required=False, default=None,
                        help="The path and filename on to which to write the output." 
                        " The extension given on the filename will be used to determine the format.")
    parser.add_argument("--output_size", type=str, required=False, default=None,
                        help="The size of the output image. Must be in the format 'WIDTHxHEIGHT'.")
    parser.add_argument("--output_color", type=str, required=False, default=None,
                        help="The background color of the output image. Must be in the format '#RRGGBB'.")

    parser.add_argument("--cover_path", type=str, required=False, default=None,
                        help="The path to the cover image.")
    parser.add_argument("--cover_align", type=str, required=False, default=None,
                        choices=['min', 'mid', 'max'], 
                        help="The alignment of the cover image. Default is 'min'")
    parser.add_argument("--cover_crop", type=str, required=False, default=None,
                        choices=['min', 'mid', 'max'], 
                        help="The crop of the cover image. Default is 'min'")
    parser.add_argument("--cover_fit", type=str, required=False, default=None,
                        choices=['square', 'cover'], 
                        help="The fit of the cover image. Default is 'square'")

    parser.add_argument("--logo", type=str, required=False, default=None,
                        help="The path to the logo image. If not specified, no logo will be added.")
    parser.add_argument("--logo_size", type=int, default=None, required=False,
                        help="The size of the logo image. If not specified, the logo will be scaled to 200 pixels.")
    parser.add_argument("--logo_mask", type=str, required=False, default=None,
                        choices=['self', 'black'], 
                        help="The mask algorithm to use for the logo image. Default is 'black'.")

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
    config = build_config(args)
    if not validate_config(config):
        sys.exit(1)

    build_image(config)

if __name__ == "__main__":
    run()
