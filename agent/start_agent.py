import sys
import os
import subprocess

def find_python_executable():
    """查找最佳 Python 解释器（优先嵌入式）"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) 
    
    embedded_python = os.path.join(project_root, "python", "python.exe")
    
    if os.path.exists(embedded_python):
        try:
            if os.path.samefile(sys.executable, embedded_python):
                return None 
        except Exception:
            if os.path.normcase(os.path.abspath(sys.executable)) == os.path.normcase(os.path.abspath(embedded_python)):
                return None
                
        print(f"[MGA] Found embedded Python: {embedded_python}")
        return embedded_python
        
    print(f"[MGA] Embedded Python not found. Continuing with system Python: {sys.executable}")
    return None 


def run_agent_logic(socket_id):
    """实际的 Agent 运行逻辑"""
    print(f"[MGA] Starting Agent Logic with Socket ID: {socket_id}")
    
    # 1. 设置工作目录和导入路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir) # 确保工作目录在 agent/ 下
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    # 2. 延迟导入 MAA 库
    try:
        from maa.agent.agent_server import AgentServer
        from maa.toolkit import Toolkit
        from UtilTools import UtilTools
        import GenericClickAction
        import UPgradeMission
        import GenericRecognition
        import DailyMission
        import StageSelect
        import HardSkip
        import StorySelect
        
    except ImportError as e:
        print(f"[MGA Error] Failed to import dependencies: {e}")
        print("[MGA Hint] This usually happens if dependencies are not installed in the current Python environment.")
        sys.exit(1)

    # 3. 加载 Pipeline 和初始化
    project_root = os.path.dirname(current_dir)
    pipeline_path = os.path.join(project_root, "assets", "resource", "pipeline", "图片.json")
    
    print(f"[MGA] Loading pipeline from: {pipeline_path}")
    if not os.path.exists(pipeline_path):
        print(f"[MGA Warning] Pipeline file not found at {pipeline_path}")
    
    UtilTools.load_pipeline_nodes(pipeline_path)
    Toolkit.init_option("./")

    # 4. 启动服务
    AgentServer.start_up(socket_id)
    print("[MGA] Agent Server started, waiting for commands...")
    AgentServer.join()
    AgentServer.shut_down()



def main():
    # 1. 获取命令行参数中的 socket_id
    if len(sys.argv) < 2:
        print("Usage: python start_agent.py <socket_id>")
        sys.exit(1)
        
    socket_id = sys.argv[-1] # 获取最后一个参数作为 socket_id

    # 2. 检查环境并决定是否重启
    target_python = find_python_executable()
    
    if target_python:
        # 如果找到了更好的 Python 环境（嵌入式），则作为子进程重新启动自己
        print(f"[MGA] Relaunching script with embedded Python...")
        args = [target_python, __file__] + sys.argv[1:]
        ret_code = subprocess.call(args)
        sys.exit(ret_code)
    else:
        # 如果当前就是正确环境，直接运行逻辑
        run_agent_logic(socket_id)

if __name__ == "__main__":
    main()