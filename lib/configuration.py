import argparse
import os
import yaml
from typing import Any
from dataclasses import dataclass
import re

from .position import position, geometry

import logging
logger = logging.getLogger(__name__)

# Defaults
IMAGE_HEIGHT = 1080
IMAGE_WIDTH = 1920
LOGO_SIZE = 200
TITLE_FONT_SIZE = 200
GUTTER_SIZE = 10


class NoneDict :
    """Alway return None if the key is not found.
    Also, support path keys like 'a.b.c'
    """
    def __init__(self, config : dict) :
        self.config = config

    def __getitem__(self, key) -> Any :
        keys = key.split('.')
        value = self.config
        for k in keys :
            if k in value :
                value = value[k]
            else :
                return None
            if not isinstance(value, dict) :
                return value
        return value

    def __contains__(self, key) :
        return key in self.config



class Settings :

    def valid_value(self, value : Any) -> bool :

        if value is None :
            return False
        
        if isinstance(value, str) :
            return value.strip() != ''
        
        try :
            return value.valid()
        except AttributeError :
            pass

        return True
    
    def valid_attr(self, key : str) -> bool :
        return self.valid_value(getattr(self, key))
    
    def override(self, key : str, new_value : Any) :
        """Update the value of the attribute if the NEW value is NOT None."""
        logger.debug(f"--- override ??? : {key} ??? {new_value}")
        if self.valid_value(new_value) :
            logger.debug(f"--- override !!! : set {key} to {new_value}")
            setattr(self, key, new_value)

    def default(self, key : str, new_value : Any) :
        """Update the value of the attribute if the OLD value is None."""
        old_value = getattr(self, key)
        if not self.valid_value(old_value) :
            setattr(self, key, new_value)

class PathSetting(Settings) :
    def path_valid(self) -> bool :
        path = getattr(self, 'path')
        return path is not None and path != ''

@dataclass
class GlobalSettings(Settings) :
    gutter : int
    font : str

@dataclass
class OutputSettings(PathSetting) :
    path : str
    size : geometry
    color : str
    background : str

@dataclass
class BorderSettings(Settings) :
    color : str
    width : int

    def exists(self) -> bool :
        return self.width > 0

@dataclass
class CoverSettings(PathSetting) :
    path : str
    align : str
    crop : str
    fit : str
    color : str | None # This is a convenience attribute
    border : BorderSettings
    margin : int

@dataclass
class LogoSettings(PathSetting) :
    path : str
    size : int
    mask : str
    position : position

@ dataclass
class StrokeSettings(Settings) :
    color : str
    width : int

    def exists(self) -> bool :
        return self.width > 0

@dataclass 
class TextSettings(Settings) :
    text : str
    size : int
    font : str
    position : position
    fill : str
    stroke : StrokeSettings

    def has_text(self) -> bool :
        return self.text is not None and self.text != ''

@dataclass
class Config(Settings) :
    globals : GlobalSettings
    output  : OutputSettings
    cover   : CoverSettings
    logo    : LogoSettings
    title   : TextSettings
    album   : TextSettings

def _build_default_config() -> Config :

    return Config(
        globals = GlobalSettings(GUTTER_SIZE, ''),
        output  = OutputSettings("", geometry(IMAGE_WIDTH, IMAGE_HEIGHT), '#000000', background = ''),
        cover   = CoverSettings('', 'min', 'min', 'square', None, 
                                BorderSettings('#000000', 0), margin=0),
        logo    = LogoSettings('', LOGO_SIZE, 'black', position('right-bottom')),
        title   = TextSettings('', TITLE_FONT_SIZE, '', 
                                position('right-top'), 
                                '#ffffff', 
                                StrokeSettings('#ffffff', 0)),
        album   = TextSettings('', TITLE_FONT_SIZE // 2, '', 
                                position('right-center'), 
                                '#ffffff', 
                                StrokeSettings('#ffffff', 0)),
    )

def _add_supplied_config(config : Config, new_cfg : NoneDict) :
    config.globals.override('gutter', new_cfg['gutter'])
    config.globals.override('font', new_cfg['font'])

    config.output.override('path', new_cfg['output.path'])
    config.output.override('size', geometry.from_string(new_cfg['output.size']))
    config.output.override('color', new_cfg['output.color'])
    config.output.override('background', new_cfg['output.background'])

    config.cover.override('path', new_cfg['cover.path'])
    config.cover.override('align', new_cfg['cover.align'])
    config.cover.override('crop', new_cfg['cover.crop'])
    config.cover.override('fit', new_cfg['cover.fit'])
    config.cover.border.override('color', new_cfg['cover.border.color'])
    config.cover.border.override('width', new_cfg['cover.border.width'])
    config.cover.override('margin', new_cfg['cover.margin'])

    config.logo.override('path', new_cfg['logo.path'])
    config.logo.override('size', new_cfg['logo.size'])
    config.logo.override('mask', new_cfg['logo.mask'])
    config.logo.override('position', position(new_cfg['logo.position']))

    config.title.override('text', new_cfg['title.text'])
    config.title.override('size', new_cfg['title.size'])
    config.title.override('font', new_cfg['title.font'])
    config.title.override('position', position(new_cfg['title.position']))
    config.title.override('fill', new_cfg['title.fill'])
    config.title.stroke.override('color', new_cfg['title.stroke.color'])
    config.title.stroke.override('width', new_cfg['title.stroke.width'])

    config.album.override('text', new_cfg['album.text'])
    config.album.override('size', new_cfg['album.size'])
    config.album.override('font', new_cfg['album.font'])
    config.album.override('position', position(new_cfg['album.position']))
    config.album.override('fill', new_cfg['album.fill'])
    config.album.stroke.override('color', new_cfg['album.stroke.color'])
    config.album.stroke.override('width', new_cfg['album.stroke.width'])

    return config

