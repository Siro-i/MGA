import time
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from UtilTools import UtilTools

class GenericSwipeAction(CustomAction):
    @staticmethod
    def left_swipe(context: Context, start_x: int = 150, start_y: int = 300, end_x: int = 620, end_y: int = 300, duration: float = 0.5):
        """封装向左滑动操作（整数 ms 时长）"""
        context.tasker.controller.post_swipe(start_x, start_y, end_x, end_y, int(duration * 1000)).wait()
        time.sleep(duration)

    @staticmethod
    def right_swipe(context: Context, start_x: int = 620, start_y: int = 300, end_x: int = 250, end_y: int = 300, duration: float = 0.5):
        """封装向右滑动操作（整数 ms 时长）"""
        context.tasker.controller.post_swipe(start_x, start_y, end_x, end_y, int(duration * 1000)).wait()
        time.sleep(duration)

    @staticmethod
    def up_swipe(context: Context, start_x: int = 400, start_y: int = 200, end_x: int = 400, end_y: int = 500, duration: float = 0.5):
        """封装向上滑动操作（整数 ms 时长）"""
        context.tasker.controller.post_swipe(start_x, start_y, end_x, end_y, int(duration * 1000)).wait()
        time.sleep(duration)

    @staticmethod
    def down_swipe(context: Context, start_x: int = 400, start_y: int = 500, end_x: int = 400, end_y: int = 200, duration: float = 0.5):
        """封装向下滑动操作（整数 ms 时长）"""
        context.tasker.controller.post_swipe(start_x, start_y, end_x, end_y, int(duration * 1000)).wait() 
        time.sleep(duration)

    @staticmethod
    def left_reset(context: Context):
        """向左滑动重置（通常用于回到列表最左边）"""
        for i in range(5): # 减少次数，通常5次够了
            GenericSwipeAction.left_swipe(context)
            
    @staticmethod
    def right_reset(context: Context):
        """向右滑动重置"""
        for i in range(5):
            GenericSwipeAction.right_swipe(context)

    @staticmethod        
    def story_reset(context: Context):
        """向左滑动直至检测到'机动战士高达'（用于列表复位）"""
        target_name = "机动战士高达"
        for i in range(7):
            image = UtilTools.get_image(context)
            if UtilTools.get_result(context, image, target=target_name, fuzzy=True)["found"]:
                print(f"[滑动重置] 已找到 {target_name}")
                break
            GenericSwipeAction.left_swipe(context)

    @staticmethod
    def stage_reset(context: Context):
        """向左滑动直至检测到 'normal1'"""
        target_name = "normal1" # OCR 会自动忽略大小写匹配 'NORMAL 1'
        for i in range(7):
            image = UtilTools.get_image(context)
            if UtilTools.get_result(context, image, target=target_name, fuzzy=True)["found"]:
                print(f"[滑动重置] 已找到 {target_name}")
                break
            GenericSwipeAction.left_swipe(context)

    @staticmethod
    def swipe_and_reco(context: Context, way: str, target: str , fuzzy: bool = False):
        """封装滑动操作并识别目标"""
        if way == "left":
            # print("向左滑动")
            GenericSwipeAction.left_swipe(context)
        elif way == "right":
            # print("向右滑动")
            GenericSwipeAction.right_swipe(context)
        elif way == "up":
            # print("向上滑动")
            GenericSwipeAction.up_swipe(context)
        elif way == "down":
            # print("向下滑动")
            GenericSwipeAction.down_swipe(context) 
            
        time.sleep(0.5) # 滑动后稍作等待再截图
        image = UtilTools.get_image(context)
        result = UtilTools.get_result(context, image, target, fuzzy)
        
        if result["found"]:
            print(f"[滑动识别] 滑动后找到目标: {target}")
            
        return result