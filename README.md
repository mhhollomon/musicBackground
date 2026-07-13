# Music Background generator
Generate an image to use as the background for a static image music video.
A logo, title, and cover image can be added.

This tool is agressively CLI based. There is no GUI, there will not be a GUI.

This is known to work on linux/macOS, and WSL2. Probably works in pure windows,
but haven't tried it.

# Install
```shell
# Get the code
git clone https://github.com/mhhollomon/musicBackground.git
cd musicBackground

# build a python virtual env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

# Usage
```
usage: music_background.py [-h] [--config_file CONFIG_FILE] [--output_path OUTPUT_PATH] [--output_size OUTPUT_SIZE]
                           [--output_color OUTPUT_COLOR] [--cover_path COVER_PATH] [--cover_align {min,mid,max}]
                           [--cover_crop {min,mid,max}] [--cover_fit {square,cover}] [--logo LOGO]
                           [--logo_size LOGO_SIZE] [--logo_mask {self,black}] [--title TITLE]
                           [--title_size TITLE_SIZE] [--title_font TITLE_FONT] [--gutter GUTTER]

options:
  -h, --help            show this help message and exit
  --config_file, -c CONFIG_FILE
                        yaml file containing configuration values. Most can then be overridden on the command
                        line.
  --output_path OUTPUT_PATH
                        The path and filename on to which to write the output. The extension given on the filename
                        will be used to determine the format.
  --output_size OUTPUT_SIZE
                        The size of the output image. Must be in the format 'WIDTHxHEIGHT'.
  --output_color OUTPUT_COLOR
                        The background color of the output image. Must be in the format '#RRGGBB'.
  --cover_path COVER_PATH
                        The path to the cover image.
  --cover_align {min,mid,max}
                        The alignment of the cover image. Default is 'min'
  --cover_crop {min,mid,max}
                        The crop of the cover image. Default is 'min'
  --cover_fit {square,cover}
                        The fit of the cover image. Default is 'square'
  --logo LOGO           The path to the logo image. If not specified, no logo will be added.
  --logo_size LOGO_SIZE
                        The size of the logo image. If not specified, the logo will be scaled to 200 pixels.
  --logo_mask {self,black}
                        The mask algorithm to use for the logo image. Default is 'black'.
  --title TITLE         The text to display in the title. If not specified, no title will be added.
  --title_size TITLE_SIZE
                        The size of the title text. If not specified, the title will be scaled to 200 pixels.
  --title_font TITLE_FONT
                        The font to use for the title text. If not specified, the default font will be used.
  --gutter GUTTER       The size of the gutter between the cover image and the title. If not specified, the gutter
                        will be 10 pixels.
  ```

# Configuration file

See [example configuration file](./example_config.yml)