@echo off
for /F "tokens=1* delims==" %%a in (windowsenv.txt) do (
  set "%%a=%%b"
)
echo Environment variables have been set.
