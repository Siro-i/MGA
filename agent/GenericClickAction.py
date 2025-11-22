from email.mime import image
from sre_constants import SUCCESS
import time
import json
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from GenericRecognition import GenericRecognition
from UtilTools import UtilTools


@AgentServer.custom_action("通用点击动作")
class GenericClickAction(CustomAction):
    """
    通用点击模块。
    使用 GenericRecognition 进行目标检测，可选等待后续目标出现。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """入口：框架自动调用"""

        return self.click_target(context,target="关卡"
        )

    @staticmethod
    def click_target(context: Context, target: str,
                     wait_for_next: str = None,
                     fuzzy: bool = False,
                     timeout: float = 5,
                     interval: float = 1,
                     roi=None) -> bool:
        """
        点击指定目标。
        如果指定 wait_for_next，则点击后等待下一个目标出现,默认等待时间为3s,间隔1s。
        """
        print(f"[通用点击动作] 调用识别模块：target='{target}', fuzzy={fuzzy}")
        image =UtilTools.get_image(context)
        result =UtilTools.get_result(context, image, target, fuzzy)
        if not result["found"] :
            print(f"[通用点击动作] 未检测到目标: '{target}'")
            return False

        roi = result["roi"]
        success = GenericClickAction.click_via_roi(context, target, roi)
        if target == "主画面":
            is_home = GenericClickAction.Check_home(context, target, roi)
            if is_home:
                print(f"[通用点击动作] 已返回主画面")
                return True
            else:
                print(f"[通用点击动作] 未返回主画面")
                UtilTools.return_home(context)

        if success and wait_for_next:
            return GenericClickAction._wait_for_next(
                context, wait_for_next, timeout, interval, fuzzy=fuzzy
            )

        return success
    @staticmethod
    def click_roi(context:Context,roi) -> bool:
        """点击指定ROI"""
        x, y, w, h = roi
        click_x, click_y = x + w // 2, y + h // 2
        context.tasker.controller.post_click(click_x, click_y).wait()
        time.sleep(0.6)
        return True

    @staticmethod
    def click_via_roi(context: Context, target, roi):
        """执行点击"""
        x, y, w, h = roi
        click_x, click_y = x + w // 2, y + h // 2
        print(f"[通用点击动作] 点击目标 '{target}' → 坐标({click_x}, {click_y})")
        context.tasker.controller.post_click(click_x, click_y).wait()
        time.sleep(0.6)
        return True

    @staticmethod
    def _wait_for_next(context: Context, wait_target, timeout,  interval,  fuzzy=False):
        """等待下一个目标出现"""
        print(f"[通用点击动作] 等待下一个目标 '{wait_target}'，最长 {timeout}s")
        start_time = time.time()

        while time.time() - start_time < timeout:
            image =UtilTools.get_image(context)
            result =UtilTools.get_result(context, image, wait_target, fuzzy)

            if result["found"]:
                print(f"[通用点击动作] 下一个目标 '{wait_target}' 已出现 ")
                return True

            time.sleep(interval)

        print(f"[通用点击动作] 等待超时  '{wait_target}' 未出现")
        return False
    @staticmethod
    def Check_home(context: Context, target, roi):
        """检查是否返回主界面"""
        if target == "主画面":
           image=UtilTools.get_image(context)
           success = UtilTools.get_result(context, image, target)["found"]
        return success
