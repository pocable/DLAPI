@echo off
setlocal
call ENVIRONMENT.bat
python -m nose
endlocal