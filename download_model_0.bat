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
echo [2/3] ��¡ Hugging Face �ֿ�: Systran/faster-whisper-small
cd models
if exist faster-whisper-small (
    echo �Ѵ��� faster-whisper-small �ļ��У����Ը���...
    cd faster-whisper-small
    git pull
    cd ..
) else (
    git clone https://huggingface.co/Systran/faster-whisper-small
)

echo.
echo [3/3] ��ʼ���ش��ļ� (model.bin ��)...
cd faster-whisper-small
git lfs pull

echo.
echo [���] ģ��������ɣ�
echo ģ��·��: %cd%

pause
