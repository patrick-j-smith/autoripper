import sys
import json
from pathlib import Path
import logging
import subprocess
from dataclasses import dataclass

logging.basicConfig(
    filename="jellyfin_processing.log",
    filemode="w",
    format='%(asctime)s - %(levelname)s:%(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

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

def _check_path(p: str | Path) -> Path:
    return Path(p) if isinstance(p, str) else p

def _process_handbrake(args: list[str]) -> tuple[str, str]:
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        universal_newlines=True,
    )
    for line in proc.stderr:
        print(line.strip())

    return proc.communicate()

def process_show(data: Show, output_folder: Path | str) -> None:

    show_folder = _check_path(output_folder) / f'{data.name} ({data.year})'
    show_folder.mkdir(parents=True, exist_ok=True)

    for season in data.seasons:
        season_folder = show_folder / f'{season.name}'

        if season_folder.is_file():
            logger.info(f'Season folder already exists: {season_folder}')
            for path in season.paths:
                path = _check_path(path)
                path.unlink(missing_ok=True)

            continue

        season_folder.mkdir(parents=True, exist_ok=True)
        for k, v in season.episodes.items():
            output_file_name = season_folder / f'{data.name} {k}.mp4'
            base_file_paths = [_check_path(path) / v for path in season.paths]
            for base_file in base_file_paths:
                if base_file.is_file():
                    cmd = [
                        "HandBrakeCLI",
                        "--preset-import-gui",
                        "-i", str(base_file),
                        "-o", str(output_file_name),
                        "-Z", "H.256 - Pat Standard"
                    ]
                    logger.info(f'Handbrake CMD: {cmd}')
                    stdout, stderr = _process_handbrake(cmd)
                    break

    return None

def process_movie(data: Movie, output_folder: Path | str) -> None:

    movie_folder = _check_path(output_folder) / f'{data.name} ({data.year})'
    movie_folder.mkdir(parents=True, exist_ok=True)

    base_file = _check_path(data.path) / data.filename
    output_file_name = movie_folder / f'{data.name} ({data.year}).mp4'

    if output_file_name.is_file():
        logger.info(f'File already exists: {output_file_name}')
        base_file.unlink(missing_ok=True)
        return None

    if base_file.is_file():
        cmd = [
            "HandBrakeCLI",
            "--preset-import-gui",
            "-i", str(base_file),
            "-o", str(output_file_name),
            "-Z", "H.256 - Pat Standard"
        ]
        logger.info(f'Handbrake CMD: {cmd}')
        stdout, stderr = _process_handbrake(cmd)
    else:
        logger.info(f'Requested file to process does not exist: {base_file}')

    base_file.unlink(missing_ok=True)
    return None

def main() -> int:
    target_dir = Path("/home/patrick-smith/Desktop/media")
    shows_dir = target_dir / "shows"
    movies_dir = target_dir / "movies"

    data_dir = Path('..') / 'data'

    for file in data_dir.rglob("*"):
        if file.is_file():
            logger.info(f'Started processing data files: {file}')
            data = parse_json(file)
            # process file & write too /home/patrick-smith/Desktop/media
            # delete old files
            if isinstance(data, Show):
                process_show(data, shows_dir)
            else:
                process_movie(data, movies_dir)
            logger.info(f'Completed processing data files: {file}')

            # HandBrakeCLI --preset-import-gui -Z "Your Preset Name" -i input.mp4 -o output.mp4
    return 0



if __name__ == "__main__":
    sys.exit(main())