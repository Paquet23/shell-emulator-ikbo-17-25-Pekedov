"""CSV VFS: дерево каталогов и двоичные данные только в памяти."""

import base64
import binascii
import csv
import io
from pathlib import Path, PurePosixPath

HEADER = ["path", "type", "base64_content"]


def normalize_path(value):
    """Проверить виртуальный путь и привести к абсолютному виду."""
    if not value or "\\" in value or "\x00" in value:
        raise ValueError("invalid VFS path")
    path = PurePosixPath("/" + value.lstrip("/"))
    if ".." in path.parts:
        raise ValueError("parent traversal is forbidden")
    return str(path)


class VirtualFileSystem:
    """Хранить пути: None для каталога, bytes для файла."""

    def __init__(self):
        """Создать минимальную VFS."""
        self.entries = {"/": None}

    @classmethod
    def load(cls, path):
        """Загрузить CSV целиком без распаковки в реальную ФС."""
        text = Path(path).read_text(encoding="utf-8-sig")
        reader = csv.DictReader(io.StringIO(text), delimiter=";", strict=True)
        if reader.fieldnames != HEADER:
            raise ValueError("expected header: path;type;base64_content")
        result = cls()
        result.entries = {}
        for row in reader:
            result.add_row(row)
        result.validate_tree()
        return result

    def add_row(self, row):
        """Проверить и добавить одну запись CSV."""
        if set(row) != set(HEADER) or any(v is None for v in row.values()):
            raise ValueError("wrong number of CSV fields")
        path = normalize_path(row["path"])
        if path in self.entries:
            raise ValueError(f"duplicate path: {path}")
        kind, content = row["type"], row["base64_content"]
        if kind == "dir" and not content:
            self.entries[path] = None
        elif kind == "file":
            try:
                self.entries[path] = base64.b64decode(content, validate=True)
            except (binascii.Error, ValueError) as error:
                raise ValueError(f"invalid base64: {path}") from error
        else:
            raise ValueError(f"invalid type or directory content: {path}")

    def validate_tree(self):
        """Потребовать корень и существующие родительские каталоги."""
        if "/" not in self.entries or self.entries["/"] is not None:
            raise ValueError("root directory is required")
        for path in self.entries:
            parent = str(PurePosixPath(path).parent)
            if parent not in self.entries or self.entries[parent] is not None:
                raise ValueError(f"parent directory is missing: {path}")

    def save(self, path):
        """Сохранить дерево в исходном CSV-формате служебной командой."""
        with Path(path).open("w", encoding="utf-8", newline="") as target:
            writer = csv.writer(target, delimiter=";")
            writer.writerow(HEADER)
            for name, data in sorted(self.entries.items()):
                kind = "dir" if data is None else "file"
                content = ("" if data is None
                           else base64.b64encode(data).decode())
                writer.writerow([name, kind, content])
