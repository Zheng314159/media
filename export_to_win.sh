#!/bin/bash

SRC="$HOME/projects/media"
DEST="/mnt/f/media"

echo "📤 正在将 WSL 项目 $SRC 导出到 Windows 目录 $DEST..."

mkdir -p "$DEST"

rsync -avh --progress \
  --exclude '.venv/' \
  --exclude 'frontend/node_modules/' \
  --exclude 'frontend/dist/' \
  --exclude 'alembic/versions/' \
  --exclude 'mediaenv/' \
  --exclude '__pycache__/' \
  --exclude '.git/' \
  --exclude '*.pyc' \
  --exclude '*.pyo' \
  --exclude '*.pyd' \
  "$SRC/" "$DEST/"

echo "✅ 导出完成！"
du -sh "$DEST"
