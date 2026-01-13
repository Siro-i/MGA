from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer

@AgentServer.custom_action("DailyBattle")
class DailyBattle(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        print("启动日常战斗")
        context.run_task("战斗入口")
        print("完成第一次战斗")
        context.run_task("战斗入口",pipeline_override={
                    
                        "关卡匹配": {
                        "action": {
                        "param": {
                            "custom_action": "StageSelect",
                            "custom_action_param": {
                            "stage_target": "HARD1"
                            }
                        },
                        "type": "Custom"
                        }
                        }
        }
                    
                    
                )
        print("完成第二次战斗")