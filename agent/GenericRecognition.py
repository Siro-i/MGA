import json
import difflib
import re
from typing import Tuple, Any
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context

class RecognitionResult:
    def __init__(self, found: bool, box: Tuple[int, int, int, int], text: str = "", score: float = 0.0, details: Any = None,filtered_results: list = None):
        self.found = found
        self.box = box if box is not None else (0, 0, 0, 0)
        self.text = text
        self.score = score
        self.details = details
        self.filtered_results = filtered_results if filtered_results is not None else []

    def to_dict(self):
        data = {
            "found": self.found,
            "roi": list(self.box),
            "text": self.text,
            "score": self.score,
        }
        if self.filtered_results:
            data["all_results"] = [
                {
                    "text": getattr(item, "text", ""), 
                    "box": getattr(item, "box", (0,0,0,0)), 
                    "score": getattr(item, "score", 0.0)
                } 
                for item in self.filtered_results
            ]
        else:
            raw_all = getattr(self.details, "all_results", []) or []
            data["all_results"] = [
                {
                    "text": getattr(i, "text", ""), 
                    "box": getattr(i, "box", (0,0,0,0)), 
                    "score": getattr(i, "score", 0)
                } 
                for i in raw_all
            ]
            
        return data
    
    

@AgentServer.custom_recognition("通用识别动作")
class GenericRecognition(CustomRecognition):
    
    def analyze(self, context: Context, argv: CustomRecognition.AnalyzeArg) -> CustomRecognition.AnalyzeResult:
        result = self.analyze_target(context, argv.image, "关卡")
        return CustomRecognition.AnalyzeResult(
            box=tuple(result.box),
            detail=json.dumps(result.to_dict(), ensure_ascii=False)
        )

    @staticmethod
    def analyze_target(context: Context, image, target: str, 
                       fuzzy_match: bool = True,
                       roi: tuple = (0, 0, 0, 0),
                       similarity_threshold: float = 0.75) -> RecognitionResult:
        
        from UtilTools import UtilTools  


        if UtilTools.is_node_defined(target):
            return GenericRecognition._run_specific_node(context, image, target)
        
        return GenericRecognition._run_dynamic_ocr_search(
            context, image, target, fuzzy_match, similarity_threshold
        )

    @staticmethod
    def _run_specific_node(context: Context, image, node_name: str) -> RecognitionResult:
        try:
            reco_detail = context.run_recognition(node_name, image)
        except Exception:
            return RecognitionResult(False, (0, 0, 0, 0))

        if not reco_detail:
            return RecognitionResult(False, (0, 0, 0, 0))
        box = getattr(reco_detail, "box", (0, 0, 0, 0))
        best = getattr(reco_detail, "best_result", None)
        is_found = (box is not None) and (box != (0, 0, 0, 0))
        
        return RecognitionResult(is_found, box, getattr(best, "text", ""), getattr(best, "score", 0), reco_detail)

    @staticmethod
    def _run_dynamic_ocr_search(context: Context, image, target_text: str, roi: tuple = (0, 0, 0, 0),
                                fuzzy: bool = True, threshold: float = 0.75) -> RecognitionResult:
        
        current_roi = roi
        temp_pipeline = {
            "Auto_Dynamic_OCR": {
                "recognition": "OCR", 
                "roi": roi,
                "action": "DoNothing"
            }
        }
        
        try:
            reco_detail = context.run_recognition("Auto_Dynamic_OCR", image, temp_pipeline)
        except Exception as e:
            print(f"[识别] OCR 执行异常: {e}")
            return RecognitionResult(False, (0, 0, 0, 0))

        if not reco_detail:
            return RecognitionResult(False, (0, 0, 0, 0))

        all_results = getattr(reco_detail, "all_results", []) or []
        target_clean = target_text.replace(" ", "").upper()
        target_digits = re.findall(r'\d+', target_clean)
        valid_candidates = []
        best_item = None
        max_score = -1.0

        for item in all_results:
            text = getattr(item, "text", "")
            if not text: continue
            text_clean = text.replace(" ", "").upper()
            
            if target_digits:
                text_digits = re.findall(r'\d+', text_clean)
                if target_digits != text_digits:
                    continue
            current_score = 0.0
            # 1. 精确匹配
            if text_clean == target_clean:
                current_score = 1.0
            
            # 2. 包含匹配 
            elif fuzzy and (target_clean in text_clean or text_clean in target_clean):
                 current_score = 0.95
            
            # 3. 相似度匹配
            elif fuzzy:
                ratio = difflib.SequenceMatcher(None, target_clean, text_clean).ratio()
                if ratio > threshold:
                    current_score = ratio
            
            if current_score > 0:
                setattr(item, "score", current_score) 
                valid_candidates.append(item)
                
                if current_score > max_score:
                    max_score = current_score
                    best_item = item

        if best_item:
            print(f"[OCR] 智能命中: '{target_text}' ≈ '{best_item.text}' (分值: {max_score:.2f})")
            return RecognitionResult(
                True, 
                getattr(best_item, "box", (0,0,0,0)), 
                getattr(best_item, "text", ""), 
                max_score, 
                reco_detail, 
                filtered_results=valid_candidates 
            )

        return RecognitionResult(False, (0, 0, 0, 0), details=reco_detail)