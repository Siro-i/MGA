from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer
import json
@AgentServer.custom_action("GP")
class GP(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        params = json.loads(argv.custom_action_param)
        target = float(params.get("GP_target"))
        print("[GP] GP_target:",target)
        input = context.tasker.get_latest_node("GP识别")
        result=input.recognition.best_result
        text=result.text.replace(",","")
        GP=float(text)
        if GP <= target:
            print("[GP] GP:",GP,"小于目标值:",target)
            return True
        else:
            print("[GP] GP:",GP,"大于目标值:",target)
            return False
