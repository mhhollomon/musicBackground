
import argparse
import pprint
import yaml
from typing import Any
from dataclasses import dataclass

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
        width, height = s.split('x')
        return cls(int(width), int(height))


def _build_default_config() -> Any :
    return {
        'output' : { 'path' : None, 'size' : geometry(IMAGE_WIDTH, IMAGE_HEIGHT), 'color' : '#000000' },
        'logo'   : { 'path' : None, 'size' : LOGO_SIZE },
        'title'  : { 'text' : None, 'size' : TITLE_FONT_SIZE, 'font' : TITLE_FONT },
        'cover'  : { 'path' : None },
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

    if 'gutter' in supplied_config :
        config['gutter'] = int(supplied_config['gutter'])

    return config

def _add_args(config : Any, args : argparse.Namespace) :
    config['output']['path'] = nvl(args.output_path, config['output']['path'])
    config['output']['size'] = nvl(geometry.from_string(args.output_size), config['output']['size'])
    config['output']['color'] = nvl(args.output_color, config['output']['color'])

    config['logo']['path'] = nvl(args.logo, config['logo']['path'])
    config['logo']['size'] = nvl(args.logo_size, config['logo']['size'])
    
    config['title']['text'] = nvl(args.title, config['title']['text'])
    config['title']['size'] = nvl(args.title_size, config['title']['size'])
    config['title']['font'] = nvl(args.title_font, config['title']['font'])

    config['cover']['path'] = nvl(args.cover_path, config['cover']['path'])

    config['gutter'] = nvl(args.gutter, config['gutter'])

    return config

def build_config(args : argparse.Namespace) -> Any:

    retval = _build_default_config()

    if args.config_file is not None:
        with open(args.config_file, "r") as f:
            supplied_config = yaml.safe_load(f)

        retval = _add_supplied_config(retval, supplied_config)

    retval = _add_args(retval, args)

    pprint.pprint(retval)

    return retval
