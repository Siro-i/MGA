"""Select a roadmap unit for a role requirement's commissioned development."""

import math
import time

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction


_LEVELS = (
    ("N", "角色要求_委托开发_N特征", "角色要求_委托开发_N颜色", [0, 0, 90], [179, 35, 240], 0.60),
    ("R", "角色要求_委托开发_R特征", "角色要求_委托开发_R颜色", [5, 65, 80], [27, 255, 242], 0.45),
    ("SR", "角色要求_委托开发_SR特征", "角色要求_委托开发_SR颜色", [80, 35, 80], [103, 255, 255], 0.40),
    ("SSR", "角色要求_委托开发_SSR特征", "角色要求_委托开发_SSR颜色", [12, 40, 243], [35, 255, 255], 0.12),
)
_CLICK_OFFSET = (65, -145)


def _rect(box):
    if box is None:
        return None
    if all(hasattr(box, key) for key in ("x", "y", "w", "h")):
        return tuple(int(getattr(box, key)) for key in ("x", "y", "w", "h"))
    if isinstance(box, (tuple, list)) and len(box) == 4:
        return tuple(int(value) for value in box)
    return None


def _color_roi(box):
    x, y, width, height = box
    inner_width = max(1, round(width * 0.56))
    inner_height = max(1, round(height * 0.56))
    return [
        x + (width - inner_width) // 2,
        y + (height - inner_height) // 2,
        inner_width,
        inner_height,
    ]


def _candidate_point(box, image_width, image_height):
    x, y, width, height = box
    if not (18 <= width <= 90 and 18 <= height <= 90):
        return None
    if not (0.65 <= width / height <= 1.55):
        return None
    point = (x + width // 2 + _CLICK_OFFSET[0], y + height // 2 + _CLICK_OFFSET[1])
    if not (0 <= point[0] < image_width and 0 <= point[1] < image_height):
        return None
    return point


def _matches_color(context, image, node, box, lower, upper, fraction):
    roi = _color_roi(box)
    required = math.ceil(roi[2] * roi[3] * fraction)
    override = {
        node: {
            "recognition": {
                "type": "ColorMatch",
                "param": {
                    "roi": roi,
                    "method": 40,
                    "lower": [lower],
                    "upper": [upper],
                    "count": required,
                    "connected": False,
                },
            }
        }
    }
    detail = context.run_recognition(node, image, override)
    return bool(detail and detail.hit), roi, required


@AgentServer.custom_action("角色要求委托开发选择机体")
class RoleRequirementCommissionSelectUnit(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        image = context.tasker.controller.post_screencap().wait().get()
        if image is None or len(image.shape) < 3:
            print("MGA_TASK_FAILED: [角色要求委托开发] 无法截取开发路线图")
            return False

        image_height, image_width = image.shape[:2]
        for level, feature_node, color_node, lower, upper, fraction in _LEVELS:
            detail = context.run_recognition(feature_node, image)
            if not detail or not detail.hit:
                continue

            results = sorted(
                getattr(detail, "all_results", []) or [],
                key=lambda item: getattr(item, "count", 0) or 0,
                reverse=True,
            )
            for result in results:
                if (getattr(result, "count", 0) or 0) < 4:
                    continue
                box = _rect(getattr(result, "box", None))
                if box is None:
                    continue
                point = _candidate_point(box, image_width, image_height)
                if point is None:
                    continue
                color_hit, roi, required = _matches_color(
                    context, image, color_node, box, lower, upper, fraction
                )
                if not color_hit:
                    continue

                click = context.tasker.controller.post_click(*point)
                click.wait()
                if not click.status.succeeded:
                    print(f"MGA_TASK_FAILED: [角色要求委托开发] 点击 {level} 机体失败，位置={point}")
                    return False
                time.sleep(0.8)
                print(
                    f"[角色要求委托开发] 选择 {level} 机体，特征点={getattr(result, 'count', None)}，"
                    f"标签框={box}，颜色ROI={roi}，最低像素={required}，点击={point}"
                )
                return True

        print("[角色要求委托开发] 未找到颜色校验和点击边界均有效的 N/R/SR/SSR 标签")
        return False
