# 分发版本用: 强制使用嵌入式 Python，无论启动方式
import sys, os, subprocess

current_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.abspath(os.path.join(current_dir, "..", "python"))
embedded_python = os.path.join(python_dir, "python.exe")

# 强制让 PATH 优先使用内嵌 python
os.environ["PATH"] = python_dir + os.pathsep + os.environ.get("PATH", "")

# 如果当前不是嵌入式 Python，就重启自己
if not os.path.exists(embedded_python):
    print("[MGA] Embedded Python not found, exiting.")
    sys.exit(1)

# 判断是否为系统 Python
if not os.path.samefile(sys.executable, embedded_python):
    print(f"[MGA] Relaunching with embedded Python: {embedded_python}")
    args = [embedded_python, os.path.abspath(__file__)] + sys.argv[1:]
    os.execv(embedded_python, args)

# 修正工作目录
os.chdir(current_dir)
sys.path.insert(0, current_dir)

from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit
from agent import GenericClickAction
from agent import UPgradeMission
from agent import GenericRecognition
from agent import DailyMission
from agent import StageSelect
from agent import HardSkip
from agent import StorySelect


def main():
    Toolkit.init_option("./")
    if len(sys.argv) < 2:
        print("Usage: python main.py <socket_id>")
        sys.exit(1)
        
    socket_id = sys.argv[-1]
    AgentServer.start_up(socket_id)
    AgentServer.join()
    AgentServer.shut_down()


if __name__ == "__main__":
    main()