def _add_args(config : Config, args : argparse.Namespace) :
    config.globals.override('gutter', args.gutter)
    config.globals.override('font', args.font)

    config.output.override('path', args.output_path)
    config.output.override('size', geometry.from_string(args.output_size))
    config.output.override('color', args.output_color)
    config.output.override('background', args.output_background)

    config.cover.override('path', args.cover_path)
    config.cover.override('align', args.cover_align)
    config.cover.override('crop', args.cover_crop)
    config.cover.override('fit', args.cover_fit)
    config.cover.border.override('color', args.cover_border_color)
    config.cover.border.override('width', args.cover_border_width)
    config.cover.override('margin', args.cover_margin)

    config.logo.override('path', args.logo)
    config.logo.override('size', args.logo_size)
    config.logo.override('mask', args.logo_mask)
    config.logo.override('position', position(args.logo_position))
    
    config.title.override('text', args.title)
    config.title.override('size', args.title_size)
    config.title.override('font', args.title_font)
    config.title.override('position', position(args.title_position))
    config.title.override('fill', args.title_fill)
    config.title.stroke.override('color', args.title_stroke_color)
    config.title.stroke.override('width', args.title_stroke_width)

    config.album.override('text', args.album)
    config.album.override('size', args.album_size)
    config.album.override('font', args.album_font)
    config.album.override('position', position(args.album_position))
    config.album.override('fill', args.album_fill)
    config.album.stroke.override('color', args.album_stroke_color)
    config.album.stroke.override('width', args.album_stroke_width)

    return config

def _get_default_font() :
    #import sys
    import platform
    #print(f"==== sys.platform: {sys.platform}")
    #print(f"==== platform: {platform.platform()}")
    if 'WSL2' in platform.platform():
        return '/mnt/c/Windows/Fonts/arial.ttf'
    else:
        return 'Arial'

def build_config(args : argparse.Namespace) -> Config:

    retval = _build_default_config()

    if args.config_file is not None:
        with open(args.config_file, "r") as f:
            supplied_config = yaml.safe_load(f)

        retval = _add_supplied_config(retval, NoneDict(supplied_config))

    retval = _add_args(retval, args)

    # HELPER
    # Makes the code a littler cleaner. cover color is not
    # actually settable by the user.
    # Make sure we inherit the output color
    # even if overridden in the args.
    retval.cover.color = retval.output.color

    # set a default font that depends on the platform
    retval.globals.default('font', _get_default_font())

    # update the other fonts to use this if needed.
    retval.title.default('font', retval.globals.font) 
    retval.album.default('font', retval.globals.font) 

    print("++ Using configuration:")
    dump = yaml.dump(retval, default_flow_style=False, sort_keys=False)
    dump = re.sub(r'\s?!![^\n]*\n', '\n', dump)
    print(dump)


    return retval

def validate_config(config : Config) -> bool :
    if not config.output.path_valid():
        logger.error("No output path specified")
        return False
    else :
        output_path = config.output.path
        dirname = os.path.dirname(output_path)
        if dirname != "" and not os.path.exists(dirname) :
            logger.error(f"The directory {dirname} does not exist.")
            return False
        ext = (os.path.splitext(output_path)[1]).lower()
        if ext not in ('.png', '.jpeg', '.jpg', 'webp'):
            logger.error(f"Unsupported output file type: {ext}")
            return False
    
    if config.output.size.is_square() :
        logger.error("Square output is currently not supported")
        return False
    
    width, height = config.output.size.to_tuple()
    if width < 1 or height < 1:
        logger.error("Invalid output size")
        return False
    
    if config.output.valid_attr('background'):
        path = config.output.background
        if not os.path.isfile(path):
            logger.error(f"The background image file {path} does not exist.")
            return False

    if config.cover.path_valid():
        cover_path = config.cover.path
        if not os.path.isfile(cover_path):
            logger.error(f"The cover image file {cover_path} does not exist.")
            return False

    if config.logo.path_valid():
        logo_path = config.logo.path
        if not os.path.isfile(logo_path):
            logger.error(f"The logo image file {logo_path} does not exist.")
            return False
        if config.logo.size < 0:
            logger.error("Logo size must be >= 0")
            return False
        if config.logo.mask not in ('self', 'black', 'alpha', 'auto', 'none'):
            logger.error("Invalid logo mask value")
            return False

    if config.title.has_text():
        if config.title.stroke.width < 0:
            logger.error("Title stroke width must be >= 0")
            return False
        
    if config.album.has_text():
        if config.album.stroke.width < 0:
            logger.error("Album stroke width must be >= 0")
            return False
        
    if config.globals.gutter < 0:
        logger.error("Gutter must be >= 0")
        return False
    
    if config.cover.border.width < 0:
        logger.error("Cover border width must be >= 0")
        return False

    return True
