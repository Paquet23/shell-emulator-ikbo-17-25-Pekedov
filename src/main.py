"""
Shell Emulator - Этап 1 (REPL)
Вариант 21, ИКБО-17-25
Эмулятор командной оболочки UNIX-подобной ОС
"""

import sys


def print_error(message):
    """Выводит сообщение об ошибке в стандартный поток ошибок."""
    print(f"Error: {message}", file=sys.stderr)


def parse_command(user_input):
    """
    Парсит ввод пользователя.
    Разделяет команду и аргументы по пробелам.
    Возвращает кортеж (command, args) или (None, []) для пустого ввода.
    """
    parts = user_input.strip().split()
    if not parts:
        return None, []
    return parts[0], parts[1:]


def execute_command(command, args):
    """
    Выполняет команду эмулятора.
    Возвращает True, если нужно продолжить работу.
    """
    if command == "exit":
        print("Goodbye!")
        return False

    if command == "ls":
        print(f"[STUB] ls called with args: {args}")
        return True

    if command == "cd":
        if not args:
            print_error("cd: missing argument")
            return True
        print(f"[STUB] cd called with args: {args}")
        return True

    print_error(f"unknown command '{command}'")
    return True


def run_repl(vfs_name):
    """
    Основной цикл REPL (Read-Eval-Print Loop).
    Отображает приглашение с именем VFS.
    """
    prompt = f"{vfs_name}> "
    print(f"Shell Emulator started. VFS: {vfs_name}")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input(prompt)
        except EOFError:
            print("\nGoodbye!")
            break

        command, args = parse_command(user_input)
        if command is None:
            continue

        if not execute_command(command, args):
            break


def main():
    """Точка входа в приложение."""
    vfs_name = sys.argv[1] if len(sys.argv) > 1 else "default_vfs"
    run_repl(vfs_name)


if __name__ == "__main__":
    main()
