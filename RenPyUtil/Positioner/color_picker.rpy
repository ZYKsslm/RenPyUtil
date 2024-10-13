################################################################################
##
## Color Picker for Ren'Py by Feniks (feniksdev.itch.io / feniksdev.com)
##
################################################################################
## This file contains code for a colour picker in Ren'Py.
## If you use this code in your projects, credit me as Feniks @ feniksdev.com
##
## If you'd like to see how to use this tool, check the other file,
## color_picker_examples.rpy!
## You can also see this tool in action in the image tint tool, also on itch:
## https://feniksdev.itch.io/image-tint-tool
##
## Leave a comment on the tool page on itch.io or an issue on the GitHub
## if you run into any issues.
## https://feniksdev.itch.io/color-picker-for-renpy
## https://github.com/shawna-p/renpy-color-picker
################################################################################
################################################################################
## SHADERS & TRANSFORMS
################################################################################
init python:
    ## A shader which creates a gradient for a colour picker.
    renpy.register_shader("feniks.color_picker", variables="""
        uniform vec4 u_gradient_top_right;
        uniform vec4 u_gradient_top_left;
        uniform vec4 u_gradient_bottom_left;
        uniform vec4 u_gradient_bottom_right;
        uniform vec2 u_model_size;
        varying float v_gradient_x_done;
        varying float v_gradient_y_done;
        attribute vec4 a_position;
    """, vertex_300="""
        v_gradient_x_done = a_position.x / u_model_size.x;
        v_gradient_y_done = a_position.y / u_model_size.y;
    """, fragment_300="""
        // Mix the two top colours
        vec4 top = mix(u_gradient_top_left, u_gradient_top_right, v_gradient_x_done);
        // Mix the two bottom colours
        vec4 bottom = mix(u_gradient_bottom_left, u_gradient_bottom_right, v_gradient_x_done);
        // Mix the top and bottom
        gl_FragColor = mix(bottom, top, 1.0-v_gradient_y_done);
    """)

    ## A shader which creates a spectrum. Generally for colour pickers.
    renpy.register_shader("feniks.spectrum", variables="""
        uniform float u_lightness;
        uniform float u_saturation;
        uniform float u_horizontal;
        uniform vec2 u_model_size;
        varying float v_gradient_x_done;
        varying float v_gradient_y_done;
        attribute vec4 a_position;
    """, vertex_300="""
        v_gradient_x_done = a_position.x / u_model_size.x;
        v_gradient_y_done = a_position.y / u_model_size.y;
    """, fragment_functions="""
    // HSL to RGB conversion adapted from
    // https://stackoverflow.com/questions/2353211/hsl-to-rgb-color-conversion
    float hue2rgb(float p, float q, float t){
        if(t < 0.0) t += 1.0;
        if(t > 1.0) t -= 1.0;
        if(t < 1.0/6.0) return p + (q - p) * 6.0 * t;
        if(t < 1.0/2.0) return q;
        if(t < 2.0/3.0) return p + (q - p) * (2.0/3.0 - t) * 6.0;
        return p;
    }
    vec3 hslToRgb(float h, float l, float s) {
        float q = l < 0.5 ? l * (1.0 + s) : l + s - l * s;
        float p = 2.0 * l - q;
        float r = hue2rgb(p, q, h + 1.0/3.0);
        float g = hue2rgb(p, q, h);
        float b = hue2rgb(p, q, h - 1.0/3.0);
        return vec3(r, g, b);
    }
    """, fragment_300="""
        float hue = u_horizontal > 0.5 ? v_gradient_x_done : 1.0-v_gradient_y_done;
        vec3 rgb = hslToRgb(hue, u_lightness, u_saturation);
        gl_FragColor = vec4(rgb.r, rgb.g, rgb.b, 1.0);
    """)

