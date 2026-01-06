from typing import final
from unittest import result
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from maa.define import Status

@AgentServer.custom_action("强制返回主页")
class ReturnHome(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        Strat_Node = "返回主画面入口"
        final_node = "结果检测"
        
        print(f"[返回主画面] 开始调度流水线: {Strat_Node}...")

        try:
            context.run_task(Strat_Node)
            final_result = context.run_task(final_node)
            if final_result !=  None :
                print("[返回主画面]  执行成功！")
                return True
            else:
                print(f"[返回主画面]  执行失败！")
                return False
        except Exception as e:
            print(f"[返回主画面]  Python 脚本执行异常: {e}")
            import traceback
            traceback.print_exc()
            return False