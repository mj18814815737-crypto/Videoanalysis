from typing import Any, Dict, Optional

import config


def build_seedance_prompt(motion, subject=None, action=None, quality=None, constraints=None):
    # type: (Dict[str, Any], Optional[str], Optional[str], Optional[str], Optional[str]) -> str
    defaults = config.DEFAULT_PROMPT_CONTEXT
    camera_text = build_camera_text(motion)

    lines = [
        "[主体] {}".format(subject or defaults["subject"]),
        "[动作] {}".format(action or defaults["action"]),
        "[运镜] {}".format(camera_text),
        "[画质] {}".format(quality or defaults["quality"]),
        "[约束] {}".format(constraints or defaults["constraints"]),
    ]
    return "\n".join(lines)


def build_camera_text(motion):
    # type: (Dict[str, Any]) -> str
    camera_type = motion.get("type", "static")
    template = config.CAMERA_PROMPT_MAP.get(camera_type, config.CAMERA_PROMPT_MAP["static"])

    horizontal = motion.get("horizontal_trend", "none")
    vertical = motion.get("vertical_trend", "none")
    direction_cn = _direction_cn(horizontal, vertical)

    return template.format(
        direction_cn=direction_cn,
        horizontal_move_cn=_horizontal_move_cn(horizontal),
        vertical_move_cn=_vertical_move_cn(vertical),
    )


def _direction_cn(horizontal, vertical):
    # type: (str, str) -> str
    if horizontal == "left":
        return "向左"
    if horizontal == "right":
        return "向右"
    if vertical == "up":
        return "向上"
    if vertical == "down":
        return "向下"
    return "无明显方向"


def _horizontal_move_cn(horizontal):
    # type: (str) -> str
    if horizontal == "left":
        return "左移"
    if horizontal == "right":
        return "右移"
    return "平移"


def _vertical_move_cn(vertical):
    # type: (str) -> str
    if vertical == "up":
        return "上升"
    if vertical == "down":
        return "下降"
    return "移动"