## A transform which creates a spectrum.
## If horizontal is True, the spectrum goes from left to right instead of
## top to bottom. You can also adjust the lightness and saturation
## (between 0 and 1).
transform spectrum(horizontal=True, light=0.5, sat=1.0):
    shader "feniks.spectrum"
    u_lightness light
    u_saturation sat
    u_horizontal float(horizontal)

## A transform which creates a square with a gradient. By default, only the
## top right colour is required (to make a colour picker gradient) but four
## corner colours may also be provided clockwise from the top-right.
transform color_picker(top_right, bottom_right="#000", bottom_left="#000",
        top_left="#fff"):
    shader "feniks.color_picker"
    u_gradient_top_right Color(top_right).rgba
    u_gradient_top_left Color(top_left).rgba
    u_gradient_bottom_left Color(bottom_left).rgba
    u_gradient_bottom_right Color(bottom_right).rgba

################################################################################
## CLASSES AND FUNCTIONS
################################################################################
init python:

    import pygame
    class ColorPicker(renpy.Displayable):
        """
        A CDD which allows the player to pick a colour between four
        corner colours, with the typical setup used for a colour picker.

        Attributes
        ----------
        xsize : int
            The width of the colour picker.
        ysize : int
            The height of the colour picker.
        top_left : Color
            The colour of the top-left corner.
        top_right : Color
            The colour of the top-right corner.
        bottom_left : Color
            The colour of the bottom-left corner.
        bottom_right : Color
            The colour of the bottom-right corner.
        color : Color
            The current colour the colour picker is focused over.
        selector_xpos : float
            The xpos of the colour selector.
        selector_ypos : float
            The ypos of the colour selector.
        picker : Displayable
            A square that is used to display the colour picker.
        hue_rotation : float
            The amount the current hue is rotated by.
        dragging : bool
            True if the indicator is currently being dragged around.
        saved_colors : dict
            A dictionary of key - Color pairs corresponding to colours the
            picker has selected in the past.
        last_saved_color : any
            The dictionary key of the last colour saved.
        mouseup_callback : callable
            An optional callback or list of callbacks which will be called when
            the player lifts their mouse after selecting a colour.
        """
        RED = Color("#f00")
        def __init__(self, xsize, ysize, start_color=None, four_corners=None,
                saved_colors=None, last_saved_color=None, mouseup_callback=None,
                **kwargs):
            """
            Create a ColorPicker object.

            Parameters:
            -----------
            xsize : int
                The width of the colour picker.
            ysize : int
                The height of the colour picker.
            start_color : str
                A hexadecimal colour code corresponding to the starting colour.
            four_corners : tuple(Color, Color, Color, Color)
                A tuple of four colours corresponding to the four corners of the
                colour picker. The order is top right, bottom right, bottom
                left, top left. If this is not None, it will override the
                start_color parameter.
            saved_colors : dict
                A dictionary of key - Color pairs corresponding to colours
                the picker has selected in the past.
            last_saved_color : any
                The dictionary key of the last colour saved.
            mouseup_callback : callable
                An optional callback or list of callbacks which will be called
                when the player lifts their mouse after selecting a colour.
            """
            super(ColorPicker, self).__init__(**kwargs)
            self.xsize = xsize
            self.ysize = ysize

            self.top_left = None
            self.top_right = None
            self.bottom_left = None
            self.bottom_right = None

            self.last_saved_color = last_saved_color
            self.saved_colors = saved_colors or dict()
            self.mouseup_callback = mouseup_callback

            if start_color is None and four_corners is None:
                ## Automatically start with red
                self.set_color("#f00")
            elif four_corners is None:
                self.set_color(start_color)
            else:
                all_corners = [Color(c) if not isinstance(c, Color) else c for c in four_corners]
                self.top_right, self.bottom_right, self.bottom_left, self.top_left = all_corners
                self.set_color(self.top_right)

            self.picker = Transform("#fff", xysize=(self.xsize, self.ysize))
            self.dragging = False

            self.save_color(self.last_saved_color)

        def set_color(self, color):
            """
            Set the current colour of the colour picker.

            Parameters
            ----------
            color : Color
                The new colour to set the colour picker to.
            """
            if not isinstance(color, Color):
                self.color = Color(color)
            else:
                self.color = color
            self.dragging = False

            ## Check if this has four custom corners
            if self.top_left is None:
                ## No; set to saturation/value
                self.selector_xpos = round(self.color.hsv[1]*255.0)/255.0
                self.selector_ypos = 1.0 - round(self.color.hsv[2]*255.0)/255.0
                self._hue_rotation = self.color.hsv[0]
            else:
                ## There isn't a good way to guess the position of a colour
                ## with custom corners, so just set it to the top right
                self.selector_xpos = 1.0
                self.selector_ypos = 0.0
                self._hue_rotation = 0.0

        @property
        def hue_rotation(self):
            """
            The hue rotation of the colour picker.
            """
            return self._hue_rotation

        @hue_rotation.setter
        def hue_rotation(self, value):
            """
            Set the hue rotation of the colour picker.
            """
            if value > 1.0:
                value = value % 1.0
            if round(self._hue_rotation*255.0) == round(value*255):
                return
            self._hue_rotation = value
            self.update_hue()

        def set_saved_color(self, key, new_color):
            """
            Set the colour saved with key as the key to new_color.

            Parameters
            ----------
            key : any
                The key of the colour to change. Must be a valid dictionary key.
            new_color : Color
                The new colour to set the saved colour to.
            """
            if not isinstance(new_color, Color):
                self.saved_colors[key] = Color(new_color)
            else:
                self.saved_colors[key] = new_color

        def save_color(self, key):
            """
            Save the current colour to the saved dictionary with key as the key.
            """
            self.saved_colors[key] = self.color

        def get_color(self, key):
            """
            Retrieve the colour saved in the dictionary with key as the key.
            """
            return self.saved_colors.get(key, Color("#000"))

        def swap_to_saved_color(self, key):
            """
            Swap to the saved colour with key as the key.
            """
            self.set_color(self.saved_colors.get(key, Color("#000")))
            self.last_saved_color = key
            renpy.redraw(self, 0)

        def render(self, width, height, st, at):
            """
            Render the displayable to the screen.
            """
            r = renpy.Render(self.xsize, self.ysize)

            if self.top_left is None:
                trc = self.RED.rotate_hue(self.hue_rotation)
                # Colorize the picker into a gradient
                picker = At(self.picker, color_picker(trc))
            else:
                # Custom four corners; no spectrum sliders
                picker = At(self.picker, color_picker(
                    self.top_right.rotate_hue(self.hue_rotation),
                    self.bottom_right.rotate_hue(self.hue_rotation),
                    self.bottom_left.rotate_hue(self.hue_rotation),
                    self.top_left.rotate_hue(self.hue_rotation)))
            # Position the selector
            selector = Transform("selector", anchor=(0.5, 0.5),
                xpos=self.selector_xpos, ypos=self.selector_ypos)
            final = Fixed(picker, selector, xysize=(self.xsize, self.ysize))
            # Render it to the screen
            ren = renpy.render(final, self.xsize, self.ysize, st, at)
            r.blit(ren, (0, 0))
            return r

        def update_hue(self):
            """
            Update the colour based on the hue in the top-right corner
            (or in all 4 corners).
            """
            # Figure out the colour under the selector
            if self.top_left is None:
                trc = self.RED.rotate_hue(self.hue_rotation)
                tlc = Color("#fff")
                brc = Color("#000")
                blc = Color("#000")
            else:
                tlc = self.top_left.rotate_hue(self.hue_rotation)
                trc = self.top_right.rotate_hue(self.hue_rotation)
                brc = self.bottom_right.rotate_hue(self.hue_rotation)
                blc = self.bottom_left.rotate_hue(self.hue_rotation)

            self.color = tlc.interpolate(trc, self.selector_xpos)
            bottom = blc.interpolate(brc, self.selector_xpos)
            self.color = self.color.interpolate(bottom, self.selector_ypos)
            self.save_color(self.last_saved_color)
            renpy.redraw(self, 0)

        def event(self, ev, x, y, st):
            """Allow the user to drag their mouse to select a colour."""
            relative_x = round(x/float(self.xsize)*255.0)/255.0
            relative_y = round(y/float(self.ysize)*255.0)/255.0

            in_range = (0.0 <= relative_x <= 1.0) and (0.0 <= relative_y <= 1.0)

            if renpy.map_event(ev, "mousedown_1") and in_range:
                self.dragging = True
                self.selector_xpos = relative_x
                self.selector_ypos = relative_y
            elif ev.type == pygame.MOUSEMOTION and self.dragging:
                self.selector_xpos = relative_x
                self.selector_ypos = relative_y
            elif renpy.map_event(ev, "mouseup_1") and self.dragging:
                self.dragging = False
                ## Update the screen
                renpy.restart_interaction()
                if self.mouseup_callback is not None:
                    renpy.run(self.mouseup_callback, self)
                return
            else:
                return

            # Limit x/ypos
            self.selector_xpos = min(max(self.selector_xpos, 0.0), 1.0)
            self.selector_ypos = min(max(self.selector_ypos, 0.0), 1.0)
            self.update_hue()
            return None

    def picker_color(st, at, picker, xsize=100, ysize=100):
        """
        A DynamicDisplayable function to update the colour picker swatch.

        Parameters:
        -----------
        picker : ColorPicker
            The picker this swatch is made from.
        xsize : int
            The width of the swatch.
        ysize : int
            The height of the swatch.
        """
        return Transform(picker.color, xysize=(xsize, ysize)), 0.01

    def picker_hexcode(st, at, picker):
        """
        A brief DynamicDisplayable demonstration of how to display color
        information in real-time.
        """
        return Text(picker.color.hexcode, style='picker_hexcode'), 0.01

