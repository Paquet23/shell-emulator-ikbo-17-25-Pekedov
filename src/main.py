"""CLI эмулятора оболочки: вариант 21, этапы 1-3."""

import argparse
import csv
from pathlib import Path
import sys

from vfs import VirtualFileSystem


def save_vfs(args, vfs):
    """Проверить параметры и сохранить VFS."""
    if len(args) != 1:
        print_error("vfs-save: expected one path")
        return "error"
    try:
        vfs.save(args[0])
    except (OSError, UnicodeError, ValueError, csv.Error) as error:
        print_error(f"vfs-save: {error}")
        return "error"
    print(f"VFS saved: {args[0]}", flush=True)
    return "continue"


def print_error(message):
    """Вывести диагностику."""
    print(f"Error: {message}", file=sys.stderr, flush=True)


def parse_command(user_input):
    """Разделить ввод по пробельным символам."""
    parts = user_input.split()
    return (parts[0], parts[1:]) if parts else (None, [])


def execute_command(command, args, vfs=None):
    """Вернуть continue, exit или error после выполнения команды."""
    if command is None:
        return "continue"
    if command == "vfs-save":
        return save_vfs(args, vfs)
    if command == "exit":
        if args:
            print_error("exit: arguments are not allowed")
            return "error"
        print("Goodbye!", flush=True)
        return "exit"
    if command in {"ls", "cd"}:
        if len(args) > 1 or (command == "cd" and not args):
            print_error(f"{command}: invalid arguments")
            return "error"
        print(f"[STUB] {command} called with args: {args}", flush=True)
        return "continue"
    print_error(f"unknown command '{command}'")
    return "error"


def run_script(path, vfs_name, vfs=None):
    """Исполнить UTF-8 скрипт до первой ошибки или exit."""
    try:
        lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as error:
        print_error(f"script: {error}")
        return "error"
    for number, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        print(f"{vfs_name}> {line}", flush=True)
        status = execute_command(*parse_command(line), vfs)
        if status == "error":
            print_error(f"script {path}:{number}: stopped at first error")
        if status != "continue":
            return status
    return "continue"


def run_repl(vfs_name, vfs=None):
    """Читать команды до exit, EOF или Ctrl+C."""
    print(f"Shell Emulator started. VFS: {vfs_name}")
    while True:
        try:
            line = input(f"{vfs_name}> ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return
        if execute_command(*parse_command(line), vfs) == "exit":
            return


def main(argv=None):
    """Разобрать настройки и запустить эмулятор."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vfs-path", help="путь к CSV-файлу VFS")
    parser.add_argument("--script-path", help="путь к стартовому скрипту")
    settings = parser.parse_args(argv)
    print(f"[CONFIG] vfs_path={settings.vfs_path!r}", flush=True)
    print(f"[CONFIG] script_path={settings.script_path!r}", flush=True)
    name = Path(settings.vfs_path).stem if settings.vfs_path else "default_vfs"
    try:
        vfs = (VirtualFileSystem.load(settings.vfs_path)
               if settings.vfs_path else VirtualFileSystem())
    except (OSError, UnicodeError, ValueError, csv.Error) as error:
        print_error(f"VFS: {error}")
        return 1
    if settings.script_path:
        status = run_script(settings.script_path, name, vfs)
        if status != "continue":
            return 1 if status == "error" else 0
    run_repl(name, vfs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
