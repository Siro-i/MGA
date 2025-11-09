import time
import json
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from StageSelect import StageSelect
from GenericRecognition import GenericRecognition
from UtilTools import UtilTools

@AgentServer.custom_action("困难关卡自动扫荡")
class HardSkip(CustomAction):
    def run(self, context: Context, argv:CustomAction.RunArg) -> bool:
        # targets=[
        #     ("w_主线", "HARD3"), 
        #     ("铁血_主线", "HARD2"), 
        #     ("铁血_主线", "HARD4"),
        #     ("w_主线","HARD1"),
        #     ("种_主线", "HARD1"),
        #     ("铁血_主线","HARD1")
        # ]

        if "target" in argv.custom_action_param:
            targets=json.loads(argv.custom_action_param)["target"]
            HardSkip.process_targets(context, targets)
        return True

    @staticmethod
    def process_targets(context, targets):
        """
        处理targets，根据当前组的第一元与上一组是否相同执行不同逻辑
        """
        result = UtilTools.group_and_sort_by_count(targets)
        print(result)
        result_list = list(result)
        for i in range(len(result_list)):
            current_item = result_list[i]
            if i > 0:
                previous_item = result_list[i - 1]
                if current_item[0] == previous_item[0]:
                    print(f"处理与上一组第一元相同的元素: {current_item}")
                    StageSelect.hard_battle(context, current_item[1])
                else:
                    print(f"处理与上一组第一元不同的元素: {current_item}")
                    StageSelect.select_battle(context, current_item[0], current_item[1])
            else:
                print(f"处理第一组元素: {current_item}")
                StageSelect.select_battle(context, current_item[0], current_item[1])