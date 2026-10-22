@echo off
echo === Тест 1: Запуск с VFS ===
python src/main.py --vfs-path test_data/vfs_minimal.csv

echo === Тест 2: Запуск со скриптом ===
python src/main.py --script-path test_data/test_script.txt
pause
