import time
from maa.context import Context
from maa.define import RectType

@staticmethod
def click_roi(context:Context,roi) -> bool:
        """点击指定ROI"""
        x, y, w, h = roi
        click_x, click_y = x + w // 2, y + h // 2
        context.tasker.controller.post_click(click_x, click_y).wait()
        time.sleep(0.6)
        return True
@staticmethod
def get_image(context: Context):
        """获取截图"""
        context.tasker.controller.post_screencap().wait()
        return context.tasker.controller.cached_image
@staticmethod
def get_result(context: Context, image, target):
        """
        识别节点
        """
        from GenericRecognition import GenericRecognition

        result_obj = GenericRecognition.analyze_target(
            context, image, target, 
        )

        result_dict = result_obj.to_dict()

        result_dict["all_results"] = []
        if result_obj.details:
            raw_all = getattr(result_obj.details, "all_results", [])
            result_dict["all_results"] = [
                {
                    "text": getattr(i, "text", ""), 
                    "box": getattr(i, "box", (0,0,0,0)), 
                    "score": getattr(i, "score", 0)
                } 
                for i in raw_all
            ]
            
        return result_dict
