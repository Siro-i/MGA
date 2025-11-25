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
            targets=['主画面','关卡','主要关卡']
            if Storytarget in ["雷霆宙域","异端"]:
                targets.append("历史关卡")
                UtilTools.click_wait(context,targets)
                image=UtilTools.get_image(context)
                Result=UtilTools.get_result(context,image,Storytarget,fuzzy=True)
                GenericClickAction.click_target(context,target=Storytarget)
                time.sleep(0.6)
                GenericClickAction.click_target(context,target="前往关卡")
                time.sleep(1)
                GenericClickAction.click_target(context,target="故事关卡")
            else:
                UtilTools.click_wait(context,targets)
                StageSelect.select_story(context,way="left",Storytarget=Storytarget)
            time.sleep(0.6)
            return True

