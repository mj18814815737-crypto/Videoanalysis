import random
import re

from config import ACTION_SPEED_VARIANTS, SPEED_LEVELS


class PromptGen:
    def __init__(self, cam_params, action):
        self.cam = cam_params
        self.action = action

    def generate(self, target=10):
        combos = []
        dirs = [None]
        if self.cam["direction"] and self.cam["type"] in ["horizontal_pan", "vertical_tilt"]:
            dirs = [self.cam["direction"], self._reverse(self.cam["direction"])]
        for sp in SPEED_LEVELS:
            for d in dirs:
                combos.append((sp, d, self.action))

        expanded = []
        for sp, d, act in combos:
            expanded.append((sp, d, act))
            for var in ACTION_SPEED_VARIANTS:
                new_act = re.sub(r"(缓慢|快速|较快|较慢)", "", act).strip()
                expanded.append((sp, d, "{}{}".format(var, new_act or act)))
        combos = list(set(expanded))

        if len(combos) < target:
            extra = []
            for ss in ["medium", "close"]:
                if ss != self.cam["shot_scale"]:
                    for c in combos[:]:
                        extra.append(c + (ss,))
            if len(combos) + len(extra) < target:
                for c in combos[:]:
                    extra.append(c + ("弧形{}".format(self.cam["type"]),))
            combos.extend(extra[: target - len(combos)])

        selected = random.sample(combos, target) if len(combos) > target else combos
        return [self._render(c) for c in selected]

    def _reverse(self, d):
        m = {"left_to_right": "right_to_left", "right_to_left": "left_to_right", "top_to_bottom": "bottom_to_top", "bottom_to_top": "top_to_bottom"}
        return m.get(d, d)

    def _render(self, combo):
        sp, d, act = combo[:3]
        cam_type = self.cam["type"].replace("_", "")
        dir_text = {"left_to_right": "从左向右", "right_to_left": "从右向左", "top_to_bottom": "从上向下", "bottom_to_top": "从下向上"}.get(d, "") if d else ""
        shot = self.cam["shot_scale"]
        if len(combo) > 3:
            cam_type = combo[3] if "弧形" in combo[3] else cam_type
            shot = shot if "弧形" in combo[3] else combo[3]
        camera = "{}，{}，{}，{}景".format(cam_type, sp, dir_text, shot) if dir_text else "{}，{}，{}景".format(cam_type, sp, shot)
        return "{}。{}。4K，电影感，浅景深。".format(camera, act)
