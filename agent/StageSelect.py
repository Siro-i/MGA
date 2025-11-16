import json
import time
from GenericClickAction import GenericClickAction
from GenericRecognition import GenericRecognition
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from UtilTools import UtilTools
from GenericSwipeAction import GenericSwipeAction

@AgentServer.custom_action("战斗关卡选择")
class StageSelect(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        Hardtarget =json.loads(argv.custom_action_param)["stage_target"]
        StageSelect.hard_battle(context,Hardtarget)
    @staticmethod
    def select_hardstage(context: Context, target: str) -> bool:
        """选择HARD关卡"""
        isfound=False
        GenericSwipeAction.right_reset(context)
        for i in range(8):
            image =UtilTools.get_image(context)
            result=UtilTools.get_result(context,image,target,fuzzy=True)
            print("是否找到HARD关卡:",result["found"])
            if result["found"]:
                GenericClickAction.click_target(context,target=target)
                selection_result = list(result["all_results"])
                tried_items = []
                while selection_result:
                    item = selection_result.pop(0) 
                    tried_items.append(item) 
                    print("当前备选:",item["box"])
                    GenericClickAction.click_roi(context,item["box"])
                    time.sleep(0.6)
                    image=UtilTools.get_image(context)
                    result=UtilTools.get_result(context,image,target=target + "_OCR",fuzzy=True)
                    if result["found"]:
                        print("匹配成功:",item)
                        isfound=True
                        return isfound
                    else:
                        print("匹配失败:",item)
                
                print("当前屏幕所有选项都已尝试，未找到匹配项，向左滑动")
                GenericSwipeAction.left_swipe(context,start_x=150,end_x=320)
                
            else:
                print("当前屏幕未找到目标，向左滑动")
                GenericSwipeAction.left_swipe(context)
                
        return isfound
    @staticmethod
    def select_story(context: Context, way: str, target: str) -> bool:
        """选择主线"""
        isfound=False
        GenericSwipeAction.story_reset(context)
        for i in range(7):
            if "机动战士高达" == target:
                GenericClickAction.click_target(context,target)
                result={"found":True}
            else :
                result=GenericSwipeAction.swipe_and_reco(context,way,target)
            if result["found"]:
                GenericClickAction.click_target(context,target)
                GenericClickAction.click_target(context,target="选择")
                isfound=True
                return isfound
        time.sleep(0.6)
        return isfound
    
    @staticmethod
    def select(context: Context,Stagetarget: str,Hardtarget: str, way: str = "right", ) -> bool:
        """选择主线和HARD关卡"""
        targets=['主画面','关卡','主要关卡']
        UtilTools.click_wait(context,targets)
        StageSelect.select_story(context,way,Stagetarget)
        time.sleep(0.6)
        StageSelect.select_hardstage(context,Hardtarget)

    @staticmethod
    def select_battle(context: Context,Stagetarget: str,Hardtarget: str, way: str = "right", ) -> bool:
        """选择并进行战斗"""
        StageSelect.select(context,Stagetarget,Hardtarget,way)
        time.sleep(0.6)
        targets=['略过','执行','OK']
        UtilTools.click_wait(context,targets)
        time.sleep(0.5)
    
    @staticmethod
    def hard_battle(context: Context,Hardtarget: str ) -> bool:
        """选择并进行HARD战斗"""
        StageSelect.select_hardstage(context,Hardtarget)
        time.sleep(0.6)
        targets=['略过','执行','OK']
        UtilTools.click_wait(context,targets)
        time.sleep(0.5)