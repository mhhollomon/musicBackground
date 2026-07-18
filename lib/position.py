
from dataclasses import dataclass
import re
from typing import Tuple

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

#---------------------------------------------------------

@ dataclass
class rectangle :
    start : geometry
    extent: geometry

    def to_tuple(self) -> tuple :
        return (self.start.to_tuple(), self.extent.to_tuple())
    
    def copy(self) -> 'rectangle' :
        return rectangle(geometry(self.start.width, self.start.height), 
                         geometry(self.extent.width, self.extent.height)) 

#---------------------------------------------------------

POS_MAP = {
    'bottom' : 'max',
    'center' : 'mid',
    'top' : 'min',
    'right' : 'max',
    'left' : 'min'
}

POS_PATTERN = re.compile(r'(\w+) \( (\w+) \s*,\s* (\w+) (?: \s*,\s* (\w+))? \)', re.RegexFlag.X)
class position :
    def __init__(self, pos_str : str ) -> None :
        self.pos_str = pos_str
        self._valid = False
        self._width = ''
        self._height = ''
        self._ref = ''
        self._side = ''

        if self.pos_str is None :
            return 
        
        self.pos_str = self.pos_str.strip().lower()

        if self.pos_str == '' :
            return

        if '-' in self.pos_str :
            self._parse_simple()
        elif '(' in self.pos_str :
            self._parse_function()
        else :
            raise ValueError(f"Invalid position string: {pos_str}")

    def _parse_simple(self) :
            w, h = self.pos_str.split('-')
            w = w.strip()
            h = h.strip()
            if w not in ('left', 'center', 'right') :
                raise ValueError(f"Invalid width in position string: {self.pos_str}")
            
            if h not in ('top', 'center', 'bottom') :
                raise ValueError(f"Invalid height in position string: {self.pos_str}")
        
            self._width = POS_MAP[w]
            self._height = POS_MAP[h]
            self._ref = 'output'
            self._valid = True

    def _parse_function(self) :
        m = POS_PATTERN.fullmatch(self.pos_str)
        if not m :
            raise ValueError(f"Invalid function position string: {self.pos_str}")

        ref, width, height, side = m.groups()

        if ref not in ('output', 'cover', 'border') :
            raise ValueError(f"Invalid reference in position string: {self.pos_str}")

        if width not in ('min', 'mid', 'max') :
            raise ValueError(f"Invalid width in position string: {self.pos_str}")

        if height not in ('min', 'mid', 'max') :
            raise ValueError(f"Invalid height in position string: {self.pos_str}")
        
        if ref == 'border' :
            if side not in ('left', 'right', 'top', 'bottom') :
                raise ValueError(f"Invalid side in position string: {self.pos_str}")
        elif side is not None :
                raise ValueError(f"Cannot give side unless reference is border in position string: {self.pos_str}")

        self._width = width
        self._height = height
        self._ref = ref
        self._valid = True
        self._side = side or ''

    def valid(self) -> bool:
        return self._valid
    
    @property
    def w(self) -> str :
        return self._width

    @property
    def h(self) -> str :
        return self._height
    

    def offsets(self, output_rect : rectangle, cover_rect : rectangle, border_rect : rectangle, elem_size : geometry, gutter : int) -> Tuple[int, int] :
        if not self.valid():
            raise ValueError("Position is not valid")
        
        if self._ref == 'output' :
            ref_rect = output_rect
        elif self._ref == 'cover' :
            ref_rect = cover_rect
        elif self._ref == 'border' :
            ref_rect = border_rect.copy()
            if self._side == 'left' :
                ref_rect.extent.width = cover_rect.start.width - ref_rect.start.width
            elif self._side == 'right' :
                ref_rect.start.width = cover_rect.start.width + cover_rect.extent.width
                ref_rect.extent.width = (ref_rect.extent.width - cover_rect.extent.width) // 2
            elif self._side == 'top' :
                ref_rect.extent.height = cover_rect.start.height - ref_rect.start.height
            elif self._side == 'bottom' :
                ref_rect.start.height = cover_rect.start.height + cover_rect.extent.height
                ref_rect.extent.height = (ref_rect.extent.height - cover_rect.extent.height) // 2
        
        # Calculate the offset
        if self.w == 'min':
            width_offset = gutter
        elif self.w == 'mid':
            width_offset = (ref_rect.extent.width - elem_size.width) // 2
        elif self.w == 'max':
            width_offset = ref_rect.extent.width - elem_size.width - gutter

        if self.h == 'min':
            height_offset = gutter
        elif self.h == 'mid':
            height_offset = (ref_rect.extent.height - elem_size.height) // 2
        elif self.h == 'max':
            height_offset = ref_rect.extent.height - elem_size.height - gutter

        # Match the references position
        width_offset += ref_rect.start.width
        height_offset += ref_rect.start.height

        print(f"++ position = {self.pos_str}, elem_size = {elem_size}, gutter = {gutter}, Offset: {width_offset}, {height_offset}")
        return (width_offset, height_offset)

