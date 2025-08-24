# cmd
set http_proxy=http://127.0.0.1:7890
set https_proxy=http://127.0.0.1:7890
# powershell
$env:http_proxy="http://127.0.0.1:7890"
$env:https_proxy="http://127.0.0.1:7890"

setx HF_ENDPOINT "https://hf-mirror.com"

Remove-Item -Recurse -Force models/XTTS-v2/.git

