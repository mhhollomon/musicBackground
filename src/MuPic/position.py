
from dataclasses import dataclass
from typing import NamedTuple

from lark import Token, Transformer, v_args, exceptions as larkexp

from .parsers import get_parser

import logging
logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
@dataclass
class PosTriple :
    element : str
    sub : str
    piece : str | None

    def to_tuple(self) :
        return (self.element, self.sub, self.piece)

    def __getitem__(self, key):
        return self.to_tuple()[key]

    def __eq__(self, other) :
        if isinstance(other, PosTriple) :
            return self.to_tuple() == other.to_tuple()
        elif isinstance(other, tuple) :
            return self.to_tuple() == other
        else :
            return False

    def to_str(self) :
        f = [x for x in self.to_tuple() if x is not None]
        if any(x in f[0] for x in ';)(:, ') :
            f[0] = f'"{f[0]}"'
        triple = '.'.join(f)
        return triple


class AnchorSpec(NamedTuple) :
    x : str
    y : str

    def to_string(self) :
        if self.y is None :
            return f"{self.x}"
        return f"{self.x}, {self.y}"

class PostnValue(NamedTuple) :
    value : int
    mode : str

    def to_str(self) -> str :
        if self.mode == 'px' :
            return f"{self.value}px"
        else :
            return f"{self.value}%"

    def calc(self, base : int) -> int :
        if self.mode == 'px' :
            return self.value
        else :
            return int(base * self.value / 100)

class PostnSpec(NamedTuple) :
    x :  PostnValue
    y :  PostnValue

    def to_str(self) -> str:
        if self.y is None :
            return f"{self.x.to_str()}"
        return f"{self.x.to_str()}, {self.y.to_str()}"

    def __str__(self) :
        return self.to_str()

#---------------------------------------------------------
# POSITION
#---------------------------------------------------------

class position :
    def __init__(self, pos_str : str) :

        ret_tuple = self._parse_pos(pos_str)
        self.pos_str = pos_str

        self.ptype : str = ret_tuple[0]
        self.target = PosTriple(*ret_tuple[1])
        self.side : str = ret_tuple[2]
        self.pos = PostnSpec(*ret_tuple[3])
        self.anchor = AnchorSpec(*ret_tuple[4])
        self.offset : int = ret_tuple[5]
        self.offset_y : int = ret_tuple[6]

    def _parse_pos(self, pos_str : str) :
        parser = get_parser('position')
        try :
            tree = parser.parse(pos_str)
        except larkexp.UnexpectedInput as e :
            raise ValueError(f"Invalid position string `{pos_str}` :\n{e}") from None
        
        return positionXform().transform(tree)

    def __str__(self) -> str :
        # normalize
        triple = self.target.to_str()
        pos = self.pos.to_str()
        anchor = self.anchor.to_string()

        side = '' if self.ptype == 'overlay' else f", {self.side}"

        return f"{self.ptype}({triple}{side}, {pos}, {anchor}, {self.offset})"

#---------------------------------------------------------

