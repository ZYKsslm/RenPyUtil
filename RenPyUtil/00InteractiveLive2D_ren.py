# 此文件提供了一系列基于Ren'Py的功能类，以供Ren'Py开发者调用
# 作者  ZYKsslm
# 仓库  https://github.com/ZYKsslm/RenPyUtil
# 声明  该源码使用 MIT 协议开源，但若使用需要在程序中标明作者信息
"""renpy
python early:
"""


import os
import json
import pygame

from typing import Union

Live2D = Live2D  # type: ignore
renpy = renpy  # type: ignore
store = store  # type: ignore


class Timer:
    def __init__(self, duration: float, callback: callable, repeat=False):
        self.duration = duration
        self.callback = callback
        self.repeat = repeat
        self.t = 0.0

    def start(self, t):
        self.t = self.duration + t

    def end(self, t):
        if self.t <= t:
            self.callback()
            if self.repeat:
                self.start(t)


class Live2DAssembly:
    def __init__(self, 
        *areas,
        motions: Union[str, list[str]] = None,
        expressions: Union[str, list[str]] = None, # 非排他性表情列表
        audio: str = None, 
        mouse: str = None, 
        timer: Timer = None, 
        attr_getter: callable = None, 
        hovered: callable = None, 
        unhovered: callable = None, 
        action: callable = None, 
        keep=False
    ):
        if isinstance(motions, str):
            motions = [motions]
        if isinstance(expressions, str):
            expressions = [expressions]

        self.areas = areas
        self.motions = motions or []
        self.expressions = expressions or []
        self.audio = audio
        self.mouse = mouse
        self.timer = timer
        self.attr_getter = attr_getter
        self.hovered = hovered
        self.unhovered = unhovered
        self.action = action
        self.keep = keep

        self._st = 0.0 # 开始时刻
        self.t = 0.0   # 触发时刻
        self.duration = 0.0 # 持续时长
        self.modal = False  # 是否为模态动作

    def set_duration(self, common):
        self.duration = 0.0
        for motion in self.motions:
            self.duration += common.motions[motion].duration
        
        return self.duration

    def get_assembly(self):
        if self.attr_getter:
            self.motions, self.expressions = self.attr_getter()
        
        return self.motions, self.expressions

    def contained(self, x, y):
        for area in self.areas:
            if Live2DAssembly.contained_rect(area, x, y):
                return True
        return False

    def activate(self, common, st):
        self.set_duration(common)
        self.st = st

        return self

    def _action(self):
        run = True
        if self.action:
            res = self.action()
            run = res if res is not None else True
        
        return run

    @staticmethod
    def contained_rect(area: tuple[int, int, int, int], x: int, y: int):
        if area[0] < x < area[0] + area[2] and area[1] < y < area[1] + area[3]:
            return True
        else:
            return False

    @property
    def st(self):
        return self._st

    @st.setter
    def st(self, value):
        self._st = value
        self.t = value + self.duration
        if self.timer:
            self.timer.start(value)

    def end(self, t):
        if self.timer:
            self.timer.end(t)
        if self.keep:
            return False
        else:
            return self.t <= t


