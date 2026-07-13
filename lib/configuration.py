import argparse
import os
import pprint
import yaml
from typing import Any
from dataclasses import dataclass
import re

# Defaults
IMAGE_HEIGHT = 1080
IMAGE_WIDTH = 1920

LOGO_SIZE = 200

TITLE_FONT = 'DejaVuSans.ttf'
TITLE_FONT_SIZE = 200

GUTTER_SIZE = 10

def nvl(*args) -> Any :
    """
    Returns the first argument that is not None.
    If all arguments are None, returns None.
    """

    try :
        retval = next(item for item in args if item is not None)
    except StopIteration:
        retval = None

    return retval

GEOMETRY_PATTERN = re.compile(r'(\d+)x(\d+)')
@dataclass
class geometry :
    width : int
    height : int

    def to_tuple(self) -> tuple :
        return (self.width, self.height)
    
    @classmethod
    def from_string(cls, s : str | None) -> 'geometry | None' :
        if s is None :
            return None
        
        match = GEOMETRY_PATTERN.match(s)
        if match is None :
            raise ValueError(f"Invalid geometry string: {s}")

        width, height = match.groups()
        return cls(int(width), int(height))
    
    def is_square(self) -> bool :
        return self.width == self.height
    
    def is_portrait(self) -> bool :
        return self.width < self.height
    
    def is_landscape(self) -> bool :
        return self.width > self.height


def _build_default_config() -> Any :
    return {
        'output' : { 'path' : None, 'size' : geometry(IMAGE_WIDTH, IMAGE_HEIGHT), 'color' : '#000000' },
        'logo'   : { 'path' : None, 'size' : LOGO_SIZE, 'mask' : 'black' },
        'title'  : { 'text' : None, 'size' : TITLE_FONT_SIZE, 'font' : TITLE_FONT },
        'cover'  : { 'path' : None, 'align' : 'min', 'crop' : 'min', 
                    'fit' : 'square', 'color' : None },
        'gutter' : GUTTER_SIZE,
    }

def _add_supplied_config(config : Any, supplied_config : Any) :
    if 'output' in supplied_config :
        c = supplied_config['output']
        if 'path' in c :
            config['output']['path'] = c['path']
        if 'size' in c :
            config['output']['size'] = geometry.from_string(c['size'])
        if 'color' in c :
            config['output']['color'] = c['color']

    if 'logo' in supplied_config :
        c = supplied_config['logo']
        if 'path' in c :
            config['logo']['path'] = c['path']
        if 'size' in c :
            config['logo']['size'] = int(c['size'])
        if 'mask' in c :
            config['logo']['mask'] = c['mask']

    if 'title' in supplied_config :
        c = supplied_config['title']
        if 'text' in c :
            config['title']['text'] = c['text']
        if 'size' in c :
            config['title']['size'] = int(c['size'])
        if 'font' in c :
            config['title']['font'] = c['font']

    if 'cover' in supplied_config :
        c = supplied_config['cover']
        if 'path' in c :
            config['cover']['path'] = c['path']
        if 'align' in c :
            config['cover']['align'] = c['align']
        if 'crop' in c :
            config['cover']['crop'] = c['crop']
        if 'fit' in c :
            config['cover']['fit'] = c['fit']


    if 'gutter' in supplied_config :
        config['gutter'] = int(supplied_config['gutter'])

    return config

def _add_args(config : Any, args : argparse.Namespace) :
    config['output']['path'] = nvl(args.output_path, config['output']['path'])
    config['output']['size'] = nvl(geometry.from_string(args.output_size), 
                                   config['output']['size'])
    config['output']['color'] = nvl(args.output_color, config['output']['color'])

    config['logo']['path'] = nvl(args.logo, config['logo']['path'])
    config['logo']['size'] = nvl(args.logo_size, config['logo']['size'])
    config['logo']['mask'] = nvl(args.logo_mask, config['logo']['mask'])
    
    config['title']['text'] = nvl(args.title, config['title']['text'])
    config['title']['size'] = nvl(args.title_size, config['title']['size'])
    config['title']['font'] = nvl(args.title_font, config['title']['font'])

    config['cover']['path'] = nvl(args.cover_path, config['cover']['path'])
    config['cover']['align'] = nvl(args.cover_align, config['cover']['align'])
    config['cover']['crop'] = nvl(args.cover_crop, config['cover']['crop'])
    config['cover']['fit'] = nvl(args.cover_fit, config['cover']['fit'])

    config['gutter'] = nvl(args.gutter, config['gutter'])

    return config

def build_config(args : argparse.Namespace) -> Any:

    retval = _build_default_config()

    if args.config_file is not None:
        with open(args.config_file, "r") as f:
            supplied_config = yaml.safe_load(f)

        retval = _add_supplied_config(retval, supplied_config)

    retval = _add_args(retval, args)

    # some helpers. Makes the code a littler cleaner.
    # Make sure we inherit the output color
    # even if overriden in the args.
    retval['cover']['color'] = retval['output']['color']

    pprint.pprint(retval)

    return retval

def validate_config(config : Any) -> bool :
    if config['output']['path'] is None:
        print("No output path specified")
        return False
    else :
        if not os.path.exists(os.path.dirname(config['output']['path'])):
            print(f"The directory {os.path.dirname(config['output']['path'])} does not exist.")
            return False
        ext = os.path.splitext(config['output']['path'])[1]
        if ext not in ('.png', '.jpeg', '.jpg'):
            print(f"Unsupported output file type: {ext}")
            return False
    
    if config['output']['size'].is_square() :
        print("Square output is currently not supported")
        return False
    
    width, height = config['output']['size'].to_tuple()
    if width < 1 or height < 1:
        print("Invalid output size")
        return False

    if config['cover']['path'] is not None:
        if not os.path.isfile(config['cover']['path']):
            print(f"The cover image file {config['cover']['path']} does not exist.")
            return False

    if config['logo']['path'] is not None:
        if not os.path.isfile(config['logo']['path']):
            print(f"The logo image file {config['logo']['path']} does not exist.")
            return False

    return True
