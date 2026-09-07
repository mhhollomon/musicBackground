from argparse import Namespace
from copy import deepcopy
import re
from typing import Any, NamedTuple
from uuid import uuid4

from lark import Transformer, v_args, Token, logger as lark_logger
import logging

from .paths import resolve_path
from .parsers import get_parser

lark_logger.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

from .settings import *
from .utils import dictmerge

from pathlib import Path

def _get_default_font() :
    #import sys
    import platform
    if 'WSL2' in platform.platform():
        return '/mnt/c/Windows/Fonts/arial.ttf'
    else:
        return 'Arial'


MINMAX_SETTINGS = ('min', 'mid', 'max')

class OptionTuple(NamedTuple) :
    name : str
    value : Any

class DefaultOption(NamedTuple) :
    name : str
    value : Any

class SettingsOption(NamedTuple) :
    name : str
    value : Any

class MuParseError(Exception) :
    def __init__(self, msg) :
        super().__init__(self, msg)

_uuids : set[str] = set()
def _random_name(prefix : str = '__a') :
    while True :
        u = prefix + uuid4().hex[:8]
        if u not in _uuids :
            _uuids.add(u)
            return u

#--------------------------------------------------------------------------

class Configuration(Transformer) :

    def __init__(self, config_file : str | Path, args : Namespace | None = None) :
        super().__init__()
        self._config_file = Path(config_file)

        self.context = self._config_file.parent
        self.args = args

        self.last_element_name : str | None = None
        self.template : dict[str, tuple] = {}

    def read_config(self) -> Settings :
        settings_dict = self._get_settings()

        # Handle commandline args last so they can
        # override the config file.

        if self.args is not None :
            if 'output_path' in self.args and self.args.output_path is not None :
                # Don't use resolve_path() on the path coming from the command line
                # Let the OS use its normal rules. THis will be less surprising for
                # the user.
                settings_dict['output']['path'] = self.args.output_path

            if 'grid' in self.args and self.args.grid is not None :
                logger.debug("Setting grid in read_config")
                settings_dict['grid'] = self.args.grid

        settings_dict = self._handle_defaults(settings_dict)

        return Settings(settings_dict)

    def _handle_defaults(self, input : dict) -> dict :
        defaults = { 'font' : _get_default_font(), 'fill' : 'white' }
        defaults = dictmerge(defaults, input['defaults'])
        input['defaults'] = defaults
        logger.debug(f"updated default settings = {defaults}")
        new_ele = []
        for i, e in enumerate(input['elements'] ):
            if e['type'] == 'text' :
                z = deepcopy(defaults)
                dictmerge(z, e)
                new_ele.append(z)
            elif e['type'] == 'image' :
                if 'content' in e and 'file' in e['content']:
                    e['content']['file'] = resolve_path(e['content']['file'], self.context)
                new_ele.append(e)
        input['elements'] = new_ele

        # -- background path
        if 'background' in input['output'] :
            input['output']['background'] = resolve_path(input['output']['background'], self.context)

        # -- output path
        if 'path' in input['output'] :
            input['output']['path'] = resolve_path(input['output']['path'], self.context)

        return input

    def _get_settings(self) -> dict[str, Any] :
        """Parse the configuration file.
        This is the lower level routine that actually does the parsing.
        It returns a dictionary of setting. That can be merged with includes, etc."""

        parser = get_parser('config')

        with open(self._config_file, 'r') as f :
            text = f.read()

        tree = parser.parse(text)
        settings = self.transform(tree)
        if 'include' in settings :
            base_settings = settings['include']
            del settings['include']
            settings = dictmerge(base_settings, settings)
            self._reconcile_elements(settings)
        return settings

    def _reconcile_elements(self, settings : dict[str, Any]) -> None:
        """Run through the element list merging later copies of the same name/type
        with earlier ones."""
        new_list = []
        seen : set[int] = set()
        for index, e in enumerate(settings['elements']) :
            if index in seen :
                continue
            if 'name' in e  and index < len(settings['elements'])-1 :
                other = next(((i, x) for i, x in enumerate(settings['elements'][index+1:]) if 'name' in x and x['name'] == e['name']
                               and x['type'] == e['type']), None)
                if other is None :
                    new_list.append(e)
                else :
                    seen_index = other[0] + index+1
                    seen.add(seen_index)
                    new_e = deepcopy(e)
                    new_e = dictmerge(new_e, other[1])
                    new_list.append(new_e)
                    seen.add(index)
            else :
                new_list.append(e)

            # Run through the new list and make sure there aren't two elements of the same
            # name.
            name_seen : set[str] = set()
            for i, e in enumerate(new_list) :
                if 'name' in e :
                    if e['name'] in name_seen :
                        raise ValueError(f"Duplicate element name: {e['name']}")
                    name_seen.add(e['name'])

        settings['elements'] = new_list

    def _util_consolidate(self, stype : str, children : list|tuple, extras:dict = {}) -> OptionTuple:
        """Turns a list of OptionTuples into a dictionary and returns an OptionTuple.
        Checks for duplicates."""

        settings = {**extras}
        for child in children :
            if isinstance(child, OptionTuple) :
                if child.name in settings :
                    raise ValueError(f"Duplicate {stype} statement: {child}")
                
                settings[child.name] = child.value
            else :
                raise ValueError(f"Invalid {stype} statement: {child}")

        return OptionTuple(stype, settings)
    
    #--------------------------------------------
    # Lark Transform routines
    #--------------------------------------------

    def __default__(self, data, children, meta) :
        if data.endswith('_option') :
            if data.endswith('_int_option') :
                data = data[:-11]
                return OptionTuple(data, int(children[0].value))
            else :
                data = data[:-7]
                value = children[0].value if isinstance(children[0], Token) else children[0]
                return OptionTuple(data, value)
            
        elif data.endswith('_spec') :
            data = data[:-5]
            return self._util_consolidate(data, children)

        elif data.endswith('_stmt') :
            data = data[:-5]
            return self._util_consolidate(data, children)

        return super().__default__(data, children, meta)

    def ESCAPED_STRING(self, token : Token) -> Token :

        string = token.value[1:-1]
        string = re.sub(r'\\\\n', '\n', string)
        token.value = string
        return token

    def STRING_VALUE(self, token : Token) -> Token :
        if token.value.startswith('"') :
            token.value = token.value[1:-1]
        return token

    def mupic_config_file(self, children) -> dict:
        settings = {'defaults':{}, 'globals':{}, 'elements':[] }

        queue = list(reversed(children))
        while queue :
            child = queue.pop()
            if child is None :
                continue
            elif isinstance(child, list) :
                queue.extend(child)
            elif isinstance(child, OptionTuple) :
                if child.name in ('text', 'image'):
                    settings['elements'].append(child.value)
                else :
                    settings[child.name] = child.value
            elif isinstance(child, DefaultOption) :
                settings['defaults'][child.name] = child.value
            elif isinstance(child, SettingsOption) :
                settings['globals'][child.name] = child.value
            else :
                raise ValueError(f"Invalid top-level statement: {child}")

        return settings

    @v_args(inline=True)
    def default_stmt(self, name : Token, value : Token) :
        name = name.value
        dvalue = value.value
        if name not in ('fill', 'font') :
            raise MuParseError(f"Unknown default option `{name}`.")
        return DefaultOption(name, dvalue)

    @v_args(inline=True)
    def zorder_stmt(self, value : Token) :
        dvalue = value.value.lower()
        if dvalue not in ('asc', 'desc') :
            raise MuParseError(f"zorder setting must be one of 'asc' or 'desc' - invalid value `{dvalue}`")
        return SettingsOption('zorder', dvalue)

    @v_args(inline=True)
    def size_2d_option(self, value : Token) -> OptionTuple:
        return OptionTuple('size', sizet(value.value))
    
    @v_args(inline=True)
    def one_side(self, side : Token, value : Token) -> OptionTuple:
        return OptionTuple(side.value, value.value)
        

    def width_spec(self, children) -> OptionTuple :
        settings = {}
        if len(children) == 1 and isinstance(children[0], Token) :
            size = int(children[0].value)
            settings = {'l':size, 'r':size, 't':size, 'b':size}
        else :
            for child in children :
                if isinstance(child, OptionTuple) :
                    settings[child.name] = int(child.value)
                else :
                    raise MuParseError(f"Invalid width spec: {child}")
        return OptionTuple('width', settings)

    #
    # border = <color> , <width>
    #
    @v_args(inline=True)
    def simple_border(self, color : Token, width : Token) -> OptionTuple:
        width_tuple = self.width_spec([width])
        color_tuple = OptionTuple('color', color.value)
        return self._util_consolidate('border', (width_tuple, color_tuple))

    #
    # size = scale, <float>
    #
    @v_args(inline=True)
    def scale_size(self, value : Token) -> OptionTuple:
        fvalue = float(value.value)
        if fvalue <= 0 :
            raise MuParseError(f"scale factor must be greater than zero (`{fvalue}`)")
        return OptionTuple("size", ("scale", fvalue))

    #
    # size = max
    # size = maxsquare
    #
    @v_args(inline=True)
    def size_max(self, stype : Token) -> OptionTuple:
        type_str = stype.value.lower()
        return OptionTuple("size", (type_str,))

    @v_args(inline=True)
    def image_stmt(self, name_token : Token, zorder_token : Token, *children) -> OptionTuple:
        logger.debug(f"process image_stmt : {name_token}")
        settings = self._util_consolidate('image', children, extras={'type':'image'})

        if name_token is None : 
            name = _random_name()
        else :
            name = name_token.value
            if name.startswith('"') :
                name = name[1:-1]
            if name.startswith('__') :
                MuParseError(f"element name cannot start with __ `{name}`")
        
        settings.value['name'] = name
        self.last_element_name = name

        if zorder_token is not None :
            svalue = zorder_token.value.lower()
            if '.' in svalue or 'e' in svalue :
                MuParseError(f"zorder number must be a simple integer (`{svalue}`)")
            settings.value['zorder'] = int(svalue)
        return settings

    #
    # fit = stretch
    # fit = contain, <alignment>
    # fit = fill, <alignment>
    #
    @v_args(inline=True)
    def fit_option(self, type_token : Token, align_token : Token | None) :
        ftype = type_token.value.lower()
        if ftype not in ('stretch', 'contain', 'fill') :
            raise MuParseError(f"Invalid fit option `{ftype}`")

        align = None
        if align_token :
            if ftype == 'stretch' :
                raise MuParseError("`stretch` fit option does not take a value.")

            align = align_token.value.lower()
            if align not in MINMAX_SETTINGS :
                raise MuParseError(f"Invalid align setting for `{ftype}` `{align}`")
        elif ftype in  ('contain', 'fill'):
            raise MuParseError("`{ftype}` fit option requires an alignment value.")

            
        return OptionTuple('fit', (ftype, align))


    #
    # transform = scale, <xfactor>, <yfactor>
    #
    @v_args(inline=True)
    def transform_scale(self, xfactor : Token, yfactor : Token) -> OptionTuple :
        scale_x = float(xfactor.value)
        scale_y = float(yfactor.value)

        if scale_x <= 0 or scale_y <= 0 :
            raise MuParseError(f"transform scale factors must be greater than zero : ({scale_x}, {scale_y})")
        return OptionTuple('transform', ('scale', scale_x, scale_y))




    @v_args(inline=True)
    def text_stmt(self, name_token : Token, zorder_token : Token, *children) -> OptionTuple:
        settings = self._util_consolidate('text', children, extras={'type':'text'})

        if name_token is None : 
            name = _random_name()
        else :
            name = name_token.value
            if name.startswith('"') :
                name = name[1:-1]

            if name.startswith('__') :
                MuParseError(f"element name cannot start with __ `{name}`")
        
        settings.value['name'] = name
        self.last_element_name = name

        if zorder_token is not None :
            settings.value['zorder'] = int(zorder_token.value)
        logger.debug(f"--- text_stmt raw text string = {settings.value['text']}")
        return settings

    @v_args(inline=True)
    def include_stmt(self, path : str) :
        logger.debug(f"=== include_stmt given path: '{path}'")
        if path.startswith('"') :
            path = path[1:-1]

        full_path = resolve_path(path, self.context)
        logger.debug(f"=== include_stmt resolved path: '{full_path}'")
        if not full_path.is_file() :
            raise MuParseError(f"include file '{full_path}' does not exist")

        xform = Configuration(full_path)
        cfg = xform._get_settings()

        return OptionTuple('include', cfg)

    def parm_list(self, children : list[Token]) -> list :
        parms = [ c.value for c in children]
        pset = set(parms)
        if len(pset) != len(parms) :
            raise MuParseError(f"Duplicate parameters defined for template : {parms}")

        if 'P' in pset or 'R' in pset :
            raise MuParseError(f"parameters `P` and `R` are reserved and cannot be in the parameter list")

        return parms

    @v_args(inline=True)
    def template_stmt(self, nameT : Token, parms : list, tbody : Token) :
        name = nameT.value
        if name in self.template :
            raise MuParseError(f"Duplicate template name `{name}`")
        body =  tbody.value.strip()[3:][:-3].strip()

        self.template[name] = (parms, body)

        logger.debug(f"""New Template :
    parameters = {parms}
    body = ```{body}```""")

    #
    # RENDER
    #

    def render_list(self, children : list[Token]) -> list[str] :
        parms = [ c.value for c in children]
        return parms

    @v_args(inline=True)
    def render_stmt(self, tname : Token, parms : list[str]) :
        name = tname.value
        if name not in self.template :
            raise MuParseError(f"No template named `{name}` exists in render statment")

        formals, body = self.template[name]
        if len(parms) != len(formals) :
            raise MuParseError(f"Incorrect number of arguments given for `{name}` - expecting {len(formals)} received {len(parms)}")

        data : dict = {}

        data = {i[0] : i[1] for i in zip(formals, parms)}
        data['P'] = self.last_element_name
        data['R'] = _random_name('r__')

        new_body = re.sub(r'\$([a-zA-Z])',
                          lambda match : data[match.groups()[0]],
                          body)
        logger.debug(f"Render output = ```{new_body}```") 

        parser = get_parser('config')

        tree = parser.parse(new_body)
        new_conf = Configuration(self.context, None)
        new_conf.last_element_name = self.last_element_name
        settings = new_conf.transform(tree)

        ele = settings['elements']
        if not len(ele) :
            logger.warning(f"No elements generated from template `{name}` render")

        self.last_element_name = ele[-1].get('name')

        optlist = list(reversed([OptionTuple(e['type'], e) for e in ele]))

        return optlist

