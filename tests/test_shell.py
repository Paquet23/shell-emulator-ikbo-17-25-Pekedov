"""Проверки сценариев этапов 1-3 без сторонних зависимостей."""

import base64
import contextlib
import csv
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from main import execute_command, parse_command, run_script
from vfs import VirtualFileSystem


class VfsTests(unittest.TestCase):
    """Проверить загрузку, валидацию и сохранение CSV."""

    def setUp(self):
        """Подготовить изолированный каталог."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "vfs.csv"

    def write_rows(self, rows):
        """Записать тестовую VFS."""
        with self.path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.writer(target, delimiter=";")
            writer.writerow(["path", "type", "base64_content"])
            writer.writerows(rows)

    def test_fixtures_and_source_unchanged(self):
        """Все три дерева читаются без изменения источника."""
        for name in ("minimal", "files", "deep"):
            path = ROOT / "test_data" / f"vfs_{name}.csv"
            before = path.read_bytes()
            vfs = VirtualFileSystem.load(path)
            self.assertIsNone(vfs.entries["/"])
            self.assertEqual(before, path.read_bytes())
        self.assertIn("/home/user/docs/notes.txt", vfs.entries)

    def test_binary_roundtrip(self):
        """Все значения байтов сохраняются и загружаются без потерь."""
        binary = bytes(range(256))
        encoded = base64.b64encode(binary).decode()
        self.write_rows([["/", "dir", ""], ["data", "file", encoded]])
        original = VirtualFileSystem.load(self.path)
        self.path.unlink()
        self.assertEqual(binary, original.entries["/data"])
        original.save(self.path)
        self.assertEqual(original.entries,
                         VirtualFileSystem.load(self.path).entries)

    def test_invalid_trees(self):
        """Отклонить поврежденные записи и неоднозначные деревья."""
        cases = [[], [["/", "file", ""]],
                 [["/", "dir", ""], ["/", "dir", ""]],
                 [["/", "dir", ""], ["a/b", "file", ""]],
                 [["/", "dir", ""], ["a", "file", "%%%"]],
                 [["/", "dir", ""], ["../a", "dir", ""]],
                 [["/", "dir", "payload"]],
                 [["/", "dir", ""], ["a", "other", ""]],
                 [["/", "dir", ""], ["a", "file", "", "extra"]],
                 [["/", "dir", ""], ["a", "file", ""],
                  ["a/b", "dir", ""]]]
        for rows in cases:
            with self.subTest(rows=rows):
                self.write_rows(rows)
                with self.assertRaises(ValueError):
                    VirtualFileSystem.load(self.path)

    def test_missing_and_invalid_header(self):
        """Сообщить об отсутствующем файле и неверном заголовке."""
        with self.assertRaises(OSError):
            VirtualFileSystem.load(self.path)
        self.path.write_text("not a CSV header", encoding="utf-8")
        with self.assertRaises(ValueError):
            VirtualFileSystem.load(self.path)


class ShellTests(unittest.TestCase):
    """Проверить CLI и остановку сценариев."""

    def cli(self, *args, input_text=""):
        """Запустить настоящую точку входа отдельным процессом."""
        return subprocess.run(
            [sys.executable, str(ROOT / "src/main.py"), *args],
            input=input_text, text=True, capture_output=True,
            cwd=ROOT, timeout=10)

    def test_parser(self):
        """Пустой ввод и пробельные разделители."""
        self.assertEqual((None, []), parse_command(" \t"))
        self.assertEqual(("ls", ["a", "b"]), parse_command(" ls\ta b "))

    def test_repl_errors_do_not_stop_session(self):
        """В интерактивном режиме ошибка допускает следующую команду."""
        result = self.cli(input_text="bad\ncd\nls a b\nexit x\nls\nexit\n")
        self.assertEqual(0, result.returncode)
        self.assertIn("default_vfs>", result.stdout)
        self.assertIn("[STUB] ls", result.stdout)
        self.assertEqual(4, result.stderr.count("Error:"))

    def test_script_stops_on_first_error(self):
        """После invalid_cmd команда cd user не исполняется."""
        result = self.cli("--script-path", "test_data/test_script.txt")
        self.assertEqual(1, result.returncode)
        self.assertIn("default_vfs> invalid_cmd", result.stdout)
        self.assertNotIn("cd user", result.stdout)
        self.assertIn(":6:", result.stderr)

    def test_script_failures(self):
        """Каждая ошибка аргументов останавливает стартовый скрипт."""
        names = ("error_args", "error_ls", "error_exit", "error_save",
                 "error_write")
        for name in names:
            with self.subTest(name=name):
                result = self.cli("--script-path", f"test_data/{name}.txt")
                self.assertEqual(1, result.returncode)
                self.assertIn("stopped at first error", result.stderr)

    def test_configuration_errors(self):
        """Ошибки параметров и чтения возвращают ненулевой код."""
        for args in [("--vfs-path", "missing.csv"),
                     ("--vfs-path", "test_data/vfs_invalid.csv"),
                     ("--script-path", "missing.txt"), ("--unknown",),
                     ("--vfs-path",)]:
            with self.subTest(args=args):
                self.assertNotEqual(0, self.cli(*args).returncode)

    def test_save_and_script_exit(self):
        """Сохранить загруженную VFS, exit завершает приложение."""
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "saved.csv"
            result = self.cli("--vfs-path", "test_data/vfs_deep.csv",
                              input_text=f"vfs-save {target}\nexit\n")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("vfs_deep>", result.stdout)
            expected = VirtualFileSystem.load(ROOT / "test_data/vfs_deep.csv")
            self.assertEqual(expected.entries,
                             VirtualFileSystem.load(target).entries)
        result = self.cli("--script-path", "test_data/exit.txt")
        self.assertEqual(0, result.returncode)
        self.assertNotIn("Shell Emulator started", result.stdout)

    def test_successful_script_continues_repl(self):
        """Пустые строки и комментарии пропускаются, затем доступен REPL."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "start.txt"
            path.write_text("# comment\n\nls\n", encoding="utf-8")
            result = self.cli("--script-path", str(path), input_text="exit\n")
        self.assertEqual(0, result.returncode)
        self.assertIn("Shell Emulator started", result.stdout)
        self.assertNotIn("# comment", result.stdout)


if __name__ == "__main__":
    unittest.main()
