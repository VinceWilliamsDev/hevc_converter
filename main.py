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
    start_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())
    end_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())
    if len(args) == 0:
        pwd: Path = Path.cwd()
        files, dest = selector(pwd)
        for file in files:
            end_time = converter(file, dest)
        elapsed = time_elapsed(start_time, end_time)
        print('File conversions are complete')
        print(f'Time elapsed: {elapsed}\n')
    elif len(args) == 1:
        arg: Path = Path(args[0])
        if not arg.exists():
            raise Exception("File or directory not found")
        if arg.is_file():
            dest: Path = make_destination_dir(arg.parent)
            end_time = converter(arg, dest)
            elapsed = time_elapsed(start_time, end_time)
            print('File conversions are complete')
            print(f'Time elapsed: {elapsed}\n')
        elif arg.is_dir():
            files, dest = selector(arg)
            for file in files:
                end_time = converter(file, dest)
            elapsed = time_elapsed(start_time, end_time)
            print('File conversions are complete')
            print(f'Time elapsed: {elapsed}\n')
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


def time_elapsed(start: str, end: str) -> str:
    start_date_time: list[str] = start.split(' ')
    start_list = start_date_time[0].split('-')
    start_list.extend(start_date_time[1].split(':'))

    end_date_time: list[str] = end.split(' ')
    end_list = end_date_time[0].split('-')
    end_list.extend(end_date_time[1].split(':'))

    delta: list[int] = []
    for idx, interval in enumerate(end_list):
        delta.append(int(interval) - int(start_list[idx]))
    elapsed = f'{delta[4]} minutes, {delta[5]} seconds'
    if delta[0] > 0:
        elapsed = f'{delta[0]} years, {delta[1]} months, {delta[2]} days, {delta[3]} hours, {elapsed}'
    elif delta[1] > 0:
        elapsed = f'{delta[1]} months, {delta[2]} days, {delta[3]} hours, {elapsed}'
    elif delta[2] > 0:
        elapsed = f'{delta[2]} days, {delta[3]} hours, {elapsed}'
    elif delta[3] > 0:
        elapsed = f'{delta[3]} hours, {elapsed}'
    return elapsed


def converter(src: Path, dest: Path) -> str:
    log_file: Path = src.parent.joinpath('HEVC.log')
    if src.suffix in ['.mp4', '.mkv', '.avi', '.mov', '.wmv']:
        input_file: str = src.name
        new_name: str = f'{src.stem}.mp4'
        output_file: Path = dest.joinpath(new_name)
        start_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())

        print(f'\n{start_time}: STARTING {input_file}\n')

        # check if the file is already encoded in HEVC. If so, simply move it to the destination folder
        try:
            ffprobe: subprocess.CompletedProcess = subprocess.run(
                ['ffprobe', '-show_format', '-show_streams', '-loglevel', 'quiet', '-print_format', 'json', input_file],
                stdout=subprocess.PIPE, check=True)
            video_info = json.loads(ffprobe.stdout.decode())
            for stream in range(len(video_info['streams'])):
                if video_info['streams'][stream]['codec_name'] == 'hevc':
                    try:
                        move(input_file, dest)
                        end_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())
                        with open(log_file, 'a') as log:
                            log.write(f'[{end_time}] successfully moved ({input_file})\n')
                        print(f'{end_time}: FINISHED {input_file}\n')
                        return end_time
                    except FileExistsError:
                        end_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())
                        with open(log_file, 'a') as log:
                            log.write(f'[{end_time}] FAILED TO MOVE ({src.name})\n')
                        print(f'\n{end_time}: {src.name} cannot be moved\n')
                        return end_time
        except subprocess.CalledProcessError as e:
            end_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())
            print(f'{end_time}: Command {e.cmd} failed with error {e.returncode}\nOutput: {e.output}')
            return end_time

        # if it isn't already HEVC, re-encode
        try:
            result: subprocess.CompletedProcess = subprocess.run(
                ['ffmpeg', '-i', input_file, '-metadata', 'title=', '-c:v', 'hevc', '-c:a', 'copy', output_file],
                stdout=subprocess.PIPE, check=True)
            print(result.stdout.decode())
            end_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())
            with open(log_file, 'a') as log:
                log.write(f'[{end_time}] successfully converted ({input_file})\n')
            print(f'{end_time}: FINISHED {input_file}\n')
            return end_time
        except subprocess.CalledProcessError as e:
            end_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())
            print(f'{end_time}: Command {e.cmd} failed with error {e.returncode}')
            with open(log_file, 'a') as log:
                log.write(f'[{end_time}] CONVERSION FAILED FOR ({input_file})\n')
            if output_file.exists():
                remove(output_file)
            return end_time

    else:
        end_time: str = strftime("%Y-%m-%d %H:%M:%S", localtime())
        if src.name not in [dest, log_file]:
            with open(log_file, 'a') as log:
                log.write(f'[{end_time}] CANNOT CONVERT ({src.name})\n')
            print(f'\n{end_time}: {src.name} cannot be converted\n')
        return end_time


if __name__ == '__main__':
    main(argv[1:])
