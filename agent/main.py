
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)
sys.path.insert(0, current_dir)

from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit
import GenericClickAction
import UPgradeMission
import GenericRecognition
import DailyMission
import StageSelect
import HardSkip
import StorySelect
from UtilTools import UtilTools


def main():
    pipeline_path = os.path.join(os.path.dirname(current_dir), "assets", "resource", "pipeline", "图片.json")
    UtilTools.load_pipeline_nodes(pipeline_path)
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