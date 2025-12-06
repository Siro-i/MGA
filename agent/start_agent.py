import sys
import os
import subprocess

# === 第一部分：环境引导与自举逻辑 ===

def find_python_executable():
    """查找最佳 Python 解释器（优先嵌入式）"""
    # 假设当前脚本在 agent/ 目录下，向上两级找到项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) 
    
    embedded_python = os.path.join(project_root, "python", "python.exe")
    
    if os.path.exists(embedded_python):
        # 简单检查：如果当前运行的已经是嵌入式 Python，则不需要切换
        # 注意：Windows下路径可能大小写不一致，建议规范化比较
        try:
            if os.path.samefile(sys.executable, embedded_python):
                return None  # 已经是正确环境，返回 None 表示无需重启
        except Exception:
            # 如果 samefile 报错（极少见），则简单比较字符串
            if os.path.normcase(os.path.abspath(sys.executable)) == os.path.normcase(os.path.abspath(embedded_python)):
                return None
                
        print(f"[MGA] Found embedded Python: {embedded_python}")
        return embedded_python
        
    print(f"[MGA] Embedded Python not found. Continuing with system Python: {sys.executable}")
    return None # 使用当前环境，无需重启

# === 第二部分：核心业务逻辑 (原 main.py) ===

def run_agent_logic(socket_id):
    """实际的 Agent 运行逻辑"""
    print(f"[MGA] Starting Agent Logic with Socket ID: {socket_id}")
    
    # 1. 设置工作目录和导入路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir) # 确保工作目录在 agent/ 下
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    # 2. 延迟导入 MAA 库
    # 为什么要延迟导入？因为如果当前是系统 Python 且没装库，
    # 在第一部分自举完成前导入会导致 crash。
    try:
        from maa.agent.agent_server import AgentServer
        from maa.toolkit import Toolkit
        from UtilTools import UtilTools
        
        # 导入自定义 Action (确保这些文件都在 agent/ 目录下)
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
    # 计算 assets/resource/pipeline/图片.json 的路径
    # current_dir 是 agent/，上一级是根目录
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

# === 主入口 ===

def main():
    # 1. 获取命令行参数中的 socket_id
    # interface.json 调用时通常是: python start_agent.py <socket_id>
    if len(sys.argv) < 2:
        print("Usage: python start_agent.py <socket_id>")
        # 为了调试方便，如果没有传参，可以不退出，或者给个默认值（视情况而定）
        # 这里保持严格模式
        sys.exit(1)
        
    socket_id = sys.argv[-1] # 获取最后一个参数作为 socket_id

    # 2. 检查环境并决定是否重启
    target_python = find_python_executable()
    
    if target_python:
        # 如果找到了更好的 Python 环境（嵌入式），则作为子进程重新启动自己
        print(f"[MGA] Relaunching script with embedded Python...")
        
        # 构建命令: [新Python路径, 当前脚本路径, 参数...]
        args = [target_python, __file__] + sys.argv[1:]
        
        # 替换当前进程或启动子进程
        # 使用 subprocess.call 保持父进程等待子进程结束
        ret_code = subprocess.call(args)
        sys.exit(ret_code)
    else:
        # 如果当前就是正确环境，直接运行逻辑
        run_agent_logic(socket_id)

if __name__ == "__main__":
    main()