@echo off
REM =======================================
REM  һ������ faster-whisper ģ�͵� media\models\
REM  ����: git, git-lfs
REM =======================================

setlocal

REM �л����ű�����Ŀ¼�������Ŀ��Ŀ¼��
cd /d %~dp0

REM ȷ������ media\models Ŀ¼
if not exist "models" (
    mkdir models
)

echo.
echo [1/3] ��ʼ�� Git LFS...
git lfs install

echo.
echo [2/3] ��¡ Hugging Face �ֿ�: ushindianalytics/tacotron2-ddc-ljspeech
cd models
if exist tacotron2-ddc-ljspeech (
    echo �Ѵ��� tacotron2-ddc-ljspeech �ļ��У����Ը���...
    cd tacotron2-ddc-ljspeech
    git pull
    cd ..
) else (
    git clone https://huggingface.co/ushindianalytics/tacotron2-ddc-ljspeech
)

echo.
echo [3/3] ��ʼ���ش��ļ� (model.bin ��)...
cd tacotron2-ddc-ljspeech
git lfs pull

echo.
echo [���] ģ��������ɣ�
echo ģ��·��: %cd%

pause
