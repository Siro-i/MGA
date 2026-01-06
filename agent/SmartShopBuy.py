import time
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

@AgentServer.custom_action("智能购买")
class SmartShopBuy(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            # 1. 截图与识别
            image = context.tasker.controller.post_screencap().wait().get()
            
            # 识别“免费”
            rec_free = context.run_recognition("Free_Tag_OCR", image, {
                "Free_Tag_OCR": {"recognition": "OCR", "expected": "免费"}
            })
            print(f"[智能购买] 免费标签: '{rec_free.best_result.text}'")
            # 识别“购买”
            rec_buy = context.run_recognition("Buy_Btn_OCR", image, {
                "Buy_Btn_OCR": {"recognition": "OCR", "expected": "购买"}
            })
            print(f"[智能购买] 购买按钮: '{rec_buy.filtered_results}'")

            # 如果没有结果，直接跳过
            if not rec_free or not rec_free.best_result or not rec_buy.all_results:
                print("[智能购买] 未发现关键元素，流程跳过")
                return False

            # 2. 获取“免费”标签中心坐标
            free_box = rec_free.best_result.box
            free_cx = free_box[0] + free_box[2] / 2
            free_cy = free_box[1] + free_box[3] / 2
            
            print(f"[智能购买] 免费标签中心: ({free_cx:.1f}, {free_cy:.1f})")

            # 3. 核心逻辑：筛选文本 + 寻找“左下方” + “距离最近”
            best_btn = None
            min_dist_sq = float('inf') 

            for btn in rec_buy.filtered_results:
                text = getattr(btn, "text","")
                if "购买" not in text:
                    continue

                # --- 坐标计算 ---
                btn_box = btn.box
                if btn_box[0] < free_cx and btn_box[1] > free_cy:
                    best_btn = btn.box
                    print(f"[智能购买] 检测到左下方的'购买'按钮: {btn}")

            # 4. 执行点击
            if best_btn:
                print(f"[智能购买] 锁定最佳目标: {best_btn}")
                context.tasker.controller.post_click(int(best_btn[0]), int(best_btn[1])).wait()
                time.sleep(0.6)
                return True
            else:
                print("[智能购买] 左下方未找到有效的'购买'按钮")

            return False

        except Exception as e:
            print(f"[智能购买] 异常: {e}")
            return False