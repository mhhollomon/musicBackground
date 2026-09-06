from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, List

from .position import position
from .geometry import sizet

from .utils import dictmerge


import logging
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# BASE CLASS Settings
# -------------------------------------------------------------------------
class SettingsBase :
    __REQ_ARGS__ = ()

    @classmethod
    def check_args(cls, input : dict) :
        failed : set[str] = set()
        for k in cls.__REQ_ARGS__ :
            if k not in input :
                failed.add(k)
        if failed :
            name = input.get('name', 'unknown')
            raise ValueError(f"Setting for '{name}' is missing required arguments: {failed} :\n{input}")



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
        if self.valid_value(new_value) :
            setattr(self, key, new_value)

    def default(self, key : str, new_value : Any) :
        """Update the value of the attribute if the OLD value is None."""
        old_value = getattr(self, key)
        if not self.valid_value(old_value) :
            setattr(self, key, new_value)

    def print(self, prefix : str = '') :
        print(f"{prefix}{str(self)}")


# -------------------------------------------------------------------------

class PathSetting(SettingsBase) :
    def path_valid(self) -> bool :
        path = getattr(self, 'path')
        return path is not None and path != ''


# -------------------------------------------------------------------------

@dataclass
class DefaultSettings(SettingsBase) :
    font : str
    fill : str

    def print(self, prefix : str = '') :
        print(f"{prefix}DefaultSettings {{")
        new_prefix = prefix + '  '
        print(f"{new_prefix}font = {self.font}")
        print(f"{new_prefix}fill = {self.fill}")
        print(f"{prefix}}}")

    def to_dict(self) :
        return { 'font' : self.font, 'fill' : self.fill }

# -------------------------------------------------------------------------

class WidthSettings(SettingsBase) :
    l : int = 0
    r : int = 0
    t : int = 0
    b : int = 0

    def __init__(self, l : int = 0, r : int = 0, t : int = 0, b : int = 0) :
        self.l = l
        self.r = r
        self.t = t
        self.b = b

    def is_zero(self) :
        return self.l < 1 and self.r < 1 and self.t < 1 and self.b < 1

    def all_sides_same(self) :
        """Check if all sides are the same width."""
        return self.l == self.r and self.r == self.t and self.t == self.b

    def __str__(self) :
        string = "width {"
        settings = [f"{attr}={getattr(self, attr)}" for attr in ('l', 'r', 't', 'b') if getattr(self, attr) > 0]
        string += ', '.join(settings)
        string += '}'
        return string


# -------------------------------------------------------------------------

@dataclass
class BorderSettings(SettingsBase) :
    __REQ_ARGS__ = ('color', 'width')
    color : str
    width : WidthSettings
    round : int = 0

    @classmethod
    def from_dict(cls, d : dict) :
        cls.check_args(d)
        d['width'] = WidthSettings(**d['width']) if 'width' in d else WidthSettings()
        return cls(**d)

    def exists(self) -> bool :
        return self.width is not None and not self.width.is_zero()

    def validate(self) -> bool :
        # if there is a width we have to have a color
        if self.width is not None :
            #self.width.validate()
            if self.color is None :
                raise ValueError("Border has width but no color")

        return True
        
    def print(self, prefix : str = '') :
        print(f"{prefix}border {{")
        new_prefix = prefix + '  '
        if self.color is not None :
            print(f"{new_prefix}color = {self.color}")
        if self.width is not None :
            self.width.print(new_prefix)
        print(f"{prefix}}}")

    def __str__(self) :
        string = "border {"
        if self.color is not None :
            string += f"color={self.color}"
        if self.width is not None :
            string += f", {self.width}"
        string += '}'
        return string

# -------------------------------------------------------------------------

@dataclass
class OutputSettings(PathSetting) :
    __REQ_ARGS__ = ('size',)
    size : sizet
    path : str | None = None
    color : str = 'black'
    background : str | None = None
    margin : int = 0
    fit : str = 'contain'
    border : BorderSettings | None = None

    @classmethod
    def from_dict(cls, d : dict) :
        cls.check_args(d)
        if 'border' in d :
            d['border'] = BorderSettings.from_dict(d['border'])

        return cls(**d)        

    def print(self, prefix: str = ''):
        print(f"{prefix}OutputSettings {{")
        new_prefix = prefix + '  '
        print(f"{new_prefix}path = {self.path}")
        print(f"{new_prefix}size = {self.size}")
        print(f"{new_prefix}fit = {self.fit}")
        print(f"{new_prefix}color = {self.color}")
        if self.background is not None :
            print(f"{new_prefix}background = {self.background}")
        print(f"{new_prefix}margin = {self.margin}")
        if self.border is not None :
            self.border.print(new_prefix)
        print(f"{prefix}}}")

# -------------------------------------------------------------------------

