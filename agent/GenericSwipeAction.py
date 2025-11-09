import time
import json
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from GenericRecognition import GenericRecognition
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
        """向左滑动重置"""
        for i in range(7):
            GenericSwipeAction.left_swipe(context)
    @staticmethod
    def right_reset(context: Context):
        """向右滑动重置"""
        for i in range(7):
            GenericSwipeAction.right_swipe(context)
    @staticmethod        
    def story_reset(context: Context):
        """向左滑动重置检测机动战士高达"""
        for i in range(7):
            image =UtilTools.get_image(context)
            if UtilTools.get_result(context,image,target="机动战士高达",fuzzy=True)["found"]:
                break
            GenericSwipeAction.left_swipe(context)
    @staticmethod
    def swipe_and_reco(context: Context, way: str, target: str , fuzzy: bool = False):
        """封装滑动操作并识别目标"""
    
        if way == "left":
            print("向左滑动")
            GenericSwipeAction.left_swipe(context)
        elif way == "right":
            print("向右滑动")
            GenericSwipeAction.right_swipe(context)
        elif way == "up":
            print("向上滑动")
            GenericSwipeAction.up_swipe(context)
        elif way == "down":
            print("向下滑动")
            GenericSwipeAction.down_swipe(context) 
        image = UtilTools.get_image(context)
        result = UtilTools.get_result(context, image, target, fuzzy)
        return result
        
    @staticmethod
    def stage_reset(context: Context):
        """向左滑动重置"""
        for i in range(7):
            image =UtilTools.get_image(context)
            if UtilTools.get_result(context,image,target="normal1",fuzzy=True)["found"]:
                break
            GenericSwipeAction.left_swipe(context)