from dataclasses import dataclass, field
import re

import logging
from typing import Any, Tuple
logger = logging.getLogger(__name__)

#---------------------------------------------------------
class point :

    def __init__(self, x : int | float | str, y : int | float | str) :
        super().__setattr__("_done" , False)
        self.x = int(x)
        self.y = int(y)
        self._done = True

    def to_tuple(self) -> tuple[int, int] :
        return (self.x, self.y)

    def __getitem__(self, key : int) :
        return self.to_tuple()[key]

    def __len__(self) -> int :
        return 2

    def set_x(self, x : int | float | str) -> 'point':
        return point(x, self.y)

    def set_y(self, y : int | float | str) -> 'point':
        return point(self.x, y)

    @classmethod
    def from_tuple(cls, t : Tuple[int | float | str, int | float | str]) -> 'point' :
        return point(int(t[0]), int(t[1]))

    def copy(self) -> 'point' :
        return point(int(self.x), int(self.y))

    def __add__(self, other) -> 'point' :
        if isinstance(other, point) :
            return point(int(self.x + other.x), int(self.y + other.y))
        elif isinstance(other, tuple) :
            return point(int(self.x + other[0]), int(self.y + other[1]))
        elif isinstance(other, (int, float)) :
            return point(int(self.x + other), int(self.y + other))
        elif isinstance(other, sizet) :
            return point(int(self.x + other.width), int(self.y + other.height))
        else :
            raise TypeError(f"Unsupported type for addition with point: {type(other)}")

    def __sub__(self, other) -> 'point' :
        if isinstance(other, point) :
            return point(int(self.x - other.x), int(self.y - other.y))
        elif isinstance(other, tuple) :
            return point(int(self.x - other[0]), int(self.y - other[1]))
        elif isinstance(other, (int, float)) :
            return point(int(self.x - other), int(self.y - other))
        elif isinstance(other, sizet) :
            return point(int(self.x - other.width), int(self.y - other.height))
        else :
            raise TypeError(f"Unsupported type for subtraction with point: {type(other)}")

    def __mul__(self, other) -> 'point' :
        if isinstance(other, (int, float)) :
            return point(int(self.x * other), int(self.y * other))
        else :
            raise TypeError(f"Unsupported type for multiplication with point: {type(other)}")

    def __eq__(self, other) :
        return self.x == other.x and self.y == other.y

    def __repr__(self) -> str :
        return f"p<{self.x}, {self.y}>"

    def __setattr__(self, name: str, value: Any) -> None:
        if not self._done :
            super().__setattr__(name, value)
        else :
            raise TypeError("point is immutable")

#---------------------------------------------------------

GEOMETRY_PATTERN = re.compile(r'(\d+)x(\d+)')
class sizet :

    def __init__(self, width : int | float | str | Tuple[int | float, int | float], height : int | float | str | None = None) :
        super().__setattr__("_done" , False)
        if height is None :
            if isinstance(width, tuple) :
                width, height = width
            elif isinstance(width, str) :
                try :
                    width = float(width)
                except ValueError :
                    match = GEOMETRY_PATTERN.match(width)
                    if match is None :
                        raise ValueError(f"Invalid geometry string: {width}")
                    gwidth, gheight = match.groups()
                    if gheight is None :
                        gheight = gwidth
                    height = int(gheight)
                    width = int(gwidth)
                width = int(width)
        elif isinstance(width, tuple) :
            raise ValueError("Cannot pass width as a tuple if height is given")
        if height is None :
            height = width
        
        self.width = int(width)
        self.height = int(height)
        self._done = True

    def to_tuple(self) -> tuple[int, int] :
        return (self.width, self.height)

    def __getitem__(self, key) :
        return self.to_tuple()[key]

    @classmethod
    def from_string(cls, s : str | None) -> 'sizet | None' :
        """ main reason to have this function is to be able to return None.
        Otherwise, just use the string handling in the constructor
        """
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
        # "square" should be treated as landscape
        return self.width >= self.height

    def small_side(self) -> int :
        return min(self.width, self.height)
    
    def copy(self) -> 'sizet' :
        return sizet(self.width, self.height)

    def scale(self, wfactor : float, hfactor : float) -> 'sizet' :
        return sizet(self.width * wfactor, self.height * hfactor)

    def __add__(self, other) -> 'sizet' :

        if isinstance(other, sizet) :
            return sizet(self.width + other.width, self.height + other.height)
        elif isinstance(other, tuple) :
            return sizet(self.width + other[0], self.height + other[1])
        elif isinstance(other, (int, float)) :
            return sizet(int(self.width + other), int(self.height + other))
        else :
            raise TypeError(f"Unsupported type for addition with sizet: {type(other)}")

    def __sub__(self, other) -> 'sizet' :

        if isinstance(other, sizet) :
            return sizet(self.width - other.width, self.height - other.height)
        elif isinstance(other, tuple) :
            return sizet(self.width - other[0], self.height - other[1])
        elif isinstance(other, (int, float)) :
            return sizet(int(self.width - other), int(self.height - other))
        else :
            raise TypeError(f"Unsupported type for subtraction with sizet: {type(other)}")
        
    def __mul__(self, other) -> 'sizet' :
        if isinstance(other, (int, float)) :
            return sizet(int(self.width * other), int(self.height * other))
        else :
            raise TypeError(f"Unsupported type for multiplication with sizet: {type(other)}")

    def __floordiv__(self, other) -> 'sizet' :
        if isinstance(other, (int, float)) :
            return sizet(int(self.width // other), int(self.height // other))
        else :
            raise TypeError(f"Unsupported type for floordiv with sizet: {type(other)}")

    def __eq__(self, other) -> bool :
        if isinstance(other, tuple) :
            return self.width == other[0] and self.height == other[1]
        elif isinstance(other, sizet) :
            return self.width == other.width and self.height == other.height
        else :
            raise TypeError(f"Unsupported type for comparison with sizet: {type(other)}")

    def __repr__(self) -> str :
        return f"st<{self.width}, {self.height}>"

    def __setattr__(self, name: str, value: Any) -> None:
        if not self._done :
            super().__setattr__(name, value)
        else :
            raise TypeError("point is immutable")

#---------------------------------------------------------

@ dataclass
class rect :
    origin : point
    extent: sizet
    _done : bool = field(init=False, default=False, repr=False)

    def __post_init__(self) :
        self._done = True

    def __repr__(self) -> str :
        return f"rect({self.origin}, {self.extent})"

    def to_tuple(self) -> tuple :
        return (self.origin.to_tuple(), self.extent.to_tuple())
    
    def copy(self) -> 'rect' :
        return rect(point(self.origin.x, self.origin.y), 
                    sizet(self.extent.width, self.extent.height)) 

    def add_offsets(self, offsets : point | tuple) -> 'rect' :
        new_origin = self.origin + offsets
        return rect(new_origin, self.extent)

    @property
    def end(self) -> point :
        return self.origin + self.extent

    def __setattr__(self, name: str, value: Any) -> None:
        if not self._done :
            super().__setattr__(name, value)
        else :
            raise TypeError("rect is immutable")