@dataclass
class ImageSettings(PathSetting) :
    __REQ_ARGS__ = ('name', 'size', 'position')
    name : str
    size : sizet | tuple[str, Any]
    position : position
    # contain, fill, stretch
    fit : tuple = ('fill', ('mid',))
    mask : str = 'auto'
    zorder : int = 0
    # legal to have no path - just a background color.
    # but one of the two needs to be set.
    path : str | None = None
    color : str | None = None
    border : BorderSettings | None = None
    margin : int = 0
    rotation : int = 0
    transform : tuple | None = None 

    @classmethod
    def from_dict(cls, d : dict) -> 'ImageSettings' :
        cls.check_args(d)
        d['position'] = position(d['position'])
        if 'border' in d :
            d['border'] = BorderSettings.from_dict(d['border'])
        try :
            t = ImageSettings(**d)
        except Exception as e :
            raise ValueError(f"Invalid image settings: {d} : {e}") from None
        return t

    def has_border(self) -> bool :
        return self.border is not None and not self.border.width.is_zero()
    
    def print(self, prefix : str = '') :
        print(f"{prefix}image \"{self.name}\" {{")
        new_prefix = prefix + '  '
        if self.zorder != 0 :
            print(f"{new_prefix}zorder = {self.zorder}")            
        print(f"{new_prefix}path = {self.path}")
        print(f"{new_prefix}size = {self.size}")
        if self.transform :
            print(f"{new_prefix}transform = {self.transform}")
        if self.color is not None :
            print(f"{new_prefix}color = \"{self.color}\"")
        print(f"{new_prefix}mask = {self.mask}")
        print(f"{new_prefix}position = {self.position}")
        print(f"{new_prefix}fit = {self.fit}")
        if self.border is not None :
            self.border.print(new_prefix)
        if self.margin > 0 :
            print(f"{new_prefix}margin = {self.margin}")
        print(f"{prefix}}}")


# -------------------------------------------------------------------------

@ dataclass
class StrokeSettings(SettingsBase) :
    color : str | None = None
    width : int | None = None


    def exists(self) -> bool :
        return self.width is not None

    def __str__(self) :
        string = "stroke {"
        if self.color is not None :
            string += f"color={self.color}"
        if self.width is not None :
            string += f", width={self.width}"
        string += '}'
        return string


# -------------------------------------------------------------------------
@dataclass 
class TextSettings(SettingsBase) :
    __REQ_ARGS__ = ['name', 'text', 'size', 'font', 'position', 'fill']
    name : str
    text : str
    size : int
    font : str
    position : position
    fill : str
    zorder : int = 0
    gap  : int = 0
    border : BorderSettings | None = None
    color : str | None = None
    stroke : StrokeSettings | None = None
    rotation : int = 0

    @classmethod
    def from_dict(cls, d : dict) -> 'TextSettings' :
        cls.check_args(d)
        d['position'] = position(d['position'])
        if 'stroke' in d :
            d['stroke'] = StrokeSettings(**d['stroke'])
        if 'border' in d :
            d['border'] = BorderSettings.from_dict(d['border'])
        try :
            t = TextSettings(**d)
        except Exception as e :
            raise ValueError(f"Invalid text settings: {d} : {e}") from e
        return t

    def has_border(self) -> bool :
        return self.border is not None and not self.border.width.is_zero()

    def print(self, prefix : str = '') :
        print(f"{prefix}text \"{self.name}\" {{")
        new_prefix = prefix + '  '
        if self.zorder > 0 :
            print(f"{new_prefix}zorder = {self.zorder}")
        print(f"{new_prefix}text = \"{self.text}\"")
        print(f"{new_prefix}size = {self.size}")
        print(f"{new_prefix}font = {self.font}")
        if self.color is not None :
            print(f"{new_prefix}color = {self.color}")
        if self.border is not None :
            self.border.print(new_prefix)
        print(f"{new_prefix}position = {self.position}")
        print(f"{new_prefix}fill = {self.fill}")
        if self.gap > 0 :
            print(f"{new_prefix}gap = {self.gap}")
        if self.color is not None :
            print(f"{new_prefix}color = {self.color}")
        if self.stroke is not None :
            self.stroke.print(new_prefix)
        print(f"{new_prefix}rotation = {self.rotation}")
        print(f"{prefix}}}")

    def has_text(self) -> bool :
        return self.text is not None and self.text != ''


#--------------------------------------------------------------------------
@dataclass
class GlobalSettings(SettingsBase) :
    zorder : str = 'asc'

    @classmethod
    def from_dict(cls, d : dict) -> 'GlobalSettings' :
        cls.check_args(d)
        try :
            t = GlobalSettings(**d)
        except Exception as e :
            raise ValueError(f"Invalid global settings: {d} : {e}") from e
        return t

    def print(self, prefix : str = '') :
        print(f"{prefix}set zorder {self.zorder}")

# -------------------------------------------------------------------------
# Settings CLASS
# -------------------------------------------------------------------------

class Settings(SettingsBase) :
    # defaults : DefaultSettings
    # globals : GlobalSettings
    # output  : OutputSettings
    # elements  : List[TextSettings | ImageSettings]
    # grid : str | None

    def __init__(self, setting : dict[str, Any]) :
        super().__init__()
        self.defaults = DefaultSettings(**setting['defaults'])
        self.output = OutputSettings.from_dict(setting['output'])
        self.globals = GlobalSettings.from_dict(setting['globals'])
        if 'grid' in setting :
            self.grid = setting['grid']
        else :
            self.grid = None
        self.elements = []
        for e in setting['elements'] :
            etype = e['type']
            del e['type']
            if etype == 'text' :
                self.elements.append(TextSettings.from_dict(e))
            elif etype == 'image' :
                self.elements.append(ImageSettings.from_dict(e))
            else :
                raise ValueError(f"Unknown element type: {etype}")

    def print(self, prefix : str = '') :
        print(f"{prefix}Config:")
        prefix += '  '
        self.defaults.print(prefix)
        self.output.print(prefix)
        for e in self.elements :
            e.print(prefix)

