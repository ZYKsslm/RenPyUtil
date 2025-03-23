#* Positioner - 一个开源的 Ren'Py 定位工具
#* 作者 ZYKsslm
#! 开源协议 MIT
#* 感谢 Feniks @ feniksdev.com 提供的非常实用的开源工具 color_picker


python early:
    import pygame

    class Positioner(renpy.Displayable):
        def __init__(self, name="", size=(100, 100), color=Color("#00d9ff", alpha=0.7), image="", **properties):
            super().__init__(**properties)
            self._name = name
            self._name_color = Color("#e5ff00")
            self.name_displayable = Text(str(name), color=self.name_color)
            self._size = size   # 大小
            self._zoom = (1.0, 1.0)  # 图像缩放比例
            self._color = color
            self._image = image
            self.opacity = 1.0
            self.image_displayable = renpy.displayable(image) if image else None
            self._pos = (0, 0)  # 左上角顶点的坐标
            self._relative_size = (0, 0)
            self.rect = (*self.pos, *self.size)
            self.pressed = False
            self.lock = False
            self.follow_mouse = False
            self.show = True

        @property
        def pos(self):
            return self._pos

        @pos.setter
        def pos(self, value):
            self._pos = value
            self.rect = (*self.pos, *self.size)
            self._update_display()

        @property
        def size(self):
            return (round(self._size[0], 2), round(self._size[1], 2))

        @size.setter
        def size(self, value):
            self._size = value
            self.rect = (*self.pos, *self.size)
            self._update_display()

        @property
        def zoom(self):
            return self._zoom

        @zoom.setter
        def zoom(self, value):
            self._zoom = value
            self._update_display()

        @property
        def color(self):
            return self._color

        @color.setter
        def color(self, value):
            self._color = Color(color=value.hexcode, alpha=0.7)
            self._update_display()

        @property
        def image(self):
            return self._image

        @image.setter
        def image(self, value):
            self._image = value
            self._update_display()

        @property
        def name(self):
            return self._name

        @name.setter
        def name(self, value):
            self._name = value
            self.name_displayable = Text(str(value), color=self.name_color)
            self._update_display()

        @property
        def name_color(self):
            return self._name_color

        @name_color.setter
        def name_color(self, value):
            self._name_color = value
            self.name_displayable = Text(str(self.name), color=self.name_color)
            self._update_display()

        def _update_display(self):
            renpy.redraw(self, 0)
            renpy.restart_interaction()

        def reset(self):
            if self.image:
                self.zoom = (1.0, 1.0)
            else:
                self.size = (100, 100)
            
            self.opacity = 1.0

            self._update_display()

        def modify(self, factor, x=True, y=True):
            if self.image:
                if x:
                    self.zoom = (self.zoom[0] * factor, self.zoom[1])
                if y:
                    self.zoom = (self.zoom[0], self.zoom[1] * factor)
            else:
                if x:
                    self.size = (self.size[0] * factor, self.size[1])
                if y:
                    self.size = (self.size[0], self.size[1] * factor)

        def plus(self, x=True, y=True):
            self.modify(1.1, x, y)

        def minus(self, x=True, y=True):
            self.modify(0.9, x, y)

        def render(self, width, height, st, at):
            render = renpy.Render(width, height)
            if self.show:
                if self.image:
                    self.image_displayable = Transform(renpy.displayable(self.image), alpha=self.opacity, xzoom=self.zoom[0], yzoom=self.zoom[1])
                    image_render = renpy.render(self.image_displayable, width, height, st, at)
                    render.blit(image_render, self.pos)
                    self.size = image_render.get_size()
                else:
                    canvas = render.canvas()
                    self.color = self.color.replace_opacity(self.opacity)
                    canvas.rect(self.color, (*self.pos, *self._size))
                if self.name:
                    name_render = renpy.render(self.name_displayable, width, height, st, at)
                    render.blit(name_render, self.pos)
            return render

        def event(self, ev, x, y, st):
            if self.lock:
                return
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    if self.rect[0] <= x <= self.rect[0] + self.rect[2] and self.rect[1] <= y <= self.rect[1] + self.rect[3]:
                        self._relative_size = (x - self.pos[0], y - self.pos[1])
                    self.pressed = True
                elif ev.button == 4:
                    self.plus()
                elif ev.button == 5:
                    self.minus()

            elif ev.type == pygame.MOUSEBUTTONUP:
                self.pressed = False
                self._relative_size = (0, 0)

            if self.pressed or self.follow_mouse:
                if self.pressed:
                    self.follow_mouse = False
                self.pos = (x - self._relative_size[0], y - self._relative_size[1])
                renpy.restart_interaction()
                
            renpy.redraw(self, 0)

    class PositionerGroup(renpy.Displayable):
        def __init__(self, *positioners, **properties):
            super().__init__(**properties)
            self.positioners = list(positioners)
            if not self.positioners:
                self.create()
            else:
                self.selected_positioner = self.positioners[-1]

        def create(self, *args, **kwargs):
            positioner = Positioner(*args, **kwargs)
            self.positioners.append(positioner)
            self.selected_positioner = positioner
            renpy.redraw(self, 0)

        def remove(self, positioner):
            self.positioners.remove(positioner)
            if not self.positioners:
                self.create()
            self.selected_positioner = self.positioners[-1]
            renpy.redraw(self, 0)
        
        def render(self, width, height, st, at):
            render = renpy.Render(width, height)
            for positioner in self.positioners:
                render.blit(positioner.render(width, height, st, at), (0, 0))
            
            return render

        def event(self, ev, x, y, st):
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for positioner in self.positioners:
                    area = (*positioner.pos, *positioner.size)
                    if area[0] <= x <= area[0] + area[2] and area[1] <= y <= area[1] + area[3]:
                        self.selected_positioner = positioner
                        renpy.restart_interaction()
            
            self.selected_positioner.event(ev, x, y, st)
            renpy.redraw(self, 0)
        
        def visit(self):
            return self.positioners

