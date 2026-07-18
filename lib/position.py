
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

POS_MAP = {
    'bottom' : 'max',
    'center' : 'mid',
    'top' : 'min',
    'right' : 'max',
    'left' : 'min'
}
class position :
    def __init__(self, pos_str : str) -> None :
        self.pos_str = pos_str
        self._valid = False

        if pos_str is None or pos_str.strip() == '' :
            return 

        if '-' in pos_str :
            w, h = pos_str.split('-')
            w = w.strip().lower()
            h = h.strip().lower()
            if w not in ('left', 'center', 'right') :
                raise ValueError(f"Invalid width in position string: {pos_str}")
            
            if h not in ('top', 'center', 'bottom') :
                raise ValueError(f"Invalid height in position string: {pos_str}")
        
            self._width = POS_MAP[w]
            self._height = POS_MAP[h]
            self._valid = True
            self._ref = 'output'

        else :
            raise ValueError(f"Invalid position string: {pos_str}")


    def valid(self) -> bool:
        return self._valid
    
    @property
    def w(self) -> str :
        return self._width

    @property
    def h(self) -> str :
        return self._height
    

    def offsets(self, img_size : geometry, elem_size : geometry, gutter : int) -> Tuple[int, int] :
        if not self.valid():
            raise ValueError("Position is not valid")
        
        # Calculate the offset
        if self.w == 'min':
            width_offset = gutter
        elif self.w == 'mid':
            width_offset = (img_size.width - elem_size.width) // 2
        elif self.w == 'max':
            width_offset = img_size.width - elem_size.width - gutter

        if self.h == 'min':
            height_offset = gutter
        elif self.h == 'mid':
            height_offset = (img_size.height - elem_size.height) // 2
        elif self.h == 'max':
            height_offset = img_size.height - elem_size.height - gutter

        #print(f"++ position = {self.pos_str}, elem_size = {elem_size}, gutter = {gutter}, Offset: {width_offset}, {height_offset}")
        return (width_offset, height_offset)

