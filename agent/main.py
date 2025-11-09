#分发版本用:如果当前不是嵌入式 Python，就重新调用自己
import sys, os, subprocess
current_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.abspath(os.path.join(current_dir, "..", "python"))
embedded_python = os.path.join(python_dir, "python.exe")
sys.path.insert(0, current_dir)
os.chdir(current_dir)
if not os.path.samefile(sys.executable, embedded_python):
    print(f"[MGA] Relaunching with embedded Python: {embedded_python}")
    args = [embedded_python, os.path.abspath(__file__)] + sys.argv[1:]
    os.execv(embedded_python, args)
from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit
import GenericClickAction
import UPgradeMission
import GenericRecognition
import DailyMission
import StageSelect
import HardSkip
import StorySelect
def main():
    Toolkit.init_option("./")
    if len(sys.argv) < 2:
        print("Usage: python main.py <socket_id>")
        print("socket_id is provided by AgentIdentifier.")
        sys.exit(1)
        
    socket_id = sys.argv[-1]

    AgentServer.start_up(socket_id)
    AgentServer.join()
    AgentServer.shut_down()


if __name__ == "__main__":
    main()