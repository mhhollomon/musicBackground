from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..music_image import MusicImage

from ..geometry import sizet, rect, point
from ..position import position
from ..settings import WidthSettings

from PIL import Image, ImageColor

from ..utils import DebugBase

import logging
logger = logging.getLogger(__name__)

#---------------------------------------------------------

class ImageElement(DebugBase) :

    def __init__(self, name : str, parent : 'MusicImage', add_to_parent : bool = True) :
        self.name = name
        self.parent = parent
        self.bbox : dict[str, rect] = {}
        self.main_image : Image.Image | None = None
        self.mask_image : Image.Image | None = None
        self.generated = False
        self.layout_done = False

        if add_to_parent :
            parent._add_element(self)

    @property
    def name(self) :
        return self._name

    @name.setter
    def name(self, name : str) :
        if name is None :
            raise ValueError("ImageElement name cannot be None")
        if name == '' :
            raise ValueError("ImageElement name cannot be empty")
        self._name = name

    def get_images(self) -> tuple[Image.Image, Image.Image | None]:
        if not self.generated :
            raise RuntimeError(f"Trying to get images before the element is generated in {self.name}")
        assert self.main_image is not None
        return self.main_image, self.mask_image

    def border_widths(self) -> WidthSettings | None :
        s = getattr(self, 'settings', None)
        logger.debug(f"looking for border widths in {self.name}")
        if s is None :
            
            return None
        b = getattr(s, 'border', None)
        if b is None :
            return None
        w = getattr(b, 'width', None)
        return w
    

    def margin_widths(self) -> WidthSettings | None :
        s = getattr(self, 'settings', None)
        if s is None :
            return None
        m = getattr(s, 'margin', None)
        return None if m is None or m < 1 else WidthSettings(m, m, m, m)
    
#-----------------------------------------------------------------------------

    def set_bbox(self, sub : str, new_bbox : rect) -> None :
    
        if sub not in ('full', 'border', 'margin', 'content', 'paste') :
            raise ValueError(f"incorrect bbox subelement {sub} in {self.name}")

        logger.debug(f"setting {self.name} {sub} bbox to {new_bbox}")
        self.bbox[sub] = new_bbox

#-----------------------------------------------------------------------------
    def _add_alpha(self, color : str, alpha : int) :
        """Add an alpha value to a color reference"""

        ct = ImageColor.getrgb(color)
        return (*ct, alpha)
    
#-----------------------------------------------------------------------------
    def layout(self) :
        raise RuntimeError("Subclass needs to override `layout`")
    
#-----------------------------------------------------------------------------
    def render(self, img : Image.Image) :
        raise RuntimeError("Subclass needs to override `render`")
    
#-----------------------------------------------------------------------------

    def get_bbox(self, sub : str, piece : str | None = None) :
        """
        Returns the element's bbox. 
        """
        logger.debug(f"getting {self.name} {sub} bbox (piece={piece})")
        if not self.layout_done :
            raise ValueError(f"Element {self.name} has not been generated yet")
        if sub not in self.bbox :
            raise ValueError(f"Element {self.name} has no bbox for sub {sub}")

        cbox = self.bbox[sub]
        
        if piece is None :
            logger.debug(f"returning {self.name} {sub} bbox {cbox}")
            return cbox.copy()

        if sub == 'border' :
            widths = self.border_widths()
        elif sub == 'margin' :
            widths = self.margin_widths()
        else :
            raise ValueError(f"Invalid sub {sub}")

        if widths is None :
            raise ValueError(f"Element {self.name} has no {sub} widths")

        if piece == 'left' :
            if widths.l == 0 :
                raise ValueError(f"Left {sub} is 0 for element {self.name}")
            origin = cbox.origin.copy()
            extent = sizet(widths.l, cbox.extent.height)
        elif piece == 'right' :
            if widths.r == 0 :
                raise ValueError(f"Right {sub} is 0 for element {self.name}")
            origin = point(cbox.origin.x + cbox.extent.width - widths.r, cbox.origin.y)
            extent = sizet(widths.r, cbox.extent.height)
        elif piece == 'top' :
            if widths.t == 0 :
                raise ValueError(f"Top {sub} is 0 for element {self.name}")
            origin = cbox.origin
            extent = sizet(cbox.extent.width, widths.t)
        elif piece == 'bottom' :
            if widths.b == 0 :
                raise ValueError(f"Bottom {sub} is 0 for element {self.name}")
            origin = point(cbox.origin.x, cbox.origin.y + cbox.extent.height - widths.b)
            extent = sizet(cbox.extent.width, widths.b)
        else :
            raise ValueError(f"Invalid piece specifier {piece}")

        return rect(origin, extent)




