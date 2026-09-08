from PIL import Image

import logging
import os
from pathlib import Path

from .geometry import sizet

def dictmerge(a: dict, b: dict) -> dict:
    """Merge b into a.
    'a' is modified in-place.
    Dicts are merged. Lists are concatenated.
    Found on stackoverflow with slight mods.
    """
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                dictmerge(a[key], b[key])
            elif isinstance(a[key], list) and isinstance(b[key], list):
                a[key].extend(b[key])
            else :
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a

#----------------------------------------------------------------------------

def clamped_mask(input : Image.Image, threshold : int = 10) -> Image.Image :

    upper_threshold = 255 - threshold
    slope = 255 / (upper_threshold - threshold)

    def new_value(x : float) -> float :
        if x < threshold :
            return 0
        elif x > upper_threshold :
            return 255
        else :
            return (x - threshold) * slope

    return input.convert('L').point(new_value)

#----------------------------------------------------------------------------
def resize_contain(img : Image.Image, needed_size : sizet, align : str, color : str | None = None) -> Image.Image :
    img_size = sizet(img.size)

    # Make the image as large as possible while making sure it fits
    # entirely into container and maintains Aspect Ratio.
    width_factor = needed_size.width / img_size.width
    height_factor = needed_size.height / img_size.height
    new_size = img_size * min(width_factor, height_factor)
    img = img.resize(new_size.to_tuple())

    if new_size != needed_size :
        # it will be smaller
        buffer = Image.new("RGBA", size=needed_size.to_tuple(), color=color)
        if align == 'min' :
            paste_pt = sizet(0, 0)
        elif align == 'mid' :
            paste_pt = (needed_size - new_size) // 2
        else : # max
            paste_pt = (needed_size - new_size)

        buffer.paste(img, paste_pt.to_tuple())
        img = buffer

    return img

#----------------------------------------------------------------------------

class DebugBase() :
    DBGCATEGORY = 'Unknown'

    def _dbgsave(self, img : Image.Image, suffix : str) :

        logger = getattr(self, 'LOGGER', logging.getLogger(self.DBGCATEGORY))

        if not logger.isEnabledFor(logging.DEBUG) :
            return

        dir = os.environ.get('MUPIC_DEBUG_SAVE_DIR')
        if not dir :
            return
        
        dir = Path(dir)
        if not dir.is_dir() :
            return

        name = getattr(self, 'name', 'unknown').lower()
        name = name.replace(' ', '_')
        name = name.replace('/', '_')

        fname =  dir / f"dbg-{self.DBGCATEGORY.lower()}-{name}-{suffix}.png"

        img.save(fname, format='png')

    def _debug(self, msg) :
        logger = getattr(self, 'LOGGER', logging.getLogger(self.DBGCATEGORY))
        name = getattr(self, 'name', '')
        logger.debug(f"{self.DBGCATEGORY} {name} -- {msg}")


