#!/usr/bin/python3

# convert video files to the H.265 codec

from os import remove
from sys import argv
from pathlib import Path
import subprocess
from datetime import datetime
from typing import Tuple, List
import json
from shutil import move


def main() -> None:
    args = argv[1:]
    start_time: datetime = datetime.now()

    if len(args) == 0:
        pwd: Path = Path.cwd()
        files, dest, archive = selector(pwd)
        for file in files:
            converter(file, dest, archive)
        end_time = datetime.now()
        elapsed = time_elapsed(start_time, end_time)
        print('File conversions are complete')
        print(f'Time elapsed: {elapsed}\n')

    elif len(args) == 1:
        arg: Path = Path(args[0])
        if not arg.exists():
            raise Exception("File or directory not found")

        if arg.is_file():
            dest: Path = make_destination_dir(arg.parent, 'hevc')
            archive: Path = make_destination_dir(arg.parent, 'archive')
            converter(arg, dest, archive)
            end_time = datetime.now()
            elapsed = time_elapsed(start_time, end_time)
            print('File conversions are complete')
            print(f'Time elapsed: {elapsed}\n')

        elif arg.is_dir():
            files, dest, archive = selector(arg)
            for file in files:
                converter(file, dest, archive)
            end_time = datetime.now()
            elapsed = time_elapsed(start_time, end_time)
            print('File conversions are complete')
            print(f'Time elapsed: {elapsed}\n')

    elif len(args) > 1:
        raise Exception('Please input only one(1) file or directory')


def selector(target: Path) -> tuple[list[Path], Path, Path]:
    selection: str = input(f'Would you like to convert all files in {target}? y/N ')

    if selection.lower() == ("y" or "yes"):
        dest: Path = make_destination_dir(target, 'hevc')
        archive: Path = make_destination_dir(target, 'archive')
        files: list[Path] = [f for f in target.iterdir() if f.is_file()]
        return files, dest, archive
    else:
        exit(0)


def make_destination_dir(directory: Path, name: str) -> Path:
    destination: Path = directory.joinpath(name)

    if not destination.exists():
        try:
            destination.mkdir()
        except FileNotFoundError:
            print('Unable to create destination directory')
            exit(1)
        except FileExistsError:
            return destination
    return destination


def time_elapsed(start: datetime, end: datetime) -> str:
    diff = end - start

    secs: int = diff.seconds % 60
    mins: int = (diff.seconds // 60) % 60
    hours: int = diff.seconds // (60 * 60)

    elapsed: str = f'{mins} minutes, {secs} seconds'

    if diff.days > 0:
        elapsed = f'{diff.days} days, {hours} hours, {elapsed}'
    elif hours > 0:
        elapsed = f'{hours} hours, {elapsed}'
    return elapsed


def log_event(parent_directory: Path, target: str, event_type: str) -> None:
    log_file: Path = parent_directory.joinpath('HEVC.log')
    timestamp = now_str()

    print(
        f'[{timestamp}] {event_type} ({target})\n')

    try:
        with open(log_file, 'a') as log:
            log.write(
                f'[{timestamp}] {event_type} ({target})\n')
    except IOError:
        print(f'Unable to write to {log_file}')
        exit(1)


def now_str() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def converter(file: Path, dest: Path, archive: Path) -> None:
    exists: bool = file.exists()
    video: bool = file.suffix in ['.mp4', '.mkv', '.avi', '.mov', '.wmv']
    if video and exists:
        new_name: str = f'{file.stem}.mp4'
        output_file: Path = dest.joinpath(new_name)
        start_time = now_str()

        print(f'\n[{start_time}]: STARTING ({file.name})\n')

        # make sure an HEVC copy doesn't already exist
        if output_file.exists():
            log_event(file.parent, file.name, 'DUPLICATE DETECTED')
            return

        # check if the file is already encoded in HEVC. If so, simply move it to the destination folder
        try:
            ffprobe: subprocess.CompletedProcess = subprocess.run(
                ['ffprobe', '-show_format', '-show_streams', '-loglevel', 'quiet', '-print_format', 'json', file],
                stdout=subprocess.PIPE, check=True)
            video_info = json.loads(ffprobe.stdout.decode())
            for stream in range(len(video_info['streams'])):
                if ('codec_name' in video_info['streams'][stream].keys()) and (
                        video_info['streams'][stream]['codec_name'] == 'hevc'):
                    try:
                        move(file, dest)
                        log_event(file.parent, file.name, 'successfully moved')
                        return
                    except FileExistsError:
                        log_event(file.parent, file.name, 'FAILED TO MOVE')
                        return
        except subprocess.CalledProcessError as e:
            end_time = now_str()
            log_event(file.parent, file.name, 'FFPROBE FAILED FOR')
            print(
                f'[{end_time}] Command {e.cmd} failed with error {e.returncode}')
            return

        # if it isn't already HEVC, re-encode, then put the original copy in the 'archive' directory
        try:
            result: subprocess.CompletedProcess = subprocess.run(
                ['ffmpeg', '-i', file, '-c:v', 'hevc', '-c:a', 'copy', output_file],
                stdout=subprocess.PIPE, check=True)
            print(result.stdout.decode())
            try:
                move(file, archive)
            except FileExistsError:
                log_event(file.parent, file.name, 'FAILED TO ARCHIVE')
                return
            log_event(file.parent, file.name, 'successfully converted')
            return
        except subprocess.CalledProcessError as e:
            end_time = now_str()
            print(f'[{end_time}] Command {e.cmd} failed with error {e.returncode}')
            log_event(file.parent, file.name, 'CONVERSION FAILED FOR')

            if output_file.exists():
                remove(output_file)
            exit(1)

    else:
        if video and not exists:
            log_event(file.parent, file.name, 'FILE MOVED OR DELETED BEFORE CONVERSION:')
        if not file.name == 'HEVC.log':
            log_event(file.parent, file.name, 'CANNOT CONVERT')
        return


if __name__ == '__main__':
    main()