#-----------------------------------------------------------------------------

    def _attach_offsets(self, pos : position, elem_size : sizet) -> point:
        ref_elem = self.parent.get_elem(pos.target.element)
        ref_bbox = ref_elem.get_bbox(sub=pos.target.sub, piece=pos.target.piece)

        logger.debug(f"attach : ref_bbox = {ref_bbox}")
        logger.debug(f"attach : elem_size = {elem_size}")

        # attach only has one pos factor. The constructor makes sure it is the x.
        rel_pos = pos.pos.x
        # attach only has one anchor. The constructor makes sure it is the x.
        anchor = pos.anchor.x

        anchor_fact = 0 if anchor == 'min' else 0.5 if anchor == 'mid' else 1
        min_diff = pos.offset
        logger.debug(f"attach : min_diff = {min_diff}")

        # All four legs do about the same thing.
        # 1. Use the relative position to calculate the attach point.
        #    This is a point along the line formed by the side of the ref element.
        #
        # 2. Offset that point to translate the attach point from the the anchor point
        #    to the required origin of the element.
        #
        # 3. Update that to handle the offset.
        #
        # Since the algorithm always puts the anchor point directly
        # on the attach point. The offset will always need to be added.
        # The difference will be the sign and which dimenstion.

        if pos.side == 'top' : 
            x_adjust = rel_pos.calc(ref_bbox.extent.width)
            attach_point = ref_bbox.origin + (x_adjust, 0)
            logger.debug(f"attach offsets : top attach_point = {attach_point}")

            anchor_x_adjust = -int(elem_size.width * anchor_fact)
            anchor_y_adjust = -elem_size.height
            offsets = attach_point + (anchor_x_adjust, anchor_y_adjust)
            logger.debug(f"attach offsets : top adjusted offsets = {offsets}")

            final_offsets = offsets - (0, min_diff)

        elif pos.side == 'bottom' :
            x_adjust = rel_pos.calc(ref_bbox.extent.width)
            attach_point = ref_bbox.origin + (x_adjust, ref_bbox.extent.height)
            logger.debug(f"attach offsets : bottom attach_point = {attach_point}")

            anchor_x_adjust = -int(elem_size.width * anchor_fact)
            anchor_y_adjust = 0
            offsets = attach_point + (anchor_x_adjust, anchor_y_adjust)
            logger.debug(f"attach offsets : bottom adjusted offsets = {offsets}")

            final_offsets = offsets + (0, min_diff)

        elif pos.side == 'left' :
            y_adjust = rel_pos.calc(ref_bbox.extent.height)
            attach_point = ref_bbox.origin + (0, y_adjust)
            logger.debug(f"attach offsets : left attach_point = {attach_point}")

            anchor_x_adjust = -elem_size.width
            anchor_y_adjust = -int(elem_size.height * anchor_fact )
            offsets = attach_point + (anchor_x_adjust, anchor_y_adjust)
            logger.debug(f"attach offsets : left adjusted offsets = {offsets}")

            final_offsets = offsets - (min_diff, 0)

        elif pos.side == 'right' :
            y_adjust = rel_pos.calc(ref_bbox.extent.height)
            attach_point = ref_bbox.origin + (ref_bbox.extent.width, y_adjust)
            logger.debug(f"attach offsets : right attach_point = {attach_point}")
            
            anchor_x_adjust = 0
            anchor_y_adjust = -int(elem_size.height * anchor_fact )
            offsets = attach_point + (anchor_x_adjust, anchor_y_adjust)
            logger.debug(f"attach offsets : left adjusted offsets = {offsets}")

            final_offsets = offsets + (min_diff, 0)

        else : 
            raise ValueError(f"Invalid attach side {pos.side}")

        return final_offsets

