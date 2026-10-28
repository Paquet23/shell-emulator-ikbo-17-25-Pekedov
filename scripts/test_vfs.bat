@echo off
setlocal
pushd "%~dp0.."
python src\main.py --help
python src\main.py --script-path test_data/exit.txt
python src\main.py --vfs-path test_data/vfs_minimal.csv < NUL
python src/main.py --vfs-path test_data/vfs_minimal.csv --script-path test_data/success.txt
python src/main.py --vfs-path test_data/vfs_files.csv --script-path test_data/success.txt
python src/main.py --vfs-path test_data/vfs_deep.csv --script-path test_data/success.txt
python src/main.py --vfs-path test_data/vfs_deep.csv --script-path test_data/test_script.txt
python src/main.py --vfs-path test_data/vfs_deep.csv --script-path test_data/error_args.txt
python src/main.py --vfs-path test_data/vfs_deep.csv --script-path test_data/error_ls.txt
python src/main.py --vfs-path test_data/vfs_deep.csv --script-path test_data/error_exit.txt
python src/main.py --vfs-path test_data/vfs_deep.csv --script-path test_data/error_save.txt
python src/main.py --vfs-path test_data/vfs_deep.csv --script-path test_data/error_write.txt
python src/main.py --vfs-path test_data/missing.csv
python src/main.py --vfs-path test_data/vfs_invalid.csv
python src/main.py --script-path test_data/missing.txt
popd
