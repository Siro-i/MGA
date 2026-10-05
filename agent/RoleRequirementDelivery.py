import json
import time
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image
from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from match_mech_image import (
    build_feature_cache,
    cosine,
    features,
    load_feature_cache,
    source_signature,
)


_target_unit_image = None
_target_unit_id = ""
_target_koma_image = None

_TARGET_IMAGE_ROI = [53, 123, 424, 440]
_UNIT_LIBRARY = Path(__file__).resolve().parent.parent / "assets" / "resource" / "units_info"
_KOMA_FEATURE_TEMPLATE = "角色要求/当前目标棋子.png"
_KOMA_FEATURE_NODE = "角色要求_开发路线图目标棋子FeatureMatch"


def _parse_params(raw: str) -> dict:
    if isinstance(raw, dict):
        return raw
    parsed = json.loads(raw or "{}")
    return parsed if isinstance(parsed, dict) else {}


def _screencap(context: Context):
    return context.tasker.controller.post_screencap().wait().get()


def _click_point(context: Context, x: int, y: int) -> None:
    context.tasker.controller.post_click(int(x), int(y)).wait()
    time.sleep(0.8)


@lru_cache(maxsize=1)
def _portrait_library():
    library = _UNIT_LIBRARY.resolve()
    mapping = json.loads((library / "idmap.json").read_text(encoding="utf-8"))
    by_path = {}
    by_id = {}
    for row in mapping["rows"]:
        by_id[row["master_unit_id"]] = row
        for relative_path in row["portrait"]["paths"]:
            by_path.setdefault(relative_path, []).append(row)

    signature = source_signature(library, by_path)
    cache_path = library / "cache" / f"{signature}.npz"
    cached, reason = load_feature_cache(cache_path, signature, by_path)
    if cached is None:
        print(f"[角色要求] 立绘特征缓存不可用（{reason}），正在重建")
        cached, failed = build_feature_cache(library, by_path, cache_path, signature)
        print(f"[角色要求] 立绘特征缓存已重建，跳过损坏图片 {failed} 张")
    return library, by_path, by_id, cached


def _asset_path(library: Path, relative_path: str) -> Path:
    path = (library / relative_path).resolve()
    if not path.is_relative_to(library):
        raise ValueError(f"资源路径超出机体库：{relative_path}")
    return path


def _match_target_portrait(target_image, min_score: float, min_margin: float):
    library, by_path, by_id, cached = _portrait_library()
    rgb_image = Image.fromarray(np.ascontiguousarray(target_image[:, :, ::-1]))
    query = features(rgb_image, False)
    ranked = []
    for relative_path, rows in by_path.items():
        candidate = cached.get(relative_path)
        if candidate is None:
            continue
        structure = max(cosine(query[0], candidate[0]), 0.0)
        color = max(cosine(query[1], candidate[1]), 0.0)
        score = 0.78 * structure + 0.22 * color
        ranked.append((score, relative_path, rows))

    if not ranked:
        raise ValueError("机体库中没有可匹配的立绘")
    ranked.sort(key=lambda item: item[0], reverse=True)
    score, portrait_path, rows = ranked[0]
    koma_paths = {path for row in rows for path in row["koma"]["paths"]}
    if len(koma_paths) != 1:
        raise ValueError(f"立绘 {portrait_path} 无法唯一对应棋子图片")
    koma_path = next(iter(koma_paths))
    competing = next(
        (
            item for item in ranked[1:]
            if {path for row in item[2] for path in row["koma"]["paths"]} != koma_paths
        ),
        None,
    )
    second_score = competing[0] if competing else 0.0
    print(
        f"[角色要求] 立绘匹配：{portrait_path} score={score:.3f}，"
        f"其他棋子最高={second_score:.3f}"
    )
    if score < min_score or score - second_score < min_margin:
        raise ValueError("立绘匹配分数不足或目标不唯一")

    unit_id = next(row["master_unit_id"] for row in rows if koma_path in row["koma"]["paths"])
    koma_path = by_id[unit_id]["koma"]["paths"][0]
    with Image.open(_asset_path(library, koma_path)) as image:
        koma_image = image.convert("RGBA").copy()
    return unit_id, koma_path, koma_image


def _koma_feature_template(koma_image: Image.Image) -> np.ndarray:
    rgba = np.asarray(koma_image.convert("RGBA"), dtype=np.uint8)
    bgr = np.ascontiguousarray(rgba[:, :, [2, 1, 0]])
    bgr[rgba[:, :, 3] < 250] = (0, 255, 0)
    return bgr


@AgentServer.custom_action("角色要求交付机体记录目标")
class RoleRequirementDeliveryRememberTarget(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        global _target_unit_image, _target_unit_id, _target_koma_image

        params = _parse_params(argv.custom_action_param)
        image = _screencap(context)
        _target_unit_image = None
        _target_unit_id = ""
        _target_koma_image = None

        x, y, width, height = _TARGET_IMAGE_ROI
        if (
            image is None
            or len(image.shape) < 3
            or image.shape[2] < 3
            or image.shape[1] < x + width
            or image.shape[0] < y + height
        ):
            print(f"MGA_TASK_FAILED: [角色要求] 无法截取交付机体目标图像，ROI={_TARGET_IMAGE_ROI}")
            return False

        _target_unit_image = image[y : y + height, x : x + width, :3].copy()
        print(f"[角色要求] 已记录交付机体目标图像，ROI={_TARGET_IMAGE_ROI}")
        try:
            _target_unit_id, koma_path, _target_koma_image = _match_target_portrait(
                _target_unit_image,
                float(params.get("portrait_min_score", 0.60)),
                float(params.get("portrait_min_margin", 0.02)),
            )
        except Exception as exc:
            print(f"MGA_TASK_FAILED: [角色要求] 目标图像匹配 ID/棋子失败：{exc}")
            return False
        print(f"[角色要求] 交付机体目标 ID={_target_unit_id}，棋子={koma_path}")
        return True


@AgentServer.custom_action("角色要求交付机体选择目标")
class RoleRequirementDeliverySelectTarget(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        if not _target_unit_id or _target_koma_image is None:
            print("MGA_TASK_FAILED: [角色要求] 尚未记录目标 ID 和棋子图片")
            return False

        image = _screencap(context)
        if image is None or len(image.shape) < 3 or image.shape[2] < 3:
            print("MGA_TASK_FAILED: [角色要求] 无法截取开发路线图")
            return False

        template = _koma_feature_template(_target_koma_image)
        if not context.override_image(_KOMA_FEATURE_TEMPLATE, template):
            print("MGA_TASK_FAILED: [角色要求] 无法设置目标棋子 FeatureMatch 模板")
            return False

        detail = context.run_recognition(_KOMA_FEATURE_NODE, image)
        if not detail or not detail.hit or not detail.box:
            print(f"MGA_TASK_FAILED: [角色要求] 开发路线图未匹配到目标棋子 ID={_target_unit_id}")
            return False

        x, y, width, height = detail.box
        if width <= 0 or height <= 0:
            print(f"MGA_TASK_FAILED: [角色要求] 目标棋子匹配框无效：{detail.box}")
            return False
        point = (x + width // 2, y + height // 2)
        _click_point(context, *point)
        count = getattr(detail.best_result, "count", None)
        print(f"[角色要求] FeatureMatch 已选择交付机体 ID={_target_unit_id}，位置={point}，特征点={count}")
        return True
