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

from renpy.gl2.live2d import states  # type: ignore


class Live2DAssembly:
    def __init__(self, 
        *areas,
        motions: str = None,
        expressions: Union[str, list[str]] = None,  # 一个表情或一个非排他性表情列表
        play = None,   # 可以 play 的对象
        channel: str = "voice", 
        mouse: str = None,  # 光标名称
        hovered: callable = None, 
        unhovered: callable = None, 
        action: callable = None, 
        keep=False
    ):
        # TODO: motions 和 expressions 参数适配
        motions = [motions] if isinstance(motions, str) else motions
        expressions = [expressions] if isinstance(expressions, str) else expressions

        self.areas = areas
        self.motions = motions or []
        self.expressions = expressions or []
        self.play = play
        self.channel = channel
        self.mouse = mouse
        self.hovered = hovered
        self.unhovered = unhovered
        self.action = action
        self.keep = keep

        self.modal = False
        self.st = 0.0

    def contained(self, x, y):
        for area in self.areas:
            if Live2DAssembly.contained_rect(area, x, y):
                return True
            
        return False

    def is_triggered(self):
        run = True
        if self.action:
            if res := self.action() is not None:
                run = bool(res)
            
        return run

    @staticmethod
    def contained_rect(area: tuple[int, int, int, int], x: int, y: int):
        if area[0] < x < area[0] + area[2] and area[1] < y < area[1] + area[3]:
            return True
        else:
            return False

    def end(self, t):
        if self.keep:
            return False
        else:
            # 2.0 表示的是持续时间
            return self.st + 2.0 <= t


