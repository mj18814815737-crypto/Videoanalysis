from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Tuple

import config


def analyze_camera_motion(frame_paths):
    # type: (List[Path]) -> Dict[str, Any]
    if len(frame_paths) < 2:
        print("警告：抽帧数量少于 2，按 static 固定镜头处理。")
        return {
            "type": "static",
            "intensity": 0.0,
            "horizontal_trend": "none",
            "vertical_trend": "none",
            "dx": 0.0,
            "dy": 0.0,
            "frame_count": len(frame_paths),
        }

    cv2, np = _load_cv_dependencies()
    diffs = []  # type: List[float]
    dx_values = []  # type: List[float]
    dy_values = []  # type: List[float]

    previous = _load_gray(frame_paths[0], cv2, np)
    for frame_path in frame_paths[1:]:
        current = _load_gray(frame_path, cv2, np)
        diffs.append(_frame_diff(previous, current, cv2, np))
        dx, dy = _optical_flow(previous, current, cv2, np)
        dx_values.append(dx)
        dy_values.append(dy)
        previous = current

    diff_rate = float(mean(diffs))
    dx = float(mean(dx_values))
    dy = float(mean(dy_values))
    camera_type = classify_motion(diff_rate, dx, dy)
    horizontal_trend, vertical_trend = direction_from_flow(dx, dy)

    return {
        "type": camera_type,
        "intensity": round(diff_rate, 4),
        "horizontal_trend": horizontal_trend,
        "vertical_trend": vertical_trend,
        "dx": round(dx, 4),
        "dy": round(dy, 4),
        "frame_count": len(frame_paths),
    }


def classify_motion(diff_rate, dx, dy):
    # type: (float, float, float) -> str
    thresholds = config.DIFF_THRESHOLDS
    if diff_rate < thresholds["static"]:
        return "static"
    if diff_rate < thresholds["slow"]:
        return "slow_pan_tilt"
    if diff_rate < thresholds["medium"]:
        if abs(dx) >= abs(dy):
            return "horizontal_tracking"
        return "vertical_tilt"
    if diff_rate < thresholds["fast"]:
        return "fast_movement"
    return "dynamic_violent"


def direction_from_flow(dx, dy):
    # type: (float, float) -> Tuple[str, str]
    epsilon = config.DIRECTION_EPSILON
    if abs(dx) < epsilon and abs(dy) < epsilon:
        return "none", "none"

    horizontal_trend = "none"
    vertical_trend = "none"
    if abs(dx) >= epsilon:
        horizontal_trend = "right" if dx > 0 else "left"
    if abs(dy) >= epsilon:
        vertical_trend = "down" if dy > 0 else "up"
    return horizontal_trend, vertical_trend


def extract_camera_params(frames):
    # type: (List[Any]) -> Dict[str, Any]
    if len(frames) < 2:
        return {"type": "static", "direction": None, "speed": 5.0, "shot_scale": "medium"}

    cv2, np = _load_cv_dependencies()
    dx_values = []  # type: List[float]
    dy_values = []  # type: List[float]
    speed_values = []  # type: List[float]

    previous = _frame_to_gray(frames[0], cv2, np)
    for frame in frames[1:]:
        current = _frame_to_gray(frame, cv2, np)
        flow = cv2.calcOpticalFlowFarneback(
            previous,
            current,
            None,
            pyr_scale=0.5,
            levels=3,
            winsize=15,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0,
        )
        dx_values.append(float(np.mean(flow[..., 0])))
        dy_values.append(float(np.mean(flow[..., 1])))
        speed_values.append(float(np.mean(np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2))))
        previous = current

    dx = float(mean(dx_values)) if dx_values else 0.0
    dy = float(mean(dy_values)) if dy_values else 0.0
    speed = min(10.0, max(0.0, (float(mean(speed_values)) if speed_values else 5.0)))

    if abs(dx) >= abs(dy) and abs(dx) >= config.DIRECTION_EPSILON:
        motion_type = "horizontal_pan"
        direction = "left_to_right" if dx > 0 else "right_to_left"
    elif abs(dy) >= config.DIRECTION_EPSILON:
        motion_type = "vertical_tilt"
        direction = "top_to_bottom" if dy > 0 else "bottom_to_top"
    else:
        motion_type = "static"
        direction = None

    return {
        "type": motion_type,
        "direction": direction,
        "speed": round(speed, 2),
        "shot_scale": "medium",
    }


def _load_cv_dependencies():
    # type: () -> Tuple[Any, Any]
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("未找到 Python 依赖：opencv-python / numpy。请先运行 pip install -r requirements.txt。") from exc
    return cv2, np


def _load_gray(frame_path, cv2, np=None):
    # type: (Path, Any, Any) -> Any
    if np is None:
        _, np = _load_cv_dependencies()
    image_data = np.fromfile(str(frame_path), dtype=np.uint8)
    image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("无法读取帧文件：{}".format(frame_path))
    resized = cv2.resize(image, config.ANALYSIS_SIZE)
    return cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)


def _frame_to_gray(frame, cv2, np):
    # type: (Any, Any, Any) -> Any
    if isinstance(frame, Path):
        return _load_gray(frame, cv2, np)
    resized = cv2.resize(frame, config.ANALYSIS_SIZE)
    return cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)


def _frame_diff(previous, current, cv2, np):
    # type: (Any, Any, Any, Any) -> float
    diff = cv2.absdiff(previous, current)
    return float(np.mean(diff) / 255.0)


def _optical_flow(previous, current, cv2, np):
    # type: (Any, Any, Any, Any) -> Tuple[float, float]
    flow = cv2.calcOpticalFlowFarneback(
        previous,
        current,
        None,
        pyr_scale=0.5,
        levels=3,
        winsize=15,
        iterations=3,
        poly_n=5,
        poly_sigma=1.2,
        flags=0,
    )
    return float(np.mean(flow[..., 0])), float(np.mean(flow[..., 1]))
