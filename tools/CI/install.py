# install.py — 供 CI 调用（已改为避免打印不可编码字符）
from pathlib import Path
import shutil
import sys
import json
import os
import subprocess
import platform
from tools.CI.configure import configure_ocr_model
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir / "tools" / "CI"))
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

def install_resource():
    """复制资源文件并配置 OCR 模型，同时动态修改 interface.json"""
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
    # 复制原始 interface.json 到安装目录
    shutil.copy2(working_dir / "assets" / "interface.json", install_path)

    # 读取并修改 interface.json
    json_path = install_path / "interface.json"
    with open(json_path, "r", encoding="utf-8") as f:
        interface = json.load(f)

    # === [关键修改] 针对 Windows 使用内嵌 Python 路径 ===
    if platform.system() == "Windows":
        print("[Config] Detecting Windows build: Pointing agent to embedded Python.")
        # 这里使用相对路径，相对于 MFA.exe 所在的目录
        # 注意：JSON中使用正斜杠 / 在 Windows 上通常也是兼容的，且更安全
        interface["agent"]["child_exec"] = "./python/python.exe"
    else:
        print("[Config] Detecting Non-Windows build: Using system python3.")
        # Linux/Mac 通常叫 python3，比 python 更准确
        interface["agent"]["child_exec"] = "python3"

    # 更新版本号
    interface["version"] = version

    # 写回文件
    with open(json_path, "w", encoding="utf-8") as f:
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

    print("Step 2: Installing resources...")
    install_resource()

    print("Step 3: Copying misc files...")
    install_chores()

    print("Step 4: Installing agent scripts...")
    install_agent()


    print(f"Installation completed successfully to {install_path}")
