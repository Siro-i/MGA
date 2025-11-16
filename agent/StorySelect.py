import json
import sys
import time
from GenericClickAction import GenericClickAction
from GenericRecognition import GenericRecognition
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from UtilTools import UtilTools
from GenericSwipeAction import GenericSwipeAction
from StageSelect import StageSelect

@AgentServer.custom_action("故事选择")
class StorySelect(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        Storytarget =json.loads(argv.custom_action_param)["story_target"]
        if UtilTools.check_stage(context,Storytarget):
            print(f"[故事选择] 已选择{Storytarget}")
            return True
        else:
            print(f"[故事选择] 未选择{Storytarget}")
            targets = ['主画面','关卡','主要关卡']
            UtilTools.click_wait(context,targets)
            StageSelect.select_story(context,"right",Storytarget)
            return True

