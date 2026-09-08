from copy import deepcopy

from math import pi, tan
from typing import TYPE_CHECKING, Any

from ..utils import clamped_mask, resize_contain

if TYPE_CHECKING:
    from ..music_image import MusicImage

from .element import ImageElement
from .border_helper import BorderHelper
from ..settings import ImageSettings
from ..geometry import point, sizet, rect

from PIL import Image, ImageChops, ImageTransform

import logging
logger = logging.getLogger(__name__)


class GraphicElement(ImageElement):
    DBGCATEGORY = 'Image'
    LOGGER = logger

    def __init__(self, name : str, graphic_settings : ImageSettings, parent : 'MusicImage') :
        super().__init__(name, parent)

        self.settings = deepcopy(graphic_settings)
        self.bh : BorderHelper | None = None
        self.img_bg_color = 'black'

    #-----------------------------------------------------
    # LAYOUT
    #-----------------------------------------------------
    def layout(self) :
        """Compute all the bboxen"""


        cfg = self.settings
        self._debug("LAYOUT start")

        # When using antialising with mask, we need to make sure
        # we are blending with a color as close as possible to the
        # expected background color.
        # If this element declares a color, use that
        # If not, use the color of the output element (this defaults to black).
        #
        # This isn't perfect, but it is the best we can do until the split between
        # layout and image generation happens.
        #
        if cfg.color :
            self.img_bg_color = cfg.color
        else :
            self.img_bg_color = self.parent.get_elem('output').settings.color # type: ignore


        if isinstance(cfg.size, tuple):
            # cfg.size is one of the relative size settings.
            cfg.size = self._calc_size(cfg.size)
            self._debug(f"Calculated size = {cfg.size}")

        offsets =  self.offsets_for_position(
            pos=cfg.position,
            elem_size=cfg.size
            )

        content_rec = rect(offsets, cfg.size)
        # --- FULL
        self.set_bbox('full', content_rec)

        if cfg.margin > 0 :
            # 'full' and 'margin' bbox are the same.
            # This is set inside the `if` because margin should not exist
            # if there is no margin.
            # --- MARGIN
            self.set_bbox('margin', content_rec)

            # Remove the margin from the content rect
            new_origin = content_rec.origin + cfg.margin
            new_extent = content_rec.extent - (cfg.margin * 2)
            content_rec = rect(new_origin, new_extent)

        self._debug(f"content_rec after margin = {content_rec}")

        # --- PASTE
        self.set_bbox('paste', content_rec)

        if cfg.has_border() :
            assert cfg.border is not None
            self.bh = BorderHelper(cfg.border, cfg.name, color=self.img_bg_color)
            self.bh.layout(content_rec)
            if self.bh.get_content_rect() is not None:

                # --- BORDER
                self.set_bbox('border', content_rec)
            
            # Get the new size for the content that excludes the border
            content_rec = self.bh.get_content_rect()

            # --- CONTENT
            self.set_bbox('content', content_rec)

        else :
            self._debug(f"No border spec")
            # --- CONTENT
            self.set_bbox('content', content_rec)

        self._debug(f"content_rec after border = {content_rec}")

        self.layout_done = True
        self._debug("LAYOUT end")


    #-----------------------------------------------------
    def _compute_mask(self, img : Image.Image, mask : str, luminance_img : Image.Image | None = None) -> Image.Image | None :
        
        if luminance_img is None:
            luminance_img = img.convert('L')

        if mask == 'self':
            # use the luminance of the image as-is
            gray_img = luminance_img

        elif mask == 'black':
            # clamp the luminance to black and white
            gray_img = clamped_mask(luminance_img)

        elif mask == 'none' :
            # no mask - but weirdness happens so an opaque mask
            gray_img = Image.new("L", luminance_img.size, color=255 )

        elif mask == 'alpha' :
            # use the alpha channel
            gray_img = img.getchannel('A')

        else : # auto
            # use alpha if it is there otherwise use black
            if 'A' in img.mode or 'a' in img.mode:
                self._debug(f"computing mask : using A channel of image")
                gray_img = img.getchannel('A')
            else:
                gray_img = self._compute_mask(img, 'black', luminance_img)

        if gray_img and self.settings.has_border() and \
                self.bh and not self.bh.is_piecewise() :
            old_gray_size = gray_img.size
            border_mask = self.bh.generate(True).getchannel('A')
            self._dbgsave(border_mask, "border-mask")
            mask_img = Image.new("L", border_mask.size, color=0 )
            offset = (sizet(border_mask.size) - gray_img.size) // 2
            mask_img.paste(gray_img, offset.to_tuple())
            gray_img = ImageChops.darker(border_mask, mask_img)
            end = offset + old_gray_size
            gray_img = gray_img.crop((*offset, *end ))

        return gray_img
            
    #-----------------------------------------------------
    def _build_image(self, needed_size : sizet) -> Image.Image :

        cfg = self.settings.content
        assert cfg is not None

        if cfg.has_color() :
            self._debug("Using color as content")
            assert cfg.color is not None
            img = Image.new("RGBA", needed_size.to_tuple(), self._add_alpha(cfg.color, 255))
            return img

        file_path  = cfg.file
        assert file_path is not None

        self._debug(f"Using file `{file_path}` as content")
        with Image.open(file_path) as img_img:

            fit = cfg.fit
            img_size = sizet(img_img.size)

            if fit[0] == 'stretch' :
                # forget aspect ratio. Just make the image fill the rectangle
                new_size = needed_size
                img_img = img_img.resize(new_size.to_tuple())

            elif fit[0] == 'contain' :
                img_img = resize_contain(img_img, needed_size, fit[1], cfg.color)

            elif fit[0] == 'fill' :
                # Make sure the image completely fills the container
                # while preserving A.R.
                # This means the image will need to be cropped.
                width_factor = needed_size.width / img_size.width
                height_factor = needed_size.height / img_size.height
                new_size = img_size * max(width_factor, height_factor)
                img_img = img_img.resize(new_size.to_tuple())

                crop_factor = 0.0 if fit[1] == 'min' else 0.5 if fit[1] == 'mid' else 1.0
                if new_size != needed_size :
                    self._debug(f"need to crop ({new_size} down to {needed_size})")

                    # The image will be bigger than the container.
                    if new_size.width > needed_size.width :
                        crop_width = new_size.width - needed_size.width
                        self._debug(f"too wide by {crop_width}")
                        crop_offset = crop_width * crop_factor
                        crop = (
                            crop_offset,
                            0,
                            needed_size.width + crop_offset,
                            needed_size.height,
                        )
                    else :
                        crop_height = new_size.height - needed_size.height
                        self._debug(f"too tall by  {crop_height}")
                        crop_offset = crop_height * crop_factor
                        crop = (
                            0,
                            crop_offset,
                            needed_size.width,
                            needed_size.height + crop_offset,
                        )

                    img_img = img_img.crop(crop)
            else :
                raise ValueError(f"unknown fit algorithm `{fit[0]}` for {self.name}")

            self._debug(f"_build_image final size = {img_img.size}")

            return img_img

    #-----------------------------------------------------
    def _calc_size(self, size : tuple[str, Any]) -> sizet :
        if size[0] == 'maxsquare' :
            pos = self.settings.position
            ref_elem = self.parent.get_elem(pos.target.element)
            ref_bbox = ref_elem.get_bbox(sub=pos.target.sub, piece=pos.target.piece)

            bbox_min = min(ref_bbox.extent.width, ref_bbox.extent.height)

            return sizet(bbox_min, bbox_min)
        elif size[0] == "scale" :
            pos = self.settings.position
            ref_elem = self.parent.get_elem(pos.target.element)
            ref_bbox = ref_elem.get_bbox(sub=pos.target.sub, piece=pos.target.piece)

            factor  = size[1]
            assert isinstance(factor, float)

            return ref_bbox.extent * factor
        elif size[0] == "max" :
            pos = self.settings.position
            ref_elem = self.parent.get_elem(pos.target.element)
            ref_bbox = ref_elem.get_bbox(sub=pos.target.sub, piece=pos.target.piece)

            return ref_bbox.extent

        raise ValueError(f"Invalid size {size}")


    #-----------------------------------------------------
    def _build(self, output_img : Image.Image, offsets : point | None = None) -> Image.Image :
        """Offsets are treated as negative offsets (they are subtracted)"""

        cfg = self.settings

        full_bbox = self.get_bbox('full')
        content_bbox = self.get_bbox('content')

        if offsets is None :
            offsets = point(0, 0)

        full_origin = full_bbox.origin - offsets
        content_origin = content_bbox.origin - offsets

        ## Background color
        if cfg.color :
            # No mask since this is supposed to be a solid background color.
            bg = Image.new("RGB", full_bbox.extent.to_tuple(), 
                           color=cfg.color)
            self._debug(f"pasting color bg at {full_origin.to_tuple()}")
            output_img.paste(bg, full_origin.to_tuple())

        ## Image file
        if cfg.content:   
            img_img = self._build_image(content_bbox.extent)
            mask_img = self._compute_mask(img_img, cfg.content.mask)
            self._debug(f"pasting image at {content_origin.to_tuple()}")
            output_img.paste(img_img, content_origin.to_tuple(), mask=mask_img)

        ## Border
        if cfg.has_border() :
            assert cfg.border is not None
            assert self.bh is not None
            border_img = self.bh.generate()
            border_bbox = self.bh.get_border_rect()
            border_origin = border_bbox.origin - offsets
            if border_img is not None:
                self._debug(f"pasting border at {border_origin.to_tuple()}")
                output_img.paste(border_img, border_origin.to_tuple(), mask=border_img )
            
        return output_img

    #-----------------------------------------------------

    def _trim_image(self, image : Image.Image) -> Image.Image :

        bbox_tuple = image.getbbox()
        return image.crop(bbox_tuple)
    
    #-----------------------------------------------------
    # RENDER
    #-----------------------------------------------------
    def render(self, output_img : Image.Image) -> Image.Image :

        logger.info(f"Adding image {self.name}")

        cfg = self.settings
        self._debug(f"START Render")

        if not self.layout_done :
            raise RuntimeError(f"Layout not called before render on {self.name}")

        full_bbox = self.get_bbox('full')

        if cfg.rotation == 0 and cfg.transform is None:
            output_img = self._build(output_img)
            self._debug(f"END Render (no rot or xfrm)")
            return output_img

        # build the image in a new canvas so we can
        # manipulate below
        ele_img = Image.new("RGBA", full_bbox.extent.to_tuple())
        ele_img = self._build(ele_img, full_bbox.origin)

        # both transform and rotation can change the needed origin to
        # keep the image centered.
        new_origin = full_bbox.origin
        new_extent = full_bbox.extent

        if cfg.transform is not None :
            xform = cfg.transform[0]
            if xform == 'scale' :
                xscale, yscale = cfg.transform[1:]
                old_extent = new_extent
                new_extent = new_extent.scale(xscale, yscale)
                # This is a simple resize.
                ele_img = ele_img.resize(new_extent.to_tuple())
                new_origin = new_origin - ((new_extent - old_extent) // 2)
                self._debug(f"Transform  scale - new origin = {new_origin}")

            elif xform == 'shear' :
                old_extent = new_extent
                self._dbgsave(ele_img, "before-shear")
                x_factor = -tan(cfg.transform[1] * pi / 180.0)
                y_factor = -tan(cfg.transform[2] * pi / 180.0)
                ele_img = ele_img.transform((old_extent * 4).to_tuple(),
                    # -old_extent.width slides the whole thing over to the right
                    # on the x-axis and down on the y-axis.
                    # This is need so the transform doesn't fall off the edge of new image
                    # and get clipped.
                    ImageTransform.AffineTransform([1, x_factor, -old_extent.width, y_factor, 1, -old_extent.height]),
                    resample = Image.Resampling.BICUBIC
                )
                self._dbgsave(ele_img, "after-shear")

                ele_img = self._trim_image(ele_img)
                self._dbgsave(ele_img, "after-first-trim")
                ele_img = resize_contain(ele_img, old_extent, 'mid')
                ele_img = self._trim_image(ele_img)
                new_extent = sizet(ele_img.size)
                new_origin = new_origin - ((new_extent - old_extent) // 2)
                self._debug(f"Transform  shear - new origin = {new_origin}")



            else :
                raise ValueError(f"Unkown transform `{xform}` in {self.name}")

        if cfg.rotation != 0 :
            self._dbgsave(ele_img, "before-rotate")
            ele_img = ele_img.rotate(cfg.rotation, expand=1, resample=Image.Resampling.BICUBIC)
            self._dbgsave(ele_img, "after-rotate")

            # `expand` in rotate makes the image way too big. So trim it down
            ele_img = self._trim_image(ele_img)
            self._dbgsave(ele_img, "after-trim")
            #
            # This rotates about the center. So, need to offset the origin so the middle
            # stays put.
            old_extent = new_extent
            new_extent = sizet(ele_img.size)
            new_origin = new_origin - ((new_extent - old_extent) // 2)
            self._debug(f"Rotation - new origin = {new_origin}")

        output_img.paste(ele_img, new_origin.to_tuple(), mask=ele_img)

        self._debug(f"END Render")

        return output_img
