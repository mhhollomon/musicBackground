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

# Configuration file

See documentation in the [example configuration file](./example_config.yml)

# Usage

## Help

You can get a complete list of the options in the help message. They are also
all listed in the [example configuration file](./example_config.yml). The example
configuration file also has information on defaults.

```
./music_background --help
```

## Ways to use

Things in the configuration file can be overridden on the command line.
This lets you set up a "standard" that changes a little between tracks.

So, an album of 6 tracks could be set up like :
- define the output size, etc in the config file
- put the album cover image path in the config file
- put the logo image path in the config file

Then each track would give the title and output file.

```
./music_background -c album.yml --title 'Cool Track 1' --output_path ./track1.jpg
```

Of, course it could be done all on the command line - or have a config file per track.