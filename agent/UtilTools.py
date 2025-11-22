import json
from multiprocessing import process
import re
import time
from tokenize import Special
from GenericRecognition import GenericRecognition
from maa.context import Context
from collections import Counter, defaultdict

import GenericClickAction
class UtilTools:
    
    @staticmethod
    def get_image(context:Context):
        """
        获取当前屏幕截图
        Returns:
            屏幕截图图像
        """
        context.tasker.controller.post_screencap().wait()
        image = context.tasker.controller.cached_image
        return image

    @staticmethod
    def get_result(context: Context, image, target, fuzzy: bool = True ,pipeline:dict = None):
        """
        识别目标并返回识别结果
        Args:
            context: MAA上下文
            image: 输入图像
            target: 目标名称或坐标
            fuzzy: 是否启用模糊匹配
            pipeline: 识别管道配置
        Returns:
            识别结果字典
        """
        reco_result = GenericRecognition.analyze_target(context, image, target, fuzzy_match=fuzzy ,pipeline=pipeline)
        # 添加对reco_result为None的检查
        if reco_result is None:
            print(f"[工具] 识别目标 '{target}' 失败，返回结果为 None")
            return {
                "found": False,
                "roi": None,
                "filterd_results": [],
                "all_results": [],
                "best_result": {}
            }
        result = json.loads(reco_result.detail)
        return result

    @staticmethod
    def click_wait(context: Context, targets:list):
        """
        点击并等待下一个目标出现
        Args:
            context: MAA上下文
            targets: 目标列表，每个元素为目标名称或坐标
        Returns:
            是否成功点击并等待所有目标
        """
        for i, target in enumerate(targets):
                next_target = targets[i+1] if i+1 < len(targets) else None
                print(f" 尝试点击: {target}, 等待下一个: {next_target}")
                success = GenericClickAction.GenericClickAction.click_target(context, target, wait_for_next=next_target, timeout=5, interval=1)
                time.sleep(1)
                if not success:
                    print(f" 点击 {target} 或等待下一个目标失败")
                    retry_success = False
                    if target == "OK":
                        for j in range(3):
                            print(f"第 {j+1} 次重试点击 {target}")
                            if GenericClickAction.GenericClickAction.click_target(context, target):
                                retry_success = True
                                break
                            time.sleep(1)
                    if next_target == "略过" or next_target == "执行":
                        print("任务失败")
                        return False
                    
                    if not retry_success:
                        return False
        return True

    @staticmethod
    def group_and_sort_by_count(tuples_list):
        """
        将相同第一元的元素聚集在一起，并按照第一元数量排序
        
        Args:
            tuples_list: 包含二元组的列表
            
        Returns:
            按照第一元数量排序后的列表，相同第一元的元素聚集在一起
        """
        first_element_counts = Counter([item[0] for item in tuples_list])
        
        groups = defaultdict(list)
        for first, second in tuples_list:
            groups[first].append((first, second))
        sorted_groups = sorted(groups.items(), key=lambda x: (-len(x[1]), x[0]))
        result = []
        for first_element, group_items in sorted_groups:
            group_items.sort(key=lambda x: x[1])
            result.extend(group_items)
        
        return result
    @staticmethod
    def check_stage(context:Context,target:str):
        """
        检查当前场景是否为目标场景
        Args:
            context: MAA上下文
            image: 当前屏幕截图
            target: 目标场景名称
        Returns:
            是否为目标场景
        """
        import re
        
        image =UtilTools.get_image(context)
        result = UtilTools.get_result(context, image, "Enpty_OCR")
        Special_target =["机动战士高达","SEED"]
        for item in result["all_results"]:
            text = item["text"]
            processed_text = text.upper()
            if target in processed_text:
                if target in Special_target:
                    processed_text = processed_text.replace(" ", "")
                    processed_text = re.sub(r'HARDSTAGE', '', processed_text, flags=re.IGNORECASE)
                    processed_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z]', '', processed_text)
                    processed_text = re.sub(r'\d+', '', text)
                    remaining_text = processed_text.replace(target, "")
                    if target != "机动战士高达":
                        remaining_text = remaining_text.replace("机动战士高达", "")

                    return remaining_text.strip() == ""
                else:
                    return True
        return False
    @staticmethod
    def return_home(context:Context):
            """
            返回主界面
            Args:
                context: MAA上下文
            Returns:
                是否成功返回主界面
            """
            time.sleep(1)
            if GenericClickAction.GenericClickAction.click_target(context, "主画面", timeout=5):
                return True
            try:
                if GenericClickAction.GenericClickAction.click_target(context, "关闭", timeout=5):
                    return True
            except Exception as e:
                print(f"点击'关闭'时发生异常: {e}")
            try:
                return GenericClickAction.GenericClickAction.click_target(context, "返回", timeout=5)
            except Exception as e:
                print(f"返回主界面的所有尝试均失败: {e}")
                return False