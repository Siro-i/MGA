import time
from GenericClickAction import GenericClickAction
from GenericRecognition import GenericRecognition
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from GenericSwipeAction import GenericSwipeAction
from StageSelect import StageSelect
from UtilTools import UtilTools

@AgentServer.custom_action("每日任务")
class DailyMission(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        shop_targets = ['主画面','商店','高级','免费','购买按钮','关闭','主画面'] 
        development_targets = ['开发','0079','终极','地球联邦','刚坦克','全部开发','执行开发','执行','TAP TO NEXT','返回','主画面'] 
        base_targets = ['个人基地','战舰巡航','全部回收','OK','主画面']  
        last_targets = ['主画面','使命','全部领取','OK','主画面','礼物','全部领取','OK','关闭']
        task_groups = [ ("商店任务", shop_targets), 
        ("开发任务", development_targets), 
        ("基地任务", base_targets), 
        ("领取每日任务奖励并收取邮件", last_targets) 
        ]
        

        print("[每日任务] 开始执行每日任务流程")
        print("开始执行战斗任务")
        StageSelect.select_battle(context,Stagetarget="机动战士高达",Hardtarget="HARD1")
        StageSelect.hard_battle(context,Hardtarget="HARD2")

        failed_tasks = []

        for task_name, targets in task_groups:
            print(f"\n[每日任务] 正在处理 {task_name}: {targets}")
            task_success = True

            for i, target in enumerate(targets):
                next_target = targets[i + 1] if i + 1 < len(targets) else None
                print(f"[每日任务] 尝试点击: {target}, 等待下一个: {next_target}")

                if target == "免费":
                    image = UtilTools.get_image(context)
                    result_free = UtilTools.get_result(context, image, "免费")
                    result_buy = UtilTools.get_result(context, image, "购买")
                    found_free = result_free["found"]
                    found_buy = False
                    all_buy = []
                    try:
                        found_buy = result_buy["found"]
                        print(f"[每日任务] 免费识别结果: {found_free}")
                        print(f"[每日任务] 购买识别结果: {found_buy}")
                    except Exception as e:
                        print(f"[每日任务] 解析购买识别结果失败: {e}")

                    if not found_free or not found_buy :
                        print("[每日任务] 免费购买条件未满足，直接结束此任务组")
                        task_success = False
                        break
                    for item in result_buy["filterd_results"]:
                        all_buy.append(item)
                        print(f"[每日任务] 购买按钮识别结果: {item}")

                    free_box = result_free["roi"]
                    candidates = [item["box"] for item in all_buy ]
                    target_box = min(candidates, key=lambda b:abs(b[0] - free_box[0]))
                    print(f"[每日任务] 点击购买按钮 ROI={target_box}")
                    GenericClickAction.click_roi(context, target_box)
                    continue  
                success = GenericClickAction.click_target(context, target, wait_for_next=next_target)
                time.sleep(0.5)
                if not success:
                    print(f"[每日任务] {task_name} - 点击 {target} 或等待下一个目标失败")
                    retry_success = False
                    for j in range(3):
                        print(f"[每日任务] 第 {j+1} 次重试点击 {target}")
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
            print("部分任务失败, 具体失败任务为:")
            for t in failed_tasks:
                print(f"- {t}")
        else:
            print("所有任务都执行成功!")

        return True
