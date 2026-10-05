import json

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction


_SLOT_ORDER = ["左", "中", "右"]
_records = {}
_current_run_skip_reason = None


def _parse_params(raw: str) -> dict:
    return json.loads(raw or "{}")


def _slot_label(slot: str) -> str:
    return f"{slot}角色"


def _record_done(slot: str, requirement_type: str) -> None:
    _records[slot] = {
        "status": "done",
        "type": requirement_type,
    }


def _record_failed(slot: str, requirement_type: str) -> None:
    _records[slot] = {
        "status": "failed",
        "type": requirement_type,
    }


def _record_skipped(slot: str, reason: str) -> None:
    _records[slot] = {
        "status": "skip",
        "reason": reason,
    }


def _format_slot_summary(slot: str) -> str:
    record = _records.get(slot)
    if not record:
        return f"{slot}=未处理"

    status = record.get("status")
    if status == "done":
        return f"{slot}={record.get('type', '未知类别')}完成"
    if status == "failed":
        return f"{slot}={record.get('type', '未知类别')}失败"
    if status == "skip":
        return f"{slot}={record.get('reason', '已跳过')}跳过"
    return f"{slot}=未处理"


@AgentServer.custom_action("角色要求记录")
class RoleRequirementRecord(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        params = _parse_params(argv.custom_action_param)
        op = params.get("op")

        if op == "reset":
            _records.clear()
            print("[角色要求] 记录已重置")
            return True

        if op == "skip":
            slot = params.get("slot")
            reason = params.get("reason", "类别不明")
            if not slot:
                print("MGA_TASK_FAILED: [角色要求] 跳过记录缺少 slot")
                return False

            _record_skipped(slot, reason)
            print(f"[角色要求] {_slot_label(slot)}：{reason}，已跳过")
            return True

        if op == "skip_if_unprocessed":
            slot = params.get("slot")
            reason = params.get("reason", "距离更新还有")
            if not slot:
                print("MGA_TASK_FAILED: [角色要求] 跳过记录缺少 slot")
                return False

            if slot not in _records:
                _record_skipped(slot, reason)
                print(f"[角色要求] {_slot_label(slot)}：{reason}，已跳过")
            return True

        if op == "summary":
            summary = "，".join(_format_slot_summary(slot) for slot in _SLOT_ORDER)
            print(f"[角色要求] 汇总：{summary}")
            return True

        print(f"MGA_TASK_FAILED: [角色要求] 未知记录操作: {op}")
        return False


@AgentServer.custom_action("角色要求执行并记录")
class RoleRequirementRunAndRecord(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        global _current_run_skip_reason

        params = _parse_params(argv.custom_action_param)
        slot = params.get("slot")
        requirement_type = params.get("type")
        entry = params.get("entry")

        if not slot or not requirement_type or not entry:
            print("MGA_TASK_FAILED: [角色要求] 执行记录缺少 slot/type/entry")
            return False

        _current_run_skip_reason = None
        print(f"[角色要求] 开始处理 {_slot_label(slot)} {requirement_type}: {entry}")
        try:
            result = context.run_task(entry)
        except Exception as exc:
            _current_run_skip_reason = None
            _record_failed(slot, requirement_type)
            print(f"MGA_TASK_FAILED: [角色要求] {_slot_label(slot)} {requirement_type}：执行异常: {exc}")
            return False

        skip_reason = _current_run_skip_reason
        _current_run_skip_reason = None
        if result is None:
            _record_failed(slot, requirement_type)
            print(f"MGA_TASK_FAILED: [角色要求] {_slot_label(slot)} {requirement_type}：执行失败")
            return False

        if skip_reason:
            _record_skipped(slot, skip_reason)
            print(f"[角色要求] {_slot_label(slot)}：{skip_reason}，已跳过")
            # False intentionally routes the outer delivery node to the
            # slot-specific detail-page return branch.
            return False

        _record_done(slot, requirement_type)
        print(f"[角色要求] {_slot_label(slot)} {requirement_type}：完成")
        return True


@AgentServer.custom_action("角色要求当前执行标记跳过")
class RoleRequirementMarkCurrentRunSkipped(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        global _current_run_skip_reason

        params = _parse_params(argv.custom_action_param)
        reason = params.get("reason", "无法完成")
        _current_run_skip_reason = reason
        print(f"[角色要求] 当前执行标记为跳过：{reason}")
        return True
