import argparse
import os
import platform
import zipfile
import tarfile
import urllib.request
import json
import shutil
from pathlib import Path

# === 配置项 ===
MAA_REPO = "MaaXYZ/MaaFramework"
MFA_REPO = "SweetSmellFox/MFAAvalonia" # [修改] 统一使用 MFAAvalonia

# 脚本位于 tools/ci/，所以项目根目录是向上三级
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def get_latest_release_url(repo, filter_func):
    """获取 GitHub 最新 Release 的下载链接"""
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        print(f"Fetching latest release for {repo}...")
        req = urllib.request.Request(api_url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            for asset in data.get("assets", []):
                if filter_func(asset["name"]):
                    return asset["browser_download_url"], asset["name"]
    except Exception as e:
        print(f"Failed to fetch release info: {e}")
    return None, None

def download_and_extract(url, filename, extract_to):
    """下载并解压"""
    if not url:
        return False
        
    print(f"Downloading {url}...")
    try:
        with urllib.request.urlopen(url) as response, open(filename, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        
        print(f"Extracting to {extract_to}...")
        if os.path.exists(extract_to):
            shutil.rmtree(extract_to)
        os.makedirs(extract_to, exist_ok=True)
        
        if filename.endswith(".zip"):
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        elif filename.endswith("tar.gz") or filename.endswith(".tgz"):
            with tarfile.open(filename, "r:gz") as tar_ref:
                tar_ref.extractall(extract_to)
        
        os.remove(filename)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def configure_ocr_model(root_dir):
    """配置 OCR 模型"""
    assets_dir = root_dir / "assets"
    assets_ocr_dir = assets_dir / "MaaCommonAssets" / "OCR"
    
    if not assets_ocr_dir.exists():
        print(f"[Warning] MaaCommonAssets not found at {assets_ocr_dir}")
        return

    ocr_dir = assets_dir / "resource" / "model" / "ocr"
    if not ocr_dir.exists():
        print("Copying default OCR model...")
        try:
            shutil.copytree(
                assets_ocr_dir / "ppocr_v5" / "zh_cn",
                ocr_dir,
                dirs_exist_ok=True,
            )
            print("OCR model configured.")
        except Exception as e:
            print(f"[Error] Failed to copy OCR model: {e}")
    else:
        print("Found existing OCR directory, skipping copy.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--os", help="Target OS (Windows, Linux, macOS, Android)")
    parser.add_argument("--arch", help="Target Arch (x86_64, aarch64)")
    args = parser.parse_args()

    # 1. 确定系统环境
    system = (args.os if args.os else platform.system()).lower()
    machine = (args.arch if args.arch else platform.machine()).lower()
    
    # 映射到 MAA/MFA 命名规则
    if system.startswith("win"): 
        os_name = "win"
        mfa_os_key = "win"
    elif system.startswith("mac") or system == "darwin": 
        os_name = "macos"
        mfa_os_key = "osx"
    elif system.startswith("linux"): 
        os_name = "linux"
        mfa_os_key = "linux"
    elif system == "android":
        os_name = "android"
        mfa_os_key = None
        
    arch_name = "aarch64" if "arm" in machine or "aarch64" in machine else "x86_64"
    if system == "android": arch_name = args.arch

    print(f"Configuring for {os_name}-{arch_name}...")

    # 2. 下载 MaaFramework
    # 规则: MAA-{os}-{arch}
    def maa_filter(name):
        return f"MAA-{os_name}-{arch_name}" in name and (name.endswith(".zip") or name.endswith(".tar.gz"))

    maa_url, maa_name = get_latest_release_url(MAA_REPO, maa_filter)
    if maa_url:
        download_and_extract(maa_url, maa_name, PROJECT_ROOT / "deps")
    else:
        print(f"[Error] Failed to find MaaFramework release for {os_name}-{arch_name}")
        exit(1)

    # 3. 下载 MFA (前端) 
    mfa_extract_dir = PROJECT_ROOT / "MFA"
    mfa_url = None
    mfa_name = None
    
    if os_name != "android":
        # 统一逻辑：Windows/Linux/macOS 都使用 MFAAvalonia
        # 架构映射: x86_64 -> x64, aarch64 -> arm64
        mfa_arch = "x64" if arch_name == "x86_64" else "arm64"
        
        def mfa_filter(name): 
            # 匹配规则: 包含系统名(win/osx/linux) 和 架构名(x64/arm64)
            return mfa_os_key in name and mfa_arch in name and (name.endswith(".zip") or name.endswith(".tar.gz"))
            
        mfa_url, mfa_name = get_latest_release_url(MFA_REPO, mfa_filter)

    if mfa_url:
        download_and_extract(mfa_url, mfa_name, mfa_extract_dir)
        print("MFA frontend configured.")
    elif os_name != "android":
        print(f"[Warning] Failed to find MFAAvalonia for {os_name}-{arch_name}")

    # 4. 配置资源
    configure_ocr_model(PROJECT_ROOT)
    
    print("Configuration done.")

if __name__ == "__main__":
    main()