screen color_picker(obj, field, default_color):
    modal True
    style_prefix 'cpicker'

    default picker = ColorPicker(500, 500, default_color)
    default picker_swatch = DynamicDisplayable(picker_color, picker=picker, xsize=100, ysize=100)
    default picker_hex = DynamicDisplayable(picker_hexcode, picker=picker)
    
    label "{i}color_picker{/i} 工具由 {u}@ feniksdev.com{/u} 提供"
    hbox:
        vbar value FieldValue(picker, "hue_rotation", 1.0)
        vbox:
            add picker
            bar value FieldValue(picker, "hue_rotation", 1.0)
        vbox:
            xsize 200 spacing 10 align (0.0, 0.0)
            add picker_swatch
            add picker_hex
            textbutton "完成" action [SetField(obj, field, picker.color), Return()]

style cpicker_vbox:
    align (0.5, 0.5)
    spacing 25
style cpicker_hbox:
    align (0.5, 0.5)
    spacing 25
style cpicker_vbar:
    xysize (50, 500)
    base_bar At(Transform("#000", xysize=(50, 500)), spectrum(horizontal=False))
    thumb Transform("selector_bg", xysize=(50, 20))
    thumb_offset 10
style cpicker_bar:
    xysize (500, 50)
    base_bar At(Transform("#000", xysize=(500, 50)), spectrum())
    thumb Transform("selector_bg", xysize=(20, 50))
    thumb_offset 10
style cpicker_text:
    color "#fff"
style cpicker_button:
    padding (4, 4) insensitive_background "#fff"
style cpicker_button_text:
    color "#aaa"
    hover_color "#fff"
style cpicker_image_button:
    xysize (104, 104)
    padding (4, 4)
    hover_foreground "#fff2"


screen change_positioner_image(positioner):
    default notice_value = FieldInputValue(positioner, "image")

    frame:
        xysize (850, 500)
        align (0.5, 0.5)

        hbox:
            align (0.5, 0.5)
            spacing 10

            vbox:
                spacing 10
                xysize (400, 350)
                label "手动输入:" align (0.5, 0.0)
                input:
                    align (0.5, 0.5)
                    pixel_width 390
                    multiline True
                    copypaste True
                    value notice_value
            vbox:
                spacing 10
                xysize (400, 350)
                label "选择图像：" align (0.5, 0.0)
                viewport:
                    xysize (400, 350)
                    align (0.5, 0.5)
                    mousewheel True
                    draggable True
                    scrollbars "vertical"

                    vbox:
                        xysize (400, 350)
                        spacing 10
                        for image in renpy.list_images():
                            textbutton "[image]":
                                xalign 0.5
                                action SetField(positioner, "image", image)
            
        textbutton "完成" align (0.5, 0.99) action Return()

screen change_positioner_name(positioner):
    default notice_value = FieldInputValue(positioner, "name")

    frame:
        xysize (500, 300)
        align (0.5, 0.5)

        label "请输入名称:" align (0.5, 0.15)
        input:
            align (0.5, 0.5)
            pixel_width 390
            multiline True
            copypaste True
            value notice_value

        hbox:
            spacing 100
            align (0.5, 0.75)
            textbutton "颜色" action ShowMenu("color_picker", obj=positioner, field="name_color", default_color=positioner.name_color)
            textbutton "完成" action Return()

screen position_helper(*displayables):
    default positioner_group = PositionerGroup()
    default show_menu = True
    $ positioner = positioner_group.selected_positioner
    
    for displayable in displayables:
        add displayable

    add positioner_group

    if show_menu:
        use positioner(positioner, positioner_group)
    
    key "v" action ToggleScreenVariable("show_menu")

screen positioner(positioner, positioner_group):
    drag:
        align (0.02, 0.1)
        draggable True
        frame:
            background Color("#ffffff", alpha=0.3)
            has vbox
            spacing 20
        
            label "当前参数"
            label "[positioner.rect]"
            label "x&y轴"
            textbutton "放大" action Function(positioner.plus)
            textbutton "缩小" action Function(positioner.minus)
            textbutton "重置" action Function(positioner.reset)
            label "x轴"
            textbutton "放大" action Function(positioner.plus, y=False)
            textbutton "缩小" action Function(positioner.minus, y=False)
            label "y轴"
            textbutton "放大" action Function(positioner.plus, x=False)
            textbutton "缩小" action Function(positioner.minus, x=False)
            label "透明度"
            bar:
                xsize 250
                value FieldValue(positioner, "opacity", 1.0)
    
    drag:
        align (0.98, 0.1)
        draggable True
        frame:
            background Color("#ffffff", alpha=0.3)
            has vbox
            spacing 20

            label "状态"
            hbox:
                spacing 5
                text "名称："
                add positioner.name_displayable
            text "位置: [positioner.pos]"
            text "大小: [positioner.size]"
            label "操作"
            textbutton "添加图片" action ShowMenu("change_positioner_image", positioner=positioner)
            textbutton "锁定/解锁" action ToggleField(positioner, "lock")
            textbutton "显示/隐藏" action ToggleField(positioner, "show")
            textbutton "跟随/取消" action ToggleField(positioner, "follow_mouse")
            textbutton "修改定位器名称" action ShowMenu("change_positioner_name", positioner=positioner)
            textbutton "修改定位器颜色" action ShowMenu("color_picker", obj=positioner, field="color", default_color=positioner.color)
            textbutton "创建定位器" action Function(positioner_group.create)
            textbutton "删除定位器" action Function(positioner_group.remove, positioner)
