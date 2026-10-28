@echo off
setlocal
pushd "%~dp0"
python src\main.py %*
set "result=%errorlevel%"
popd
exit /b %result%