#-----------------------------------------------------------------------------

    def _overlay_offsets(self, pos : position, elem_size : sizet) -> point :
        ref_elem = self.parent.get_elem(pos.target.element)
        ref_bbox = ref_elem.get_bbox(sub=pos.target.sub, piece=pos.target.piece)

        logger.debug(f"overlay offsets - ref_bbox = {ref_bbox}")

        offset_pt = point(
            pos.pos.x.calc(ref_bbox.extent.width),
            pos.pos.y.calc(ref_bbox.extent.height)
        )

        attach_point = ref_bbox.origin + offset_pt
        logger.debug(f'overlay offsets - attach_point = {attach_point}')

        anchor = pos.anchor.x
        adjust_fact = 0 if anchor == 'min' else 0.5 if anchor == 'mid' else 1
        adjust_x = int(elem_size.width * adjust_fact)

        anchor = pos.anchor.y
        adjust_fact = 0 if anchor == 'min' else 0.5 if anchor == 'mid' else 1
        adjust_y = int(elem_size.height * adjust_fact)

        anchor_adjust = (adjust_x, adjust_y)
        logger.debug(f'overlay offsets - anchor_adjust = {anchor_adjust}')

        adjusted_pt = attach_point - anchor_adjust
        logger.debug(f'overlay offsets - adjusted_pt = {adjusted_pt}')
       
        anchor = pos.anchor.x
        if anchor == 'min' :
            tweak_x = pos.offset - (adjusted_pt.x - ref_bbox.origin.x)
            tweak_x = 0 if tweak_x < 0 else tweak_x
        elif anchor == 'max' :
            tweak_x = -(pos.offset - (ref_bbox.end.x - (adjusted_pt.x + elem_size.width)))
            tweak_x = 0 if tweak_x > 0 else tweak_x
        else :
            tweak_x = 0

        anchor = pos.anchor.y
        if anchor == 'min' :
            tweak_y = pos.offset - (adjusted_pt.y - ref_bbox.origin.y)
            tweak_y = 0 if tweak_y < 0 else tweak_y
        elif anchor == 'max' :
            tweak_y = -(pos.offset - (ref_bbox.end.y - (adjusted_pt.y + elem_size.height)))
            tweak_y = 0 if tweak_y > 0 else tweak_y
        else :
            tweak_y = 0

        offset_tweak = (tweak_x, tweak_y)
        logger.debug(f'overlay offsets - offset_tweak = {offset_tweak}')

        final_offset = adjusted_pt + offset_tweak
        logger.debug(f'overlay offsets - final_offset = {final_offset}')

        return final_offset

#-----------------------------------------------------------------------------
    def _relative_offsets(self, pos : position, elem_size : sizet) -> point :

        ref_elem = self.parent.get_elem(pos.target.element)
        ref_bbox = ref_elem.get_bbox(sub=pos.target.sub, piece=pos.target.piece)

        offset_pt = point(
            pos.pos.x.calc(ref_bbox.extent.width),
            pos.pos.y.calc(ref_bbox.extent.height)
        )

        # This is our reference point
        attach_point = ref_bbox.origin + offset_pt
        logger.debug(f'relative offsets - attach_point = {attach_point}')

        # Figure out where the anhcor point is on the client
        anchor = pos.anchor.x
        adjust_fact = 0 if anchor == 'min' else 0.5 if anchor == 'mid' else 1
        adjust_x = int(elem_size.width * adjust_fact)

        anchor = pos.anchor.y
        adjust_fact = 0 if anchor == 'min' else 0.5 if anchor == 'mid' else 1
        adjust_y = int(elem_size.height * adjust_fact)

        anchor_adjust = (adjust_x, adjust_y)
        logger.debug(f'relative offsets - anchor_adjust = {anchor_adjust}')

        # The reference point adjusted to be at the upper right of the client
        adjusted_pt = attach_point - anchor_adjust
        logger.debug(f'relative offsets - adjusted_pt = {adjusted_pt}')

        final_offset = adjusted_pt + (pos.offset, pos.offset_y)
        logger.debug(f'relative offsets - final_offset = {final_offset}')

        return final_offset


#-----------------------------------------------------------------------------

    def offsets_for_position(self, pos : position, elem_size : sizet) -> point :

        logger.debug(f"""Position Inputs :
    position = {pos}
    elem_size = {elem_size}"""
    )
        
        if pos.ptype == 'attach' :
            final_offsets = self._attach_offsets(pos, elem_size)
        elif pos.ptype == 'overlay' :
            final_offsets = self._overlay_offsets(pos, elem_size)
        elif pos.ptype == 'relative' :
            final_offsets = self._relative_offsets(pos, elem_size)

        logger.debug(f"Position Calculated final_offsets = {final_offsets}")
        return final_offsets

