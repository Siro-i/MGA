import sys
import os
import subprocess

def find_python_executable():
    """智能查找Python可执行文件"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    embedded_python = os.path.join(project_root, "python", "python.exe")
    if os.path.exists(embedded_python):
        print(f"[MGA] Using embedded Python: {embedded_python}")
        return embedded_python
    system_python = sys.executable
    print(f"[MGA] Embedded Python not found, using system Python: {system_python}")
    return system_python

def main():
    """主函数"""
    python_exec = find_python_executable()
    main_script = os.path.join(os.path.dirname(__file__), "main.py")
    args = [python_exec, main_script] + sys.argv[1:]
    print(f"[MGA] Launching: {' '.join(args)}")
    sys.exit(subprocess.call(args))
if __name__ == "__main__":
    main()
