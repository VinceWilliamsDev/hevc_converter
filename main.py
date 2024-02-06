# convert video files to the H.265 codec

from os import remove
from sys import argv
from pathlib import Path
import subprocess
from time import localtime, strftime
from typing import Tuple, List
import json
from shutil import move


def main(args: list[str]) -> None:
    if len(args) == 0:
        pwd: Path = Path.cwd()
        files, dest = selector(pwd)
        for file in files:
            converter(file, dest)
        print('File conversions are complete\n')
    elif len(args) == 1:
        arg: Path = Path(args[0])
        if not arg.exists():
            raise Exception("File or directory not found")
        if arg.is_file():
            dest: Path = make_destination_dir(arg.parent)
            converter(arg, dest)
        elif arg.is_dir():
            files, dest = selector(arg)
            for file in files:
                converter(file, dest)
            print('File conversions are complete\n')
        else:
            exit(0)
    elif len(args) > 1:
        raise Exception('Please input only one(1) file or directory')
    else:
        exit(0)


def selector(target: Path) -> tuple[list[Path], Path]:
    selection: str = input(f'Would you like to convert all files in {target}? y/N ')
    if selection.lower() == ("y" or "yes"):
        dest: Path = make_destination_dir(target)
        files: list[Path] = [f for f in target.iterdir() if f.is_file()]
        return files, dest
    else:
        exit(0)


def make_destination_dir(directory: Path) -> Path:
    destination: Path = directory.joinpath('hevc')
    if not destination.exists():
        try:
            destination.mkdir()
        except FileNotFoundError:
            print('Unable to create destination directory')
            exit(1)
        except FileExistsError:
            return destination
    return destination


def converter(src: Path, dest: Path) -> None:
    log_file: Path = src.parent.joinpath('HEVC.log')
    if src.suffix in ['.mp4', '.mkv', '.avi', '.mov', '.wmv']:
        input_file: str = src.name
        new_name: str = f'{src.stem}.mp4'
        output_file: Path = dest.joinpath(new_name)
        error: bool = False
        start_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())

        print(f'\n{start_time}: STARTING {input_file}\n')

        # check if the file is already encoded in HEVC. If so, simply move it to the destination folder
        try:
            ffprobe: subprocess.CompletedProcess = subprocess.run(
                ['ffprobe', '-show_format', '-show_streams', '-loglevel', 'quiet', '-print_format', 'json', input_file],
                stdout=subprocess.PIPE, check=True)
            video_info = json.loads(ffprobe.stdout.decode())
            for stream in range(5):
                if video_info['streams'][stream]['codec_name'] == 'hevc':
                    try:
                        move(input_file, dest)
                        end_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())
                        with open(log_file, 'a') as log:
                            log.write(f'[{end_time}] successfully moved ({input_file})\n')
                        print(f'{end_time}: FINISHED {input_file}\n')
                        return
                    except FileExistsError:
                        end_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())
                        with open(log_file, 'a') as log:
                            log.write(f'[{end_time}] FAILED TO MOVE ({src.name})\n')
                        print(f'\n{end_time}: {src.name} cannot be moved\n')
                        exit(1)
        except subprocess.CalledProcessError as e:
            end_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())
            print(f'{end_time}: Command {e.cmd} failed with error {e.returncode}\nOutput: {e.output}')

        # if it isn't already HEVC, re-encode
        try:
            result: subprocess.CompletedProcess = subprocess.run(
                ['ffmpeg', '-i', input_file, '-metadata', 'title=', '-c:v', 'hevc', '-c:a', 'copy', output_file],
                stdout=subprocess.PIPE, check=True)
            print(result.stdout.decode())
        except subprocess.CalledProcessError as e:
            error = True
            end_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())
            print(f'{end_time}: Command {e.cmd} failed with error {e.returncode}')
            with open(log_file, 'a') as log:
                log.write(f'[{end_time}] CONVERSION FAILED FOR ({input_file})\n')
            if output_file.exists():
                remove(output_file)
        if not error:
            end_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())
            with open(log_file, 'a') as log:
                log.write(f'[{end_time}] successfully converted ({input_file})\n')
            print(f'{end_time}: FINISHED {input_file}\n')
    else:
        end_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())
        with open(log_file, 'a') as log:
            log.write(f'[{end_time}] CANNOT CONVERT ({src.name})\n')
        print(f'\n{end_time}: {src.name} cannot be converted\n')


if __name__ == '__main__':
    main(argv[1:])
