# convert video files to the H.265 codec
from sys import argv
from pathlib import Path
import subprocess


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


def selector(target: Path) -> list[Path]:
    selection: str = input(f'Would you like to convert all files in {target}? y/N ')
    if selection.lower() == ("y" or "yes"):
        dest: Path = make_destination_dir(target)
        files: list[Path] = [f for f in target.iterdir() if f.is_file()]
        return [files, dest]
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


def converter(file: Path, dest: Path) -> None:
    if file.suffix in ['.mp4', '.mkv', '.avi', '.mov', '.wmv']:
        input_file: str = file.name
        new_name: str = f'{file.stem}.mp4'
        output_file: Path = dest.joinpath(new_name)

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

        print(f'\nFINISHED {input_file}\n')
    else:
        print(f'\n{file.name} cannot be converted\n')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main(argv[1:])
