from pathlib import Path
import shutil
import sys
import json
import os
import subprocess
import platform

# === 路径修正逻辑 ===
current_script_dir = Path(__file__).resolve().parent
project_root = current_script_dir.parent.parent
sys.path.append(str(current_script_dir))

try:
    from configure import configure_ocr_model
except ImportError:
    print("Warning: Could not import configure_ocr_model.")
    def configure_ocr_model(root): pass

install_path = project_root / "install"
# 获取 tag 版本号，如果没有传参则默认为 v0.0.1
version = len(sys.argv) > 1 and sys.argv[1] or "v0.0.1"

def install_deps():
    """复制 MaaFramework 二进制到 install 目录"""
    deps_path = project_root / "deps"
    if not (deps_path / "bin").exists():
        print(f"Error: MaaFramework not found at {deps_path}.")
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
    """复制资源文件并配置 OCR，同时修改 interface.json"""
    print("Installing resources...")
    try:
        configure_ocr_model(project_root) 
    except Exception as e:
        print("configure_ocr_model() failed:", e)

    # 复制 resource 文件夹
    if (project_root / "assets" / "resource").exists():
        resource_src = project_root / "assets" / "resource"
    else:
        resource_src = project_root / "resource"

    shutil.copytree(
        resource_src,
        install_path / "resource",
        dirs_exist_ok=True,
    )

    # === 处理 interface.json ===
    # 优先找根目录，其次找 assets 目录
    interface_src = project_root / "interface.json"
    if not interface_src.exists():
        if (project_root / "assets" / "interface.json").exists():
            interface_src = project_root / "assets" / "interface.json"
        else:
            print(f"[Error] interface.json not found!")
            sys.exit(1)

    print(f"Processing interface.json from {interface_src}...")
    
    # 读取原始 JSON
    with open(interface_src, "r", encoding="utf-8") as f:
        interface = json.load(f)

    # === [核心修复] 在 Python 中直接修改字段，替代不稳定的 jq ===
    
    # 1. 设置版本信息
    interface["version"] = version
    
    # 2. 设置 MGA 更新所需的字段 (仅 Windows 或全部写入，多写通常无害)
    # 如果你只希望 Windows 版有这些字段，可以加 if platform.system() == "Windows":
    interface["name"] = "MGA"
    interface["url"] = "https://github.com/283P/MGA"

    # 3. 设置 agent 启动路径
    if platform.system() == "Windows":
        print("[Config] Windows: Pointing agent to embedded Python.")
        # 使用正斜杠 / 在 JSON 中是合法的，且避免了转义问题
        interface["agent"]["child_exec"] = "./python/python.exe"
    else:
        print("[Config] Non-Windows: Using system python3.")
        interface["agent"]["child_exec"] = "python3"

    # 4. 写入文件 (ensure_ascii=False 防止中文乱码)
    json_path = install_path / "interface.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(interface, f, ensure_ascii=False, indent=4)
        print(f"interface.json saved successfully.")

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

    install_deps()
    install_resource()
    install_chores()
    install_agent()

    print(f"Installation completed successfully.")