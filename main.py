# convert video files to the H.265 codec
import os
from sys import argv
from pathlib import Path
import subprocess
from datetime import date, time
from typing import Tuple, List


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
    if src.suffix in ['.mp4', '.mkv', '.avi', '.mov', '.wmv']:
        input_file: str = src.name
        new_name: str = f'{src.stem}.mp4'
        output_file: Path = dest.joinpath(new_name)
        log_file: Path = src.parent.joinpath('conversion.log')
        flag: bool = False

        print(f'\nSTARTING {input_file}\n')

        # print(f'input_file: {input_file}')
        # print(f'new name: {new_name}')
        # print(f'output_file: {output_file}')

        try:
            result: subprocess.CompletedProcess = subprocess.run(
                ['ffmpeg', '-i', input_file, '-metadata', 'title=', '-c:v', 'hevc', '-c:a', 'copy', output_file],
                stdout=subprocess.PIPE, check=True)
            print(result.stdout.decode())
        except subprocess.CalledProcessError as e:
            print(f'Command {e.cmd} failed with error {e.returncode}')
            flag = True
            with open(log_file, 'a') as log:
                now = f'{date.today()} {time.hour}:{time.minute}'
                log.write(f'{now}: CONVERSION FAILED FOR ({input_file})\n')
            if output_file.exists():
                os.remove(output_file)
        if not flag:
            with open(log_file, 'a') as log:
                now = f'{date.today()} {time.hour}:{time.minute}'
                log.write(f'{now}: successfully converted ({input_file})\n')
        print(f'FINISHED {input_file}\n')
    else:
        print(f'\n{src.name} cannot be converted\n')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main(argv[1:])
