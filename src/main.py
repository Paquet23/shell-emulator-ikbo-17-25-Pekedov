"""CLI эмулятора оболочки: вариант 21, этапы 1-3."""

import argparse
from pathlib import Path
import sys


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
    if settings.script_path:
        status = run_script(settings.script_path, name)
        if status != "continue":
            return 1 if status == "error" else 0
    run_repl(name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