class InteractiveLive2D(Live2D):
    """ `Live2D` 动作交互实现"""

    def __init__(self, 
        idle_motions: Union[str, list[str]], 
        idle_exps: Union[str, list[str]] = None, 
        live2d_assemblies: list[Live2DAssembly] = None, 
        eye_follow=False,
        head_follow=False,
        body_follow=False,
        eye_center=None,
        head_center=None,
        body_center=None,
        rotate_strength=0.02,
        max_angle=None,
        min_angle=None,
        range=None,
        **properties
    ):
        super().__init__(**properties)
        self.all_motions = list(self.common.motions.keys())
        self.all_expressions = list(self.common.expressions.keys())

        if isinstance(idle_motions, str):
            idle_motions = [idle_motions]
        if isinstance(idle_exps, str):
            idle_exps = [idle_exps]
        
        if not set(idle_motions).issubset(self.all_motions):
            raise ValueError(f"未知的动作: {idle_motions}")
        if idle_exps and (not set(idle_exps).issubset(self.all_expressions)):
            raise ValueError(f"未知的表情: {idle_exps}")

        self.motions = idle_motions
        self.used_nonexclusive = idle_exps or []
        
        if eye_follow or head_follow or body_follow:
            filename: str = properties["filename"]
            if filename.endswith(".model3.json"):
                filename = filename.replace("model3", "physics3")
            else:
                name = os.path.basename(filename)
                filename = f"{filename}/{name}.physics3.json"
            
            try:
                with renpy.loader.load(filename) as f:
                    physics_data = json.load(f)
                    angle = physics_data["PhysicsSettings"][0]["Normalization"]["Angle"]
                    self.max_angle = angle["Maximum"]
                    self.min_angle = angle["Minimum"]
            except Exception as e:
                if max_angle and min_angle:
                    self.max_angle = max_angle
                    self.min_angle = min_angle
                else:
                    raise ValueError(f"无法获取模型角度参数: {filename}，请手动添加 max_angle 和 min_angle 参数") from e

        self.idle_motions = idle_motions
        self.idle_exps = idle_exps or []
        self.live2d_assemblies = live2d_assemblies or []

        self.eye_follow = eye_follow
        self.head_follow = head_follow
        self.body_follow = body_follow
        if not self.head_follow and self.body_follow:
            self.head_follow = True
        self.eye_center = eye_center
        self.head_center = head_center
        self.body_center = body_center
        self.rotate_strength = rotate_strength
        self.angle_params = {
            "ParamAngleX": 0.0,
            "ParamBodyAngleX": 0.0,
            "ParamEyeBallX": 0.0,
            "ParamAngleY": 0.0,
            "ParamBodyAngleY": 0.0,
            "ParamEyeBallY": 0.0
        }

        self.st = None
        self.mouse_pos = (0, 0)
        self.range = range
        self.size = (0, 0)
        self.toggled_motions = None
        self.toggled_exps = None
        self.current_assembly = None
        self.hovered_assembly = None
        self._modal = False

    @property
    def modal(self):
        return self._modal

    @modal.setter
    def modal(self, value):
        for live2d_assembly in self.live2d_assemblies:
            live2d_assembly.modal = value

            if live2d_assembly.mouse and hasattr(store, "default_mouse"):
                del store.default_mouse

        self._modal = value
    
    def turn_to_assembly(self, live2d_assembly: Live2DAssembly):
        if live2d_assembly._action():
            self.motions, self.used_nonexclusive = live2d_assembly.get_assembly()
            self.current_assembly = live2d_assembly.activate(self.common, self.st)
        
        renpy.redraw(self, 0)

    def toggle_motion(self, motions: Union[str, list[str]], reset_exps=False):
        self.modal = False
        if isinstance(motions, str):
            motions = [motions]

        if motions == self.motions:
            self.toggled_motions = motions
            self.motions = self.idle_motions
        else:
            self.toggled_motion = None
            self.motions = motions

        if reset_exps:
            self.used_nonexclusive = self.idle_exps
        renpy.redraw(self, 0)

    def toggle_exp(self, exps: Union[str, list[str]], reset_motions=False):
        self.modal = False
        if isinstance(exps, str):
            exps = [exps]
        
        exps_set = set(exps)
        used_nonexclusive_set = set(self.used_nonexclusive)
        if exps_set.issubset(used_nonexclusive_set):
            self.toggled_exp = exps
            self.used_nonexclusive = list(used_nonexclusive_set - exps_set)
        else:
            self.toggled_exp = None
            self.used_nonexclusive += exps

        if reset_motions:
            self.motions = self.idle_motions
        renpy.redraw(self, 0)

    def reset_assembly(self):
        self.modal = False
        self.current_assembly = None
        self.motions = self.idle_motions
        self.used_nonexclusive = self.idle_exps
        renpy.redraw(self, 0)

    def _end_assembly(self, st):
        if self.current_assembly.end(st):
            self.current_assembly = None
            self.motions = self.idle_motions
            self.used_nonexclusive = self.idle_exps
            renpy.redraw(self, 0)

    def update_angle(self, rotate_center):
        if self.range and (not Live2DAssembly.contained_rect(self.range, *self.mouse_pos)):
            x, y = 0.0, 0.0
        else:
            d_x = self.mouse_pos[0] - rotate_center[0]
            d_y = rotate_center[1] - self.mouse_pos[1]
            x = d_x * self.rotate_strength
            y = d_y * self.rotate_strength

            if x < self.min_angle: x = self.min_angle
            elif x > self.max_angle: x = self.max_angle

            if y < self.min_angle: y = self.min_angle
            elif y > self.max_angle: y = self.max_angle
        
        return x, y

    def update(self, common, st, st_fade):
        """
        This updates the common model with the information taken from the
        motions associated with this object. It returns the delay until
        Ren'Py needs to cause a redraw to occur, or None if no delay
        should occur.
        """
        
        if not self.motions:
            return

        # True if the motion should be faded in.
        do_fade_in = True

        # True if the motion should be faded out.
        do_fade_out = True

        # True if this is the last frame of a series of motions.
        last_frame = False

        # The index of the current motion in self.motions.
        current_index = 0

        # The motion object to display.
        motion = None

        # Determine the current motion.

        motion_st = st

        if st_fade is not None:
            motion_st = st - st_fade

        for m in self.motions:
            motion = common.motions.get(m, None)

            if motion is None:
                continue

            if motion.duration > st:
                break

            elif (motion.duration > motion_st) and not common.is_seamless(m):
                break

            motion_st -= motion.duration
            st -= motion.duration
            current_index += 1

        else:

            if motion is None:
                return None

            m = self.motions[-1]

            if (not self.loop) or (not motion.duration):
                st = motion.duration
                last_frame = True

            elif (st_fade is not None) and not common.is_seamless(m):
                # This keeps a motion from being restarted after it would have
                # been faded out.
                motion_start = motion_st - motion_st % motion.duration

                if (st - motion_start) > motion.duration:
                    st = motion.duration
                    last_frame = True

        if motion is None:
            return None

        # Determine the name of the current, last, and next motions. These are
        # None if there is no motion.

        if current_index < len(self.motions):
            current_name = self.motions[current_index]
        else:
            current_name = self.motions[-1]

        if current_index > 0:
            last_name = self.motions[current_index - 1]
        else:
            last_name = None

        if current_index < len(self.motions) - 1:
            next_name = self.motions[current_index + 1]
        elif self.loop:
            next_name = self.motions[-1]
        else:
            next_name = None

        # Handle seamless.

        if (last_name == current_name) and common.is_seamless(current_name):
            do_fade_in = False

        if (next_name == current_name) and common.is_seamless(current_name) and (st_fade is None):
            do_fade_out = False

        # Apply the motion.

        motion_data = motion.get(st, st_fade, do_fade_in, do_fade_out)

        if self.head_follow:
            self.angle_params["ParamAngleX"], self.angle_params["ParamAngleY"] = self.update_angle(self.head_center)
        if self.body_follow:
            self.angle_params["ParamBodyAngleX"], self.angle_params["ParamBodyAngleY"] = self.update_angle(self.body_center)
        if self.eye_follow:
            self.angle_params["ParamEyeBallX"], self.angle_params["ParamEyeBallY"] = self.update_angle(self.eye_center)
            
        for k, v in motion_data.items():

            kind, key = k
            factor, value = v

            if kind == "PartOpacity":
                common.model.set_part_opacity(key, value)
                
            elif kind == "Parameter":
                if (
                    self.head_follow and key in ("ParamAngleX", "ParamAngleY") or 
                    self.body_follow and key in ("ParamBodyAngleX", "ParamBodyAngleY") or 
                    self.eye_follow and key in ("ParamEyeBallX", "ParamEyeBallY")
                ):
                    value = self.angle_params[key]

                common.model.set_parameter(key, value, factor)

            elif kind == "Model":
                common.model.set_parameter(key, value, factor)

        if last_frame:
            return None
        else:
            return motion.wait(st, st_fade, do_fade_in, do_fade_out)

    def update_expressions(self, st):
        try:
            return super().update_expressions(st)
        except:
            renpy.gl2.live2d.states[self.name].old_expressions = []

    def render(self, width, height, st, at):
        render = super().render(width, height, st, at)
        self.size = render.get_size()
        self.st = st
        if self.motions != self.idle_motions and self.current_assembly:
            self._end_assembly(st)
        
        return render
        
    def event(self, ev, x, y, st):
        self.mouse_pos = (x, y)
        for live2d_assembly in self.live2d_assemblies:
            if live2d_assembly.modal:
                continue
            if live2d_assembly.contained(x, y):
                self.hovered_assembly = live2d_assembly
                if live2d_assembly.mouse:
                    store.default_mouse = live2d_assembly.mouse
                if live2d_assembly.hovered:
                    live2d_assembly.hovered(live2d_assembly)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if live2d_assembly._action():
                        if live2d_assembly.audio:
                            renpy.music.play(live2d_assembly.audio, channel="voice")
                        self.motions, self.used_nonexclusive = live2d_assembly.get_assembly()
                        self.current_assembly = live2d_assembly.activate(self.common, st)
            else:
                if live2d_assembly is self.hovered_assembly:
                    if hasattr(store, "default_mouse"):
                        del store.default_mouse
                    if live2d_assembly.unhovered:
                        live2d_assembly.unhovered(live2d_assembly)
                    self.hovered_assembly = None

        print(x, y)
        renpy.redraw(self, 0)

