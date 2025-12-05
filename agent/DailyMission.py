import time
from GenericClickAction import GenericClickAction
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from StageSelect import StageSelect
from UtilTools import UtilTools

@AgentServer.custom_action("每日任务")
class DailyMission(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        shop_targets = ['主画面', '商店', '高级', '免费', '购买', '关闭', '主画面'] 
        development_targets = ['开发', '0079', '终极', '地球联邦', '刚坦克', '全部开发', '执行开发', '执行', 'TAP TO NEXT', '返回', '主画面'] 
        base_targets = ['个人基地', '战舰巡航', '全部回收', 'OK', '主画面']  
        last_targets = ['主画面', '使命', '全部领取', 'OK', '主画面', '礼物', '全部领取', 'OK', '关闭']
        
        task_groups = [ 
            ("商店任务", shop_targets), 
            ("开发任务", development_targets), 
            ("基地任务", base_targets), 
            ("领取每日任务奖励并收取邮件", last_targets) 
        ]

        print("[每日任务] 开始执行每日任务流程")
        print("开始执行战斗任务")
        StageSelect.select_battle(context, Stagetarget="机动战士高达", Hardtarget="HARD1")
        StageSelect.hard_battle(context, Hardtarget="HARD2")

        failed_tasks = []

        for task_name, targets in task_groups:
            print(f"\n[每日任务] 正在处理 {task_name}: {targets}")
            task_success = True

            for i, target in enumerate(targets):
                next_target = targets[i + 1] if i + 1 < len(targets) else None
                print(f"[每日任务] 尝试点击: {target}, 等待下一个: {next_target}")
                if target == "主画面":
                    if UtilTools.return_home(context):
                        time.sleep(1)
                        continue
                    else:
                        print("[每日任务] return_home 尝试失败，降级为普通点击")
                if target == "免费":
                    image = UtilTools.get_image(context)
                    result_free = UtilTools.get_result(context, image, "免费")
                    if not result_free["found"]:
                        print("[每日任务] 未找到'免费'标签，判断为今日已领取，跳过购买")
                        continue 
                    result_buy = UtilTools.get_result(context, image, "购买")
                    all_buy = []
                    if result_buy["found"]:
                        all_buy = [item for item in result_buy.get("all_results", []) if "购买" in item.get("text", "")]
                    if not all_buy:
                        print("[每日任务] 异常：找到'免费'标签，但未找到任何'购买'按钮，任务中止")
                        task_success = False
                        break
                    free_box = result_free["roi"]
                    candidates = [item["box"] for item in all_buy]
                    
                    target_box = min(candidates, key=lambda b: abs(b[0] - free_box[0]))
                    print(f"[每日任务] 锁定距离'免费'最近的购买按钮 ROI={target_box}")
                    
                    GenericClickAction.click_roi(context, target_box)
                    time.sleep(1) 
                    continue  
                success = GenericClickAction.click_target(context, target, wait_for_next=next_target)
                time.sleep(0.5)
                
                if not success:
                    print(f"[每日任务] 点击 {target} 失败")
                    retry_success = False
                    for j in range(2):
                        if GenericClickAction.click_target(context, target):
                            retry_success = True
                            break
                        time.sleep(1)
                    
                    if not retry_success:
                        task_success = False
                        if target != targets[0]:
                           UtilTools.return_home(context)
                        break
            
                time.sleep(0.5)

            if task_success:
                print(f"[每日任务] {task_name} 执行成功")
            else:
                print(f"[每日任务] {task_name} 执行失败")
                failed_tasks.append(task_name)

            time.sleep(1)

        print("\n[每日任务] 所有任务流程执行完成")
        if failed_tasks:
            print("部分任务失败: " + ", ".join(failed_tasks))
        else:
            print("所有任务都执行成功!")

        return True