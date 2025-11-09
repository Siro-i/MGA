import json
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context
import re

@AgentServer.custom_recognition("通用识别动作")
class GenericRecognition(CustomRecognition):
    """通用识别模块，可独立调用。支持 OCR、模板匹配、特征匹配。"""

    def analyze(self, context: Context, argv: CustomRecognition.AnalyzeArg) -> CustomRecognition.AnalyzeResult:
        return self.analyze_target(context, argv.image, "关卡", fuzzy_match = True )

    @staticmethod
    def analyze_target(context: Context, image, target: str, fuzzy_match: bool = True ,pipeline:dict = None):
        roi = None
        all_results = []
        filterd_results = []
        best_result = None
        node_data = context.get_node_data(target)
        if not node_data:
            print(f"[通用识别动作] 未找到节点数据: '{target}'")
            return GenericRecognition._make_result(False, roi, filterd_results, all_results,best_result)

        recognition = node_data.get("recognition")
        if not recognition:
            print(f"[通用识别动作] 节点 '{target}' 缺少 recognition 字段")
            return GenericRecognition._make_result(False, roi, filterd_results, all_results,best_result)

        node_type = recognition.get("type")
        print(f"[通用识别动作] 识别节点 '{target}' 类型: {node_type}")
        if pipeline is None:

            reco_detail = context.run_recognition(target, image)
        else:
            reco_detail = context.run_recognition(target, image, pipeline)

        if not reco_detail:
            return GenericRecognition._make_result(False, roi, filterd_results, all_results,best_result)

        found, roi, best_result,filterd_results, all_results = GenericRecognition._extract_detail(reco_detail)

        # ---------- OCR ----------
        if node_type == "OCR":
            target_upper = target.replace(" ", "").upper()
            
            found_item = None
            for item in all_results:
                text = getattr(item, "text", "") or ""
                text_upper = text.replace(" ", "").upper()
                
                if not text_upper:
                    continue
                
                if fuzzy_match:
                    if target_upper == text_upper:
                        found_item = item
                        break
                    elif target_upper in text_upper:
                        found_item = item
                        break
                else:
                    if target_upper == text_upper:
                        found_item = item
                        break
            if found : 
                return GenericRecognition._make_result(True, roi, filterd_results, all_results,best_result)


            if found_item:
                print(f"[OCR匹配成功] {found_item}")
                return GenericRecognition._make_result(True, roi, filterd_results, all_results,best_result)
            else:
                print(f"[OCR匹配失败] 未找到匹配项: '{target}'")

        if node_type in ["TemplateMatch", "FeatureMatch"] :
            if best_result:
                return GenericRecognition._make_result(True, roi, filterd_results, all_results,best_result)
            else:
                print(f"[通用识别动作] '{target}' 无匹配结果")
                return GenericRecognition._make_result(False, None, filterd_results, all_results,best_result)

    @staticmethod
    def _extract_detail(reco_detail):
        """从 reco_detail 中提取 OCR 结果列表。"""
        all_results = []
        filterd_results = []
        best_result = []
        roi = None
        found = False
        try:
            all_results =getattr(reco_detail, "all_results", [])
            filterd_results =getattr(reco_detail, "filterd_results", [])
            best_result = getattr(reco_detail, "best_result", [])
            box = getattr(reco_detail, "box", (0,0,0,0))
            roi = list(box)
            if roi != (0,0,0,0):
                found = True
        except Exception as e:
            print(f"[通用识别动作] detail解析失败: {e}")
        return found, roi, best_result, filterd_results, all_results
                
    @staticmethod
    def _make_result(found, roi, filterd_results, all_results,best_result):
        def serialize(item):
                
                return {
                    "text": getattr(item, "text", ""),
                    "score": getattr(item, "score", ""),
                    "box": getattr(item, "box", None)
                }
        detail = {
            "found": found,
            "roi": roi,
            "filterd_results": [serialize(i) for i in (filterd_results or [])],
            "all_results": [serialize(i) for i in (all_results or [])],
            "best_result": serialize(best_result) if best_result else {}
        }
        return CustomRecognition.AnalyzeResult(
            box=tuple(roi) if roi else (0, 0, 0, 0),
            detail=json.dumps(detail, ensure_ascii=False)
        )