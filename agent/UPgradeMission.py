import json
import time
from GenericClickAction import GenericClickAction
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from UtilTools import UtilTools

@AgentServer.custom_action("养成培育材料")
class UPgradeMission(CustomAction):
   def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        target1 = ['主画面', '关卡', '强化培育关卡', 'CAPITAL', '略过', '执行', 'OK']
        target2 = ['返回', '单位培育', '略过', '执行', 'OK']
        target3 = ['返回', '角色培育', '略过', '执行', 'OK']
        target4 = ['返回', '支援人员培育', '略过', '执行', 'OK']
        
        task_groups = [
            ("强化培育关卡", target1),
            ("单位培育", target2),
            ("角色培育", target3),
            ("支援人员培育", target4)
        ]
        
        print("[每日任务] 开始执行每日任务流程")
        
        task_successes = {}

        for task_name, targets in task_groups:
            print(f"[每日任务] 正在处理 {task_name}: {targets}")
            task_success = UtilTools.click_wait(context, targets)
            task_successes[task_name] = task_success
            
            if task_success:
                print(f"[每日任务] {task_name} 执行成功")
            else:
                print(f"[每日任务] {task_name} 执行失败，跳过到下一个任务组")
            
            time.sleep(1)

        print("[每日任务] 所有任务流程执行完成")
        
        failed_tasks = [task_name for task_name, success in task_successes.items() if not success]
        
        if failed_tasks:
            print("部分任务失败,具体失败任务为:")
            for task_name in failed_tasks:
                print(f"{task_name}")
        else:
            print("所有任务都执行成功!")
            
        return True