import os
import sys
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

# === 配置 ===
PYTHON_VERSION = "3.11.9"
EMBED_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

# 定义路径 (假设脚本在 tools/ci/ 下，项目根目录在 ../../)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INSTALL_DIR = PROJECT_ROOT / "install"
PYTHON_DIR = INSTALL_DIR / "python"
PYTHON_EXE = PYTHON_DIR / "python.exe"

def download_file(url, dest_path):
    print(f"Downloading {url}...")
    try:
        urllib.request.urlretrieve(url, dest_path)
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        sys.exit(1)

def setup_embed_python():
    # 1. 检查是否已安装
    if PYTHON_EXE.exists():
        print(f"Embedded Python already exists at {PYTHON_EXE}")
        # 你可以在这里加逻辑判断是否强制重新安装
        # return 

    print(f"=== Setting up Embedded Python {PYTHON_VERSION} ===")
    
    # 准备目录
    if not PYTHON_DIR.exists():
        PYTHON_DIR.mkdir(parents=True, exist_ok=True)

    # 2. 下载并解压 Python Embed 包
    zip_path = PROJECT_ROOT / "python-embed.zip"
    download_file(EMBED_URL, zip_path)
    
    print("Extracting Python...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(PYTHON_DIR)
    os.remove(zip_path) # 清理压缩包

    # 3. 修正 ._pth 文件 (开启 site-packages 支持)
    # 默认的 python311._pth 会忽略 site-packages，导致无法使用 pip 安装的库
    pth_file = PYTHON_DIR / f"python{PYTHON_VERSION.replace('.', '')[:2]}._pth" # e.g. python311._pth
    if not pth_file.exists():
        # 尝试模糊匹配
        pth_files = list(PYTHON_DIR.glob("python*._pth"))
        if pth_files: pth_file = pth_files[0]

    if pth_file.exists():
        print(f"Patching {pth_file.name} to enable site-packages...")
        with open(pth_file, "w", encoding="utf-8") as f:
            f.write(f"python{PYTHON_VERSION.replace('.', '')[:2]}.zip\n")
            f.write(".\n")
            f.write("Lib/site-packages\n") # 关键：添加这一行
            f.write("import site\n")       # 关键：添加这一行
    else:
        print("[Warning] Could not find ._pth file to patch!")

    # 4. 下载并安装 pip
    get_pip_path = PROJECT_ROOT / "get-pip.py"
    download_file(PIP_URL, get_pip_path)
    
    print("Installing pip...")
    subprocess.check_call([str(PYTHON_EXE), str(get_pip_path)])
    os.remove(get_pip_path) # 清理

    # 5. 安装基础依赖 (maafw, numpy)
    print("Installing dependencies (maafw, numpy)...")
    subprocess.check_call([str(PYTHON_EXE), "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([str(PYTHON_EXE), "-m", "pip", "install", "maafw", "numpy"])

    # 6. [关键] 补齐标准库 (从宿主环境复制 Lib)
    # GitHub Actions 的 Windows 环境里，运行此脚本的 `python` 是完整的。
    # 我们将其 Lib 目录复制给嵌入式 Python，以修复缺失的标准库（如 tkinter, unittest 等）。
    host_python_lib = Path(sys.executable).parent / "Lib"
    target_lib = PYTHON_DIR / "Lib"
    
    if host_python_lib.exists():
        print(f"Copying standard library from host ({host_python_lib})...")
        try:
            # dirs_exist_ok=True 允许覆盖或合并
            shutil.copytree(host_python_lib, target_lib, dirs_exist_ok=True)
        except Exception as e:
            print(f"[Warning] Failed to copy standard library: {e}")
    else:
        print("[Warning] Host Python Lib directory not found. Embedded Python might lack standard libraries.")

    print("=== Embedded Python Setup Complete ===")

if __name__ == "__main__":
    setup_embed_python()