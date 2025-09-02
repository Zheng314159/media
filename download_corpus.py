import os
import subprocess
import requests
from urllib.parse import urlparse

# 下载目录
DATA_DIR = "datasets"
os.makedirs(DATA_DIR, exist_ok=True)

# 开源中文语料库
CORPUS = {
    # "AISHELL-1": "http://www.openslr.org/resources/33/data_aishell.tgz",
    # "faster-whisper-small":"https://huggingface.co/Systran/faster-whisper-small/tree/main"
    "tacotron2-DDC-GST":"https://coqui.gateway.scarf.sh/v0.6.1_models/tts_models--zh-CN--baker--tacotron2-DDC-GST.zip"
}

# 从环境变量读取代理
HTTP_PROXY =  os.getenv("http_proxy", "http://127.0.0.1:1081")
HTTPS_PROXY = os.getenv("https_proxy", "http://127.0.0.1:1081")
PROXIES = {"http": HTTP_PROXY, "https": HTTPS_PROXY} 

def download_with_aria2c(url, save_dir=DATA_DIR):
    """
    使用 aria2c 多线程下载
    """
    file_name = os.path.basename(urlparse(url).path)
    output_path = os.path.join(save_dir, file_name)

    if os.path.exists(output_path):
        print(f"✅ 已存在: {output_path}")
        return output_path

    print(f"⬇️ 正在下载: {url}")

    ARIA2C_PATH = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\aria2c.exe"
    cmd = [
        ARIA2C_PATH, "-x", "16", "-s", "16", "-k", "1M",
        "-d", save_dir, "-o", file_name, url
    ]

    # 如果有代理，传给 aria2c
    if HTTP_PROXY or HTTPS_PROXY:
        proxy = HTTPS_PROXY or HTTP_PROXY
        cmd += ["--all-proxy", proxy]

    subprocess.run(cmd, check=True)
    return output_path


def resolve_final_url(url):
    """
    跟随跳转，返回最终下载地址
    """
    try:
        r = requests.get(url, stream=True, allow_redirects=True, proxies=PROXIES, timeout=15)
        if r.status_code == 200:
            return r.url
        else:
            print(f"⚠️ 请求异常 {url}: {r.status_code}")
            return None
    except Exception as e:
        print(f"❌ 请求失败 {url}: {e}")
        return None


if __name__ == "__main__":
    for name, url in CORPUS.items():
        print(f"\n=== {name} ===")
        final_url = resolve_final_url(url)
        if final_url:
            print(f"👉 最终地址: {final_url}")
            download_with_aria2c(final_url)
        else:
            print(f"跳过 {name}，链接不可用")