################################################################################
## IMAGES
################################################################################
init offset = -1
init python:
    def construct_selector(w=2, sz=5):
        """
        Constructs a white box surrounded by a black box, to use as a
        selector for the colour picker.

        Parameters
        ----------
        w : int
            The width of the lines.
        sz : int
            The size of the inner box.
        """
        ## First, the sides of the box
        box_leftright = [
            Transform("#000", xysize=(w, sz+2*3*w), align=(0.5, 0.5)),
            Transform("#fff", xysize=(w, sz+2*2*w), align=(0.5, 0.5)),
            Transform("#000", xysize=(w, sz+2*1*w), align=(0.5, 0.5)),
        ]
        ## Then the top and bottom
        box_topbottom = [
            Transform("#000", xysize=(sz+2*2*w, w), align=(0.5, 0.5)),
            Transform("#fff", xysize=(sz+2*1*w, w), align=(0.5, 0.5)),
            Transform("#000", xysize=(sz, w), align=(0.5, 0.5)),
        ]
        final_vbox = box_topbottom + [Null(height=sz)] + box_topbottom[::-1]
        final_hbox = (box_leftright + [Null(width=-w*2)]
            + [VBox(*final_vbox, style='empty', spacing=0)]
            + [Null(width=-w*2)] + box_leftright[::-1])
        ## Now put it together
        return HBox(*final_hbox, spacing=0, style='empty')

## These can be changed; see color_picker_examples.rpy for more.
## Feel free to remove the constructor function above if you don't use these.
## Used for both the spectrum thumb and the colour indicator.
image selector_img = construct_selector(2, 3)
image selector_bg = Frame("selector_img", 7, 7)
## The image used for the indicator showing the current colour.
image selector = Transform("selector_bg", xysize=(15, 15))

style picker_hexcode:
    color "#fff"
    font "DejaVuSans.ttf"


