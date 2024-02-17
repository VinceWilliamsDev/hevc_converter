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


def main(args: list[str]) -> None:
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
            archive: Path = make_destination_dir(parent, 'archive')
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


def log_event(timestamp: datetime, parent_directory: Path, target: str, event_type: str) -> None:
    log_file: Path = parent_directory.joinpath('HEVC.log')

    print(
        f'[{timestamp.date()} {timestamp.hour}:{timestamp.minute}:{timestamp.second}] {event_type} ({target})\n')

    try:
        with open(log_file, 'a') as log:
            log.write(
                f'[{timestamp.date()} {timestamp.hour}:{timestamp.minute}:{timestamp.second}] {event_type} ({target})\n')
    except IOError:
        print(f'Unable to write to {log_file}')
        exit(1)


def converter(src: Path, dest: Path, archive: Path) -> None:
    exists: bool = src.exists()
    video: bool = src.suffix in ['.mp4', '.mkv', '.avi', '.mov', '.wmv']
    if video and exists:
        new_name: str = f'{src.stem}.mp4'
        output_file: Path = dest.joinpath(new_name)
        start_time = datetime.now()

        print(f'\n[{start_time.date()} {start_time.hour}:{start_time.minute}:{start_time.second}]: STARTING ({src.name})\n')

        # make sure an HEVC copy doesn't already exist
        if output_file.exists():
            end_time = datetime.now()
            log_event(end_time, src.parent, src.name, 'DUPLICATE DETECTED')
            return

        # check if the file is already encoded in HEVC. If so, simply move it to the destination folder
        try:
            ffprobe: subprocess.CompletedProcess = subprocess.run(
                ['ffprobe', '-show_format', '-show_streams', '-loglevel', 'quiet', '-print_format', 'json', src],
                stdout=subprocess.PIPE, check=True)
            video_info = json.loads(ffprobe.stdout.decode())
            for stream in range(len(video_info['streams'])):
                if ('codec_name' in video_info['streams'][stream].keys()) and (video_info['streams'][stream]['codec_name'] == 'hevc'):
                    try:
                        move(src, dest)
                        end_time = datetime.now()
                        log_event(end_time, src.parent, src.name, 'successfully moved')
                        return
                    except FileExistsError:
                        end_time = datetime.now()
                        log_event(end_time, src.parent, src.name, 'FAILED TO MOVE')
                        return
        except subprocess.CalledProcessError as e:
            end_time = datetime.now()
            log_event(end_time, src.parent, src.name, 'FFPROBE FAILED FOR')
            print(
                f'[{end_time.date()} {end_time.hour}:{end_time.minute}:{end_time.second}] Command {e.cmd} failed with error {e.returncode}')
            return

        # if it isn't already HEVC, re-encode, then put the original copy in the 'archive' directory
        try:
            result: subprocess.CompletedProcess = subprocess.run(
                ['ffmpeg', '-i', src, '-c:v', 'hevc', '-c:a', 'copy', output_file],
                stdout=subprocess.PIPE, check=True)
            print(result.stdout.decode())
            try:
                move(src, archive)
            except FileExistsError:
                end_time = datetime.now()
                log_event(end_time, src.parent, src.name, 'FAILED TO ARCHIVE')
                return
            end_time = datetime.now()
            log_event(end_time, src.parent, src.name, 'successfully converted')
            return
        except subprocess.CalledProcessError as e:
            end_time = datetime.now()
            print(f'[{end_time.date()} {end_time.hour}:{end_time.minute}:{end_time.second}] Command {e.cmd} failed with error {e.returncode}')
            log_event(end_time, src.parent, src.name, 'CONVERSION FAILED FOR')

            if output_file.exists():
                remove(output_file)
            return

    else:
        end_time = datetime.now()
        if video and not exists:
            log_event(end_time, src.parent, src.name, 'FILE MOVED OR DELETED BEFORE CONVERSION:')
        if not src.name == 'HEVC.log':
            log_event(end_time, src.parent, src.name, 'CANNOT CONVERT')
        return


if __name__ == '__main__':
    main(argv[1:])