class InteractiveLive2D(Live2D):
    """ `Live2D` 动作交互实现"""

    def __init__(self, 
        idle_motions: str, 
        idle_exps: Union[str, list[str]] = None,    # 一个表情或一个非排他性表情列表
        *,
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
        range=None, # TODO: 待优化：交互区域范围
        **properties
    ):
        super().__init__(**properties)

        # TODO: motions 和 expressions 参数适配
        idle_motions = [idle_motions]
        idle_exps = [idle_exps] if isinstance(idle_exps, str) else idle_exps

        self.name = properties['filename']
        self.old_state = None
        self.new_state = None
        self.tmp_st = 0.0
        self.reset_st = 0.0

        self.motions = idle_motions
        self.used_nonexclusive = idle_exps or []
        self.idle_motions = idle_motions
        self.idle_exps = idle_exps or []
        self.live2d_assemblies = live2d_assemblies or []

        self.setup_following(
            eye_follow, head_follow, body_follow, 
            eye_center, head_center, body_center, 
            rotate_strength, max_angle, min_angle,
            properties["filename"]
        )

        self.mouse_pos = (0, 0)
        self.range = range
        self.size = (0, 0)
        self.toggled_motions = None
        self.toggled_exps = None
        self.current_assembly = None
        self.hovered_assembly = None
        self._modal = False

    def setup_following(self,
        eye_follow, head_follow, body_follow, 
        eye_center, head_center, body_center, 
        rotate_strength, max_angle, min_angle,
        filename
    ):
        self.eye_follow = eye_follow
        self.head_follow = head_follow
        self.body_follow = body_follow

        # 确保头部跟随逻辑在身体跟随时也会生效
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

        self.load_physics(filename=filename, max_angle=max_angle, min_angle=min_angle)

    def load_physics(self, filename: str, max_angle=None, min_angle=None):
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

    def _start_assembly(self, live2d_assembly: Live2DAssembly):
        if live2d_assembly.play:
            renpy.music.play(live2d_assembly.play, channel=live2d_assembly.channel)
        # print(f"Start Assembly self.name: {self.name}")
        state = states[self.name]
        # print(self.common.motions)

        from renpy.display.displayable import DisplayableArguments
        old_args = DisplayableArguments()
        old_args.args = tuple(self.idle_motions + self.idle_exps)
        new_args = DisplayableArguments()
        new_args.args = tuple(live2d_assembly.motions+live2d_assembly.expressions)
        
        if self.new_state is not None:
            state.old = self.new_state
        else:
            state.old = self._duplicate(old_args)

        state.new = self._duplicate(new_args)

        self.old_state = state.old
        self.new_state = state.new

        self.reset_st = self.tmp_st
        state.old_base_time = renpy.display.interface.frame_time - self.tmp_st
        
        self.current_assembly = live2d_assembly


    def _end_assembly(self):
        state = states[self.name]

        state.old = self.new_state
        
        from renpy.display.displayable import DisplayableArguments
        new_args = DisplayableArguments()
        new_args.args = tuple(self.idle_motions + self.idle_exps)
        state.new = self._duplicate(new_args)

        self.old_state = state.old
        self.new_state = state.new

        # self.reset_st = self.tmp_st
        # state.old_base_time = renpy.display.interface.frame_time - self.tmp_st

        self.motions = self.idle_motions
        self.used_nonexclusive = self.idle_exps
        self.current_assembly = None

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
        # print(self.name)
        # state = states[self.name]
        # print(state.new)
        if self.new_state is not self and self.new_state is not None:
            # print("Use New State to Instead")
            return self.new_state.update(common, st, st_fade)

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
            elif kind == "Parameter" :
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

    def render(self, width, height, st, at):

        # 此处有修改
        st-=self.reset_st

        common = self.common
        model = common.model

        # Determine if we should fade.
        fade = self.fade if (self.fade is not None) else renpy.store._live2d_fade

        if not self.name:
            fade = False

        if fade:

            state = states[self.name]

            if state.new is not self:
                fade = False

            if state.new_base_time is None:
                state.new_base_time = renpy.display.interface.frame_time - st

            if state.old is None:
                fade = False
            elif state.old_base_time is None:
                fade = False
            elif state.old.common is not self.common:
                fade = False

        # Reset the parameter, and update.
        # if self.motions[0] != "hiyori_m02":
        model.reset_parameters()

        if fade:
            t = renpy.display.interface.frame_time - state.new_base_time # type: ignore
        else:
            t = st

        ########################
        # 此处有修改
        if self.current_assembly is not None and self.new_state is not None:
            new_redraw = self.new_state.update(common, t, None)
        else:
            new_redraw = self.update(common, t, None)

        if fade:
            # print(f"renpy.display.interface.frame_time:{renpy.display.interface.frame_time} | state.old_base_time: {state.old_base_time} | st: {st} | parsing: {renpy.display.interface.frame_time - state.old_base_time}")
            if self.current_assembly is not None and self.new_state is not None:
                old_redraw = self.old_state.update(common, renpy.display.interface.frame_time - state.old_base_time, st) # type: ignore
            else:
                old_redraw = state.old.update(common, renpy.display.interface.frame_time - state.old_base_time, st) # type: ignore
        else:
            old_redraw = None
        ##########################

        # if self.motions[0] != "hiyori_m02":
        model.finish_parameters()

        # Apply the expressions.
        expression_redraw = self.update_expressions(st)

        # Apply the user-defined update.
        if common.update_function is None:
            user_redraw = None
        else:
            user_redraw = common.update_function(self, st)

        # Determine when to redraw.
        redraws = [ new_redraw, old_redraw, expression_redraw, user_redraw ]
        redraws = [ i for i in redraws if i is not None ]

        if redraws:
            renpy.display.render.redraw(self, min(redraws))

        # Get the textures.
        textures = [ renpy.display.im.render_for_texture(d, width, height, st, at) for d in common.textures ]

        sw, sh = model.get_size()

        zoom = self.zoom

        if zoom is None:
            top = absolute.compute_raw(self.top, sh)
            base = absolute.compute_raw(self.base, sh)

            size = max(base - top, 1.0)

            zoom = 1.0 * self.height * renpy.config.screen_height / size
        else:
            size = sh
            top = 0

        # Render the model.
        rend = model.render(textures, zoom)

        # Apply scaling as needed.
        rv = renpy.exports.Render(sw * zoom, size * zoom)
        rv.blit(rend, (0, -top * zoom))

        return rv
        # return render
        
    def event(self, ev, x, y, st):

        self.mouse_pos = (x, y)
        self.tmp_st = st

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
                    if live2d_assembly.is_triggered():
                        live2d_assembly.st = st
                        self._start_assembly(live2d_assembly)
            else:
                if live2d_assembly is self.hovered_assembly:
                    if hasattr(store, "default_mouse"):
                        del store.default_mouse
                    if live2d_assembly.unhovered:
                        live2d_assembly.unhovered(live2d_assembly)
                    self.hovered_assembly = None

        # 这里直接设置了一个 2 秒自动关闭 assembly
        if self.current_assembly is not None and self.current_assembly.st + 2.0 < st:
            self._end_assembly()

        # print(x, y)
