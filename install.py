# install.py — 供 CI 调用（已改为避免打印不可编码字符）
from pathlib import Path
import shutil
import sys
import json
import os
import subprocess
import platform
from configure import configure_ocr_model

working_dir = Path(__file__).resolve().parent
install_path = working_dir / "install"
version = len(sys.argv) > 1 and sys.argv[1] or "v0.0.1"

def install_deps():
    """复制 MaaFramework 二进制到 install 目录"""
    deps_path = working_dir / "deps"
    if not (deps_path / "bin").exists():
        print("Please download the MaaFramework into 'deps' first.")
        sys.exit(1)

    print("Copying MaaFramework binaries...")
    shutil.copytree(
        deps_path / "bin",
        install_path,
        ignore=shutil.ignore_patterns(
            "*MaaDbgControlUnit*",
            "*MaaThriftControlUnit*",
            "*MaaRpc*",
            "*MaaHttp*",
        ),
        dirs_exist_ok=True,
    )
    shutil.copytree(
        deps_path / "share" / "MaaAgentBinary",
        install_path / "MaaAgentBinary",
        dirs_exist_ok=True,
    )

def install_python_packages():
    """
    如果 embed python 存在，则确保 maafw 已安装（使用 embed python 的 pip）。
    在 CI 已经通常安装好 maafw；这里运行时会尝试检测并安装。
    """
    python_embed = install_path / "python" / "python.exe"

    if not python_embed.exists():
        print("No embedded Python detected — skipping embedded python check.")
        return

    print(f"Detected embedded Python: {python_embed}")
    try:
        # 先检查 pip/maafw 可用性
        subprocess.check_call([str(python_embed), "-m", "pip", "--version"])
    except Exception:
        print("Pip not available in embedded Python; attempting to install pip using get-pip.py")
        # 保守处理：如果 CI 已经写好 get-pip 步骤，这里可跳过。若需要可在 CI 下载 get-pip.py 到 install/
        try:
            # 如果 get-pip.py 已经被放置到 working_dir，使用它
            gp = working_dir / "get-pip.py"
            if gp.exists():
                subprocess.check_call([str(python_embed), str(gp)])
            else:
                print("get-pip.py not found, skipping pip bootstrap here.")
        except Exception as e:
            print("Failed to bootstrap pip:", e)

    # 检查 maafw 是否可用
    try:
        subprocess.check_call([str(python_embed), "-m", "maa", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("maafw appears available in the embedded Python.")
    except Exception:
        print("maafw not found in embedded Python — attempting to install maafw via pip.")
        try:
            subprocess.check_call([str(python_embed), "-m", "pip", "install", "--upgrade", "maafw"])
            print("maafw installed successfully in embedded Python.")
        except Exception as e:
            print("Failed to install maafw in embedded python:", e)

def install_resource():
    """复制资源文件并配置 OCR 模型"""
    print("Installing resources...")
    try:
        configure_ocr_model()
    except Exception as e:
        print("configure_ocr_model() failed:", e)

    shutil.copytree(
        working_dir / "assets" / "resource",
        install_path / "resource",
        dirs_exist_ok=True,
    )
    shutil.copy2(working_dir / "assets" / "interface.json", install_path)

    with open(install_path / "interface.json", "r", encoding="utf-8") as f:
        interface = json.load(f)
    interface["version"] = version
    with open(install_path / "interface.json", "w", encoding="utf-8") as f:
        json.dump(interface, f, ensure_ascii=False, indent=4)

def install_chores():
    """复制 README/LICENSE 等"""
    print("Copying docs...")
    for fname in ["README.md", "LICENSE"]:
        src = working_dir / fname
        if src.exists():
            shutil.copy2(src, install_path)

def install_agent():
    """复制 agent 脚本"""
    print("Copying agent scripts...")
    shutil.copytree(
        working_dir / "agent",
        install_path / "agent",
        dirs_exist_ok=True,
    )



if __name__ == "__main__":
    install_path.mkdir(exist_ok=True)
    print(f"Installing to: {install_path}")

    print("Step 1: Installing MaaFramework files...")
    install_deps()

    print("Step 2: Verifying Python environment...")
    install_python_packages()

    print("Step 3: Installing resources...")
    install_resource()

    print("Step 4: Copying misc files...")
    install_chores()

    print("Step 5: Installing agent scripts...")
    install_agent()


    print(f"Installation completed successfully to {install_path}")
