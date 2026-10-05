from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context


@AgentServer.custom_action("强制返回主页")
class ReturnHome(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            result = context.run_task("返回主画面入口")
            if result is None:
                print("MGA_TASK_FAILED: [返回主画面] 返回流程失败")
                return False
            return context.run_task("结果检测") is not None
        except Exception as exc:
            print(f"MGA_TASK_FAILED: [返回主画面] {exc}")
            return False
