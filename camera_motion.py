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
