#!/bin/bash
echo "=== Тест 1: Запуск с VFS ==="
bash run.sh --vfs-path test_data/vfs_minimal.csv

echo "=== Тест 2: Запуск со скриптом ==="
bash run.sh --script-path test_data/test_script.txt
