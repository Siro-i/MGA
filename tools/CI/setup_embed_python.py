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
        # return 

    print(f"=== Setting up Embedded Python {PYTHON_VERSION} ===")
    
    if not PYTHON_DIR.exists():
        PYTHON_DIR.mkdir(parents=True, exist_ok=True)

    # 2. 下载并解压 Python Embed 包
    zip_path = PROJECT_ROOT / "python-embed.zip"
    download_file(EMBED_URL, zip_path)
    
    print("Extracting Python...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(PYTHON_DIR)
    os.remove(zip_path)

    # 3. 修正 ._pth 文件 (开启 site-packages 支持)
    ver_tag = PYTHON_VERSION.replace('.', '')[:3] 
    
    pth_file = PYTHON_DIR / f"python{ver_tag}._pth" 
    
    # 如果通过名称算出来的文件不存在，尝试找一下实际存在的 ._pth 文件
    if not pth_file.exists():
        found = list(PYTHON_DIR.glob("python*._pth"))
        if found:
            pth_file = found[0]
            print(f"Detected pth file: {pth_file.name}")

    if pth_file.exists():
        print(f"Patching {pth_file.name} to enable site-packages...")
        zip_name = f"python{ver_tag}.zip" 
        
        with open(pth_file, "w", encoding="utf-8") as f:
            f.write(f"{zip_name}\n")
            f.write(".\n")
            f.write("Lib/site-packages\n")
            f.write("import site\n")
    else:
        print("[Error] Could not find ._pth file to patch!")
        sys.exit(1)

    # 4. 下载并安装 pip
    get_pip_path = PROJECT_ROOT / "get-pip.py"
    download_file(PIP_URL, get_pip_path)
    
    print("Installing pip...")
    # 使用 full_path 确保调用的是刚才解压的 python
    subprocess.check_call([str(PYTHON_EXE), str(get_pip_path)])
    os.remove(get_pip_path)

    # 5. 安装基础依赖
    print("Installing dependencies (maafw, numpy)...")
    subprocess.check_call([str(PYTHON_EXE), "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([str(PYTHON_EXE), "-m", "pip", "install", "maafw", "numpy"])

    # 6. 补齐标准库 (从宿主环境复制 Lib)
    host_python_lib = Path(sys.executable).parent / "Lib"
    target_lib = PYTHON_DIR / "Lib"
    
    if host_python_lib.exists():
        print(f"Copying standard library from host ({host_python_lib})...")
        try:
            shutil.copytree(host_python_lib, target_lib, dirs_exist_ok=True)
        except Exception as e:
            print(f"[Warning] Failed to copy standard library: {e}")
    else:
        print("[Warning] Host Python Lib directory not found.")

    print("=== Embedded Python Setup Complete ===")

if __name__ == "__main__":
    setup_embed_python()