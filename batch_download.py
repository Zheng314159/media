import os
import subprocess
import time
from urllib.parse import urlparse

# ---------- 配置区域 ----------
DATA_DIR = "datasets"                  # 下载目录
URL_FILE = "urls.txt"                  # 批量下载链接文件
ARIA2C_PATH = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\aria2c.exe"
RETRIES = 3                            # 下载失败最大重试次数

# 代理配置（可从环境变量读取，也可直接填写）
HTTP_PROXY = os.getenv("http_proxy", "http://127.0.0.1:1081")
HTTPS_PROXY = os.getenv("https_proxy", "http://127.0.0.1:1081")
PROXY = HTTPS_PROXY or HTTP_PROXY
# -------------------------------

def read_urls(file_path):
    """读取 urls.txt，每行一个 URL，忽略空行和注释"""
    urls = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls

def download_file(url, save_dir=DATA_DIR, retries=RETRIES, proxy=PROXY):
    """使用 aria2c 下载单个文件，支持 ghproxy + 代理"""
    parsed = urlparse(url)
    # ghproxy 要求去掉前面的 https://
    clean_url = parsed.netloc + parsed.path
    # proxy_url = f"https://ghproxy.com/{clean_url}"
    proxy_url = url  # 不用 ghproxy



    file_name = os.path.basename(parsed.path)
    output_path = os.path.join(save_dir, file_name)
    
    if os.path.exists(output_path):
        print(f"✅ 已存在: {output_path}")
        return output_path

    os.makedirs(save_dir, exist_ok=True)

    cmd = [
        ARIA2C_PATH,
        "-x", "1",       # 线程数
        "-s", "1",       # 连接数
        "-k", "1M",
        "-d", save_dir,
        "-o", file_name,
        proxy_url,
        "--all-proxy", proxy
    ]

    for attempt in range(1, retries + 1):
        print(f"⬇️ 第 {attempt} 次尝试下载: {file_name}")
        try:
            subprocess.run(cmd, check=True)
            print(f"✅ 下载完成: {file_name}\n")
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"⚠️ 下载失败: {e}")
            if attempt < retries:
                print("等待 5 秒后重试...")
                time.sleep(5)
            else:
                print(f"❌ 下载失败超过 {retries} 次: {file_name}\n")
                return None

if __name__ == "__main__":
    if not os.path.exists(URL_FILE):
        print(f"❌ {URL_FILE} 不存在，请先创建文件，每行一个下载链接。")
        exit(1)

    urls = read_urls(URL_FILE)
    print(f"[INFO] 读取到 {len(urls)} 个下载链接，开始批量下载...\n")

    for url in urls:
        download_file(url, DATA_DIR, RETRIES, PROXY)

    print("[INFO] 批量下载完成。")
