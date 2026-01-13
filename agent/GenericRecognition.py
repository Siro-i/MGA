import json
from typing import Tuple, Any
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context

class RecognitionResult:
    """
    [标准化输出] 统一识别结果格式
    """
    def __init__(self, found: bool, box: Tuple[int, int, int, int], text: str = "", score: float = 0.0, details: Any = None):
        self.found = found
        self.box = box if box is not None else (0, 0, 0, 0)
        self.text = text
        self.score = score
        self.details = details

    def to_dict(self):
        """转为标准字典格式供流水线使用"""
        data = {
            "found": self.found,
            "roi": list(self.box),
            "text": self.text,
            "score": self.score,
        }
        
        # 提取 all_results (如果底层返回了多个结果)
        raw_all = getattr(self.details, "all_results", []) or []
        data["all_results"] = [
            {
                "text": getattr(i, "text", ""), 
                "box": getattr(i, "box", (0,0,0,0)), 
                "score": getattr(i, "score", 0.0)
            } 
            for i in raw_all
        ]
        return data

@AgentServer.custom_recognition("通用识别动作")
class GenericRecognition(CustomRecognition):
    def analyze(self, context: Context, argv: CustomRecognition.AnalyzeArg) -> CustomRecognition.AnalyzeResult:
        result = self.analyze_target(context, argv.image, "")
        return CustomRecognition.AnalyzeResult(
            box=tuple(result.box),
            detail=json.dumps(result.to_dict(), ensure_ascii=False)
        )

    @staticmethod
    def analyze_target(context: Context, image, target: str, ) -> RecognitionResult:
        return GenericRecognition.run_node(
            context, image, target
        )
    @staticmethod
    def run_node(context: Context, image, node_name: str) -> RecognitionResult:
        """
        [原子操作] 运行指定的 Pipeline 节点
        输入: context, image, 节点名称
        输出: 标准化的 RecognitionResult
        """
        try:
            # 直接调用 MAA 底层接口运行特定节点
            reco_detail = context.run_recognition(node_name, image)
        except Exception:
            # 运行出错（如节点不存在）返回未找到
            return RecognitionResult(False, (0, 0, 0, 0))

        if not reco_detail:
            return RecognitionResult(False, (0, 0, 0, 0))

        # 提取最佳结果
        box = getattr(reco_detail, "box", (0, 0, 0, 0))
        best = getattr(reco_detail, "best_result", None)
        
        # 判断是否找到：box 存在且不为 (0,0,0,0)
        is_found = (box is not None) and (box != (0, 0, 0, 0))
        
        # 封装标准化结果
        return RecognitionResult(
            found=is_found, 
            box=box, 
            text=getattr(best, "text", ""), 
            score=getattr(best, "score", 0.0), 
            details=reco_detail
        )