@echo off
setlocal

set VENV=F:\media\.venv\Scripts\python.exe
set INPUT_TXT=input.txt
set OUTPUT_DIR=outputs

if not exist %OUTPUT_DIR% (
    mkdir %OUTPUT_DIR%
)

%VENV% -m cog.cli predict -i text="@%INPUT_TXT%" -i speaker=@4.MOV > %OUTPUT_DIR%\result.wav

echo ✅ 生成完成: %OUTPUT_DIR%\result.wav
endlocal
pause
