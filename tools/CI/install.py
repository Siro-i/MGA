from pathlib import Path
import shutil
import sys
import json
import os
import subprocess
import platform


current_script_dir = Path(__file__).resolve().parent
project_root = current_script_dir.parent.parent
sys.path.append(str(current_script_dir))

try:
    from configure import configure_ocr_model
except ImportError:
    print("Warning: Could not import configure_ocr_model.")
    def configure_ocr_model(): pass

install_path = project_root / "install"
version = len(sys.argv) > 1 and sys.argv[1] or "v0.0.1"

def install_deps():
    """复制 MaaFramework 二进制到 install 目录"""
    deps_path = project_root / "deps"
    if not (deps_path / "bin").exists():
        print(f"Error: MaaFramework not found at {deps_path}. Please check download steps.")
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
        configure_ocr_model(project_root) 
    except Exception as e:
        print("configure_ocr_model() failed:", e)
    if (project_root / "assets" / "resource").exists():
        resource_src = project_root / "assets" / "resource"
    else:
        resource_src = project_root / "resource"

    shutil.copytree(
        resource_src,
        install_path / "resource",
        dirs_exist_ok=True,
    )
    interface_src = project_root / "interface.json"
    
    if not interface_src.exists():
        print(f"[Error] interface.json not found at {interface_src}")
        if (project_root / "assets" / "interface.json").exists():
            print("Found interface.json in assets folder, using that instead.")
            interface_src = project_root / "assets" / "interface.json"
        else:
            sys.exit(1) 

    print(f"Copying interface.json from {interface_src}...")
    shutil.copy2(interface_src, install_path)

    # 修改 interface.json
    json_path = install_path / "interface.json"
    with open(json_path, "r", encoding="utf-8") as f:
        interface = json.load(f)

    # 针对 Windows 使用内嵌 Python 路径
    if platform.system() == "Windows":
        print("[Config] Detecting Windows build: Pointing agent to embedded Python.")
        interface["agent"]["child_exec"] = "./python/python.exe"
    else:
        print("[Config] Detecting Non-Windows build: Using system python3.")
        interface["agent"]["child_exec"] = "python3"

    interface["version"] = version

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(interface, f, ensure_ascii=False, indent=4)

def install_chores():
    print("Copying docs...")
    for fname in ["README.md", "LICENSE"]:
        src = project_root / fname
        if src.exists():
            shutil.copy2(src, install_path)

def install_agent():
    print("Copying agent scripts...")
    shutil.copytree(
        project_root / "agent",
        install_path / "agent",
        dirs_exist_ok=True,
    )

if __name__ == "__main__":
    install_path.mkdir(exist_ok=True)
    print(f"Project Root: {project_root}")
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