class positionXform(Transformer) :

    def __default__(self, data, children, meta) :
        print(f"===== Calling default for {data}")
        return super().__default__(data, children, meta)

    @v_args(inline=True)
    def start(self, s : tuple) -> tuple:
        """The return tuple has the following values :
        0 : str - position type (overlay, attach, or relative)
        1 : PosTriple
        2 : str | None - side (piece)
        3 : PostnSpec
        4 : tuple[str, str] for AnchorSpec
        5 : int - offset
        6 : int - offset_y (may be 0) (only used by relative)

        see _fix_pos() for more details
        """
        return s

    @v_args(inline=True)
    def INTEGER(self, s : Token) -> int:
        return int(s.value)

    @v_args(inline=True)
    def PERCENT(self, s : Token) -> int:
        return int(s.value[:-1])

    @v_args(inline=True)
    def ELEMENT_NAME(self, s : Token) -> str:
        value = s.value
        if value.startswith('"') :
            value = value[1:-1]
        return value

    @v_args(inline=True)
    def SUB_ELEMENT(self, s : Token) -> str:
        return s.value.lower()

    @v_args(inline=True)
    def MINMAX(self, s : Token) -> str:
        return s.value.lower()

    @v_args(inline=True)
    def PIECE(self, s : Token) -> str:
        return s.value.lower()

    @v_args(inline=True)
    def POS_VALUE(self, s : Token) -> PostnValue:
        value = s.value.lower()

        if value.endswith('%') :
            value = int(value[:-1])
            mode = '%'
        elif value.endswith('px') :
            value = int(value[:-2])
            mode = 'px'
        else :
            value = int(value)
            mode = 'px'

        return PostnValue(value, mode)

    @v_args(inline=True)
    def side(self, s : Token) -> str:
        return s

    @v_args(inline=True)
    def triple(self, ele, sub, piece) :
        return (ele, sub, piece)

    @v_args(inline=True)
    def simple_pos(self, w, h, offset):
        w = w.lower()
        h = h.lower()

        if offset is None :
            offset = 10

        if w == 'left' :
            w = 0
            anchor_w = 'min'
        elif w == 'center' :
            w = 50
            anchor_w = 'mid'
        elif w == 'right' :
            w = 100
            anchor_w = 'max'
        else :
            raise ValueError(f"Invalid width in position string: {w}")

        if h == 'top' :
            h = 0
            anchor_h = 'min'
        elif h == 'center' :
            h = 50
            anchor_h = 'mid'
        elif h == 'bottom' :
            h = 100
            anchor_h = 'max'
        else :
            raise ValueError(f"Invalid height in position string: {h}")

        return ('overlay', 
                PosTriple('output', 'content', None), None, 
                (PostnValue(w, '%'), PostnValue(h, '%')), 
                (anchor_w, anchor_h), offset)

    def _target_to_str(self, t : tuple) :
        f = [x for x in t if x is not None]
        return '.'.join(f)

    POS_MAP = {
        'min' : 0,
        'mid' : 50,
        'max' : 100
    }
    def _fix_pos(self, style : str, sub_def : str, target : tuple, side : str | None,
                 pos : tuple, anchor : tuple | None, offset : int | None, offset_y : int = 0) -> tuple:
        logger.debug(f"{style} input -- target: {target}, side: {side}, pos: {pos}, anchor: {anchor}, offset: {offset}, offset_y: {offset_y}")

        # default for offset
        if offset is not None :
            offset = int(offset)
        else :
            offset = 0

        # Fix up pos
        pos_x = self.POS_MAP[pos[0]] if isinstance(pos[0], str) else pos[0]
        pos_y = self.POS_MAP[pos[1]] if isinstance(pos[1], str) else pos[1]

        pos = (pos_x, pos_y)

        # Fix up target
        # (border, none, piece) => (cover, border, piece)
        if target[0:2] == ('border', None) :
            target = ('cover', 'border', target[2])

        # (element, None, None) => (element, `sub_def`, None)
        elif target[1] is None :
            if target[2] is not None :
                raise ValueError(f"Invalid target: {self._target_to_str(target)}")
            
            target = (target[0], sub_def, None)

        if target[1] in ('margin', 'border') and target[2] is None :
            raise ValueError(f"Invalid target - must have piece for piecewise sub target: {self._target_to_str(target)}")

        pt = PosTriple(*target)

        # default for anchor
        if anchor is None :
            if isinstance(pos[0], PostnValue) :
                if pos[0].mode == 'px' :
                    anchor_x = 'min'
                else :
                    anchor_x = 'max' if pos[0].value > 70 else 'min' if pos[0].value < 30 else 'mid'
            else :
                anchor_y = pos[1]

            if pos[1] is not None and isinstance(pos[1], PostnValue) :
                if pos[1].mode == 'px' :
                    anchor_y = 'min'
                else :
                    anchor_y = 'max' if pos[1].value > 70 else 'min' if pos[1].value < 30 else 'mid'
            else :
                anchor_y = pos[1]

            anchor = (anchor_x, anchor_y)


        return (style, pt, side, pos, anchor, offset, offset_y)


    @v_args(inline=True)
    def attach_pos(self, target : tuple, side : str, pos : PostnValue, 
                   anchor : tuple | str | None, offset : int | None) -> tuple :

        if isinstance(anchor, str) :
            anchor = (anchor, None)

        pos_spec = PostnSpec(pos, None)  # type: ignore

        return self._fix_pos('attach', 'full', target, side, pos_spec, anchor, offset)

    @v_args(inline=True)
    def overlay_pos(self, target : tuple, pos : tuple, 
                    anchor : tuple | None, offset : int | None) -> tuple :

        return self._fix_pos('overlay', 'content', target, None, pos, anchor, offset)

    @v_args(inline=True)
    def output_pos(self, pos : tuple, 
                    anchor : tuple | None, offset : int | None) -> tuple :

        return self._fix_pos('overlay', 'content', ('output', 'content', None), None, pos, anchor, offset)

    @v_args(inline=True)
    def relative_pos(self, target : tuple, pos : tuple, 
                    anchor : tuple | None, 
                    offsets : tuple | None) -> tuple :

        logger.debug(f"parser -- relative_pos -- offsets = {offsets}")

        if offsets :
            offsets = (
                int(offsets[0].value),
                int(offsets[1].value),
            )
        else :
            offsets = (0, 0)

        return self._fix_pos('relative', 'content', target, None, pos, anchor, *offsets)
        


    @v_args(inline=True)
    def one_pos_value(self, value) :
        if isinstance(value, PostnValue) :
            return value

        value = value.lower()
        value = self.POS_MAP[value]

        return PostnValue(value, '%')
        
    @v_args(inline=True)
    def pos_values(self, left, right) :
        return (left, right)

    @v_args(inline=True)
    def offset_values(self, left, right) :
        return (left, right)

    @v_args(inline=True)
    def anchor_values(self, x, y) :
        return (x, y)

    @v_args(inline=True)
    def offset(self, x) :
        return x

