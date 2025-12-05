import json
import time
from GenericClickAction import GenericClickAction
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from UtilTools import UtilTools
from StageSelect import StageSelect

@AgentServer.custom_action("故事选择")
class StorySelect(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            params = json.loads(argv.custom_action_param)
            Storytarget = params.get("story_target")
        except Exception:
            print("[故事选择] 参数解析失败")
            return False

        if not Storytarget:
            print("[故事选择] 未指定 story_target")
            return False

        if UtilTools.check_stage(context, Storytarget):
            print(f"[故事选择] 当前已在 {Storytarget} 界面")
            return True
            
        targets = ['主画面', '关卡', '主要关卡']
        
        if Storytarget in ["雷霆宙域", "异端"]:
            targets.append("历史关卡")
            if not UtilTools.click_wait(context, targets):
                return False
            image = UtilTools.get_image(context)
            if UtilTools.get_result(context, image, Storytarget, fuzzy=True)["found"]:
                GenericClickAction.click_target(context, target=Storytarget)
                time.sleep(0.6)
                GenericClickAction.click_target(context, target="前往关卡")
                time.sleep(1)
                GenericClickAction.click_target(context, target="故事关卡")
            else:
                print(f"[故事选择] 在历史关卡中未找到 {Storytarget}")
                return False
        else:
            if not UtilTools.click_wait(context, targets):
                return False
            StageSelect.select_story(context, way="right", target=Storytarget)
            
        time.sleep(0.6)
        return True