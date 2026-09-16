import sys
import json
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Program:
    name: str
    year: int
    path: str | Path

@dataclass
class Season:
    name: str
    paths: list[str | Path]
    episodes: dict[str, Path | str]

@dataclass
class Show(Program):
    def __init__(self, name: str, year: int, **kwargs):
        self.name = name
        self.year = year
        self.seasons = []
        for key in kwargs.keys():
            self.seasons.append(Season(key, **kwargs[key]))


@dataclass
class Movie(Program):
    filename: str | Path

def parse_json(filename: str | Path) -> Show | Movie:

    try:
        with open(filename, 'r') as f:
            values = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not available at requested location: {filename}.")
    except json.JSONDecodeError:
        raise json.JSONDecodeError

    try:
        content_type = values.pop("type")
    except KeyError:
        raise TypeError(f"Unsupported type: {values}.")

    if content_type == 'show':
        d = Show(**values)
    elif content_type == 'movie':
        d = Movie(**values)
    else:
        raise TypeError(f"Unsupported type: {content_type}.")

    return d

def main() -> int:
    target_dir = Path("/home/patrick-smith/Desktop/media")
    shows_dir = target_dir / "shows"
    movies_dir = target_dir / "movies"

    data_dir = Path('..') / 'data'

    for file in data_dir.rglob("*"):
        if file.is_file():
            data = parse_json(file)
            # process file & write too /home/patrick-smith/Desktop/media
            # delete old files
            if isinstance(data, Show):
                print('show')
            else:
                print('movie')
            print('hi')

            # HandBrakeCLI --preset-import-gui -Z "Your Preset Name" -i input.mp4 -o output.mp4
    return 0



if __name__ == "__main__":
    sys.exit(main())