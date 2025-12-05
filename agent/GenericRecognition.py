import json
import difflib
from typing import Tuple, Any
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context

# --- [核心修复点] 数据层 ---
class RecognitionResult:
    def __init__(self, found: bool, box: Tuple[int, int, int, int], text: str = "", score: float = 0.0, details: Any = None):
        self.found = found
        self.box = box if box is not None else (0, 0, 0, 0)
        self.text = text
        self.score = score
        self.details = details

    def to_dict(self):
        return {
            "found": self.found,
            "roi": list(self.box), 
            "text": self.text,
            "score": self.score
        }

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
        
        best_item = None
        max_score = -1.0

        for item in all_results:
            text = getattr(item, "text", "")
            if not text: continue
            
            text_clean = text.replace(" ", "").upper()
            current_score = 0.0
            
            if text_clean == target_clean:
                current_score = 1.0
            elif fuzzy and (target_clean in text_clean):
                current_score = 0.9
            elif fuzzy:
                ratio = difflib.SequenceMatcher(None, target_clean, text_clean).ratio()
                if ratio > threshold:
                    current_score = ratio
            
            if current_score > max_score and current_score > 0:
                max_score = current_score
                best_item = item

        if best_item and max_score > 0:
            return RecognitionResult(True, getattr(best_item, "box", (0,0,0,0)), getattr(best_item, "text", ""), max_score, reco_detail)

        return RecognitionResult(False, (0, 0, 0, 0), details=reco_detail)