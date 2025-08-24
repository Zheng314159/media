@echo off
REM =======================================
REM  一键下载 faster-whisper 模型到 media\models\
REM  依赖: git, git-lfs
REM =======================================

setlocal

REM 切换到脚本所在目录（你的项目根目录）
cd /d %~dp0

REM 确保存在 media\models 目录
if not exist "models" (
    mkdir models
)

echo.
echo [1/3] 初始化 Git LFS...
git lfs install

echo.
echo [2/3] 克隆 Hugging Face 仓库: ushindianalytics/tacotron2-ddc-ljspeech
cd models
if exist tacotron2-ddc-ljspeech (
    echo 已存在 tacotron2-ddc-ljspeech 文件夹，尝试更新...
    cd tacotron2-ddc-ljspeech
    git pull
    cd ..
) else (
    git clone https://huggingface.co/ushindianalytics/tacotron2-ddc-ljspeech
)

echo.
echo [3/3] 开始下载大文件 (model.bin 等)...
cd tacotron2-ddc-ljspeech
git lfs pull

echo.
echo [完成] 模型下载完成！
echo 模型路径: %cd%

pause
