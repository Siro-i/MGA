import json
import time
from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer
from StageSelect import select_stage


VALID_STAGE_TARGETS = {"HARD1", "HARD2", "HARD3", "HARD4", "HARD5"}


def _parse_stage_targets(raw):
    if isinstance(raw, str):
        parts = (
            raw.replace("，", ",")
            .replace("、", ",")
            .replace("\n", ",")
            .replace(" ", ",")
            .split(",")
        )
    elif isinstance(raw, list):
        parts = raw
    else:
        parts = []

    targets = []
    seen = set()
    for item in parts:
        target = str(item).strip().upper()
        if not target or target in seen:
            continue
        seen.add(target)
        targets.append(target)
    return targets


@AgentServer.custom_action("BatchStageSweep")
class BatchStageSweep(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        params = json.loads(argv.custom_action_param or "{}")
        targets = _parse_stage_targets(
            params.get("stage_targets", params.get("stage_target", []))
        )
        skip_task = params.get("skip_task", "连续扫荡_略过入口")
        skip_optional = bool(params.get("skip_optional", False))

        if not targets:
            print("[BatchStageSweep] 未配置扫荡关卡，跳过")
            return True

        for target in targets:
            if not context.tasker.running:
                context.tasker.post_stop().wait()
                return False

            if target not in VALID_STAGE_TARGETS:
                print(f"[BatchStageSweep] 非法关卡 `{target}`，跳过")
                continue

            print(f"[BatchStageSweep] 开始处理 {target}")
            if not select_stage(context, target):
                print(f"[BatchStageSweep] 当前故事未找到 {target}，跳过")
                continue

            time.sleep(0.8)
            result = context.run_task(skip_task)
            if result is None:
                if skip_optional and context.tasker.running:
                    print(f"[BatchStageSweep] {target} 未找到可用略过，继续下一个关卡")
                    continue
                print(f"MGA_TASK_FAILED: [BatchStageSweep] {target} 扫荡链 `{skip_task}` 执行失败")
                return False

            print(f"[BatchStageSweep] {target} 扫荡完成")
            time.sleep(1.0)

        print("[BatchStageSweep] 选中关卡处理完成")
        return True
