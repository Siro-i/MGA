from pathlib import Path
import shutil
import sys
import json
import os
import platform

script_dir = Path(__file__).resolve().parent
sys.path.append(str(script_dir))

try:
    from configure import configure_ocr_model
except ImportError:
    print("Warning: Could not import configure_ocr_model.")
    def configure_ocr_model(root): pass

working_dir = script_dir.parent.parent
install_path = working_dir / "install"
version = len(sys.argv) > 1 and sys.argv[1] or "v0.0.1"

def install_deps():
    """安装 MAA 核心库 (从 deps 目录)"""
    print("Installing MaaFramework dependencies...")
    deps_bin = working_dir / "deps" / "bin"
    
    if not deps_bin.exists():
        print(f"[Warning] Deps binary not found at {deps_bin}")
        return

    shutil.copytree(
        deps_bin,
        install_path,
        ignore=shutil.ignore_patterns(
            "*MaaDbgControlUnit*",
            "*MaaThriftControlUnit*",
            "*MaaRpc*",
            "*MaaHttp*",
        ),
        dirs_exist_ok=True,
    )
    
    # 复制 MaaAgentBinary (如果存在)
    agent_binary = working_dir / "deps" / "share" / "MaaAgentBinary"
    if agent_binary.exists():
        shutil.copytree(
            agent_binary,
            install_path / "MaaAgentBinary",
            dirs_exist_ok=True,
        )

def install_resource():
    """安装资源并配置 interface.json"""
    print("Installing resources and configuring interface...")
    
    # 1. 配置 OCR 模型
    try:
        configure_ocr_model(working_dir)
    except Exception as e:
        print(f"[Warning] configure_ocr_model failed: {e}")

    # 2. 复制资源文件夹
    resource_src = working_dir / "assets" / "resource"
    if not resource_src.exists():
        resource_src = working_dir / "resource" # 备选路径
    
    if resource_src.exists():
        target_resource_dir = install_path / "assets" / "resource"
        shutil.copytree(
            resource_src,
            target_resource_dir, 
            dirs_exist_ok=True,
        )

    # 3. 处理 interface.json
    # 优先使用 assets 下的，其次根目录下的
    interface_src = working_dir / "assets" / "interface.json"
    if not interface_src.exists():
        interface_src = working_dir / "interface.json"
    
    if interface_src.exists():
        shutil.copy2(interface_src, install_path)
        
        # 读取并修改
        json_path = install_path / "interface.json"
        with open(json_path, "r", encoding="utf-8") as f:
            interface = json.load(f)

        # === 修改配置 ===
        interface["version"] = version
        interface["custom_title"] = f"MGA {version}"
        interface["name"] = "MGA"
        interface["url"] = "https://github.com/283P/MGA"

        # === 自动设置 Agent 启动路径 ===
        # Windows 使用内嵌 Python，其他系统使用 python3
        if sys.platform.startswith("win"):
            interface["agent"]["child_exec"] = r"./python/python.exe"
        else:
            interface["agent"]["child_exec"] = "python3"
        
        # 确保启动参数正确
        # interface["agent"]["child_args"] = ["./agent/start_agent.py"] 

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(interface, f, ensure_ascii=False, indent=4)
            print("interface.json configured successfully.")

def install_chores():
    """复制杂项文件"""
    print("Copying docs...")
    for file in ["README.md", "LICENSE"]:
        src = working_dir / file
        if src.exists():
            shutil.copy2(src, install_path)

def install_agent():
    """复制 Agent 脚本"""
    print("Copying agent scripts...")
    agent_src = working_dir / "agent"
    if agent_src.exists():
        shutil.copytree(
            agent_src,
            install_path / "agent",
            dirs_exist_ok=True,
        )

if __name__ == "__main__":
    install_path.mkdir(parents=True, exist_ok=True)
    print(f"Installing to {install_path}")
    
    install_deps()
    install_resource()
    install_chores()
    install_agent()
    
    print("Installation script finished.")