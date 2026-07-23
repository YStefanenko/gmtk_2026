from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
import numpy as np
import math
import time
import sys


class OpenglManager:
    def __init__(self):
        # REMEMBER THIS!!!
        self.map_size = np.array([1600, 900])
        self.inv_map_size = np.array([1600, -900])

        # Standard size:
        self.screen_size = np.array([0, 0])
        self.screen_offset = np.array([0, 0])

        self.shaders = []
        self.shader_buffer = None
        self.shader_buffer_texture = None
        self.shader_number = 0

        self.control_text = "TeaAndPython's secret text (don't even dare read this)"
        self.reference_width = 1979

        self.textures = {}

        self.rendered_text = {}

    def create_screen(self):
        pygame.display.gl_set_attribute(pygame.GL_ACCELERATED_VISUAL, 1)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)

        if sys.platform == "darwin":
            # (0,0) auto-size is unreliable on macOS — size explicitly
            info = pygame.display.Info()
            size = (info.current_w, info.current_h)
        else:
            # Original behaviour: let SDL size to the active display
            size = (0, 0)

        pygame.display.set_mode(size, pygame.OPENGL | pygame.DOUBLEBUF | pygame.NOFRAME, vsync=1)

        screen = pygame.display.get_surface()
        win_w, win_h = screen.get_size()

        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)

        # Retina: GL drawable is physical pixels, mouse events are logical points.
        # Clamped so Windows display scaling (125%, 150%) always yields 1.0.
        if sys.platform == "darwin":
            fb_w, _ = pygame.display.get_window_size()
            raw_scale = fb_w / win_w if win_w else 1.0
            self.pixel_scale = 2.0 if raw_scale >= 1.9 else 1.0
        else:
            self.pixel_scale = 1.0

        # Calculate centered 16:9 viewport inside actual screen
        screen_aspect = win_w / win_h
        target_aspect = 16 / 9

        if screen_aspect >= target_aspect:
            # Screen is wider than 16:9 — letterbox (black bars left/right)
            view_h = win_h
            view_w = int(view_h * target_aspect)
        else:
            # Screen is taller than 16:9 — pillarbox (black bars top/bottom)
            view_w = win_w
            view_h = int(view_w / target_aspect)

        view_x = (win_w - view_w) // 2
        view_y = (win_h - view_h) // 2

        # Set OpenGL viewport to just the 16:9 area (in physical pixels)
        glViewport(
            int(view_x * self.pixel_scale),
            int(view_y * self.pixel_scale),
            int(view_w * self.pixel_scale),
            int(view_h * self.pixel_scale),
        )

        # Set up 2D projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, 1, 0, 1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Enable alpha blending for transparent images
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_FASTEST)

        # Keep in logical points so these match pygame mouse event coordinates
        self.screen_size = np.array([view_w, view_h])
        self.screen_offset = np.array([view_x, view_y])

        self.load_shaders()

        # Calibrate text
        try:
            f = pygame.font.SysFont("Arial", 100)
        except TypeError:
            f = pygame.font.Font(pygame.font.get_default_font(), 100)

        local_width = f.size(self.control_text)[0]

        if self.reference_width and local_width:
            self.text_scale = self.reference_width / local_width
        else:
            self.text_scale = 1.0

    def clear_images(self):
        glDeleteTextures(list(self.textures.values()))
        self.textures = {}
        self.rendered_text = {}

    def delete_image(self, name):
        glDeleteTextures([self.textures[name]])
        del self.textures[name]

    def load_image(self, name, image_path):
        surface = pygame.image.load(image_path).convert_alpha()
        width, height = surface.get_size()
        image_data = pygame.image.tostring(surface, "RGBA", True)
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        try:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        except GLError:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, image_data)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.textures[name] = texture_id

    def draw_image(self, name, position, size, alpha=None, direction=None):
        if alpha is not None:
            glColor4f(1.0, 1.0, 1.0, alpha)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        texture_id = self.textures[name]
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        glBegin(GL_QUADS)
        if direction is None:
            glTexCoord2f(0, 0);
            glVertex2f(position[0] - size[0] / 2, position[1] - size[1] / 2)
            glTexCoord2f(1, 0);
            glVertex2f(position[0] + size[0] / 2, position[1] - size[1] / 2)
            glTexCoord2f(1, 1);
            glVertex2f(position[0] + size[0] / 2, position[1] + size[1] / 2)
            glTexCoord2f(0, 1);
            glVertex2f(position[0] - size[0] / 2, position[1] + size[1] / 2)
        else:
            position = np.asarray(position, dtype=float)
            aspect = self.screen_size[0] / self.screen_size[1]  # 16/9
            scale = np.array([aspect, 1.0])  # coord -> physical

            d = np.asarray(direction, dtype=float)
            d = d / np.linalg.norm(d)  # unit on-screen direction
            perp = np.array([-d[1], d[0]])

            # build half-edge vectors in physical space, then divide back into coord space
            w_vec = (size[0] * aspect / 2 * d) / scale
            h_vec = (size[1] / 2 * perp) / scale

            glTexCoord2f(0, 0);
            glVertex2f(*(position - w_vec - h_vec))
            glTexCoord2f(1, 0);
            glVertex2f(*(position + w_vec - h_vec))
            glTexCoord2f(1, 1);
            glVertex2f(*(position + w_vec + h_vec))
            glTexCoord2f(0, 1);
            glVertex2f(*(position - w_vec + h_vec))

        glEnd()
        glDisable(GL_TEXTURE_2D)
        glPopMatrix()
        glColor4f(1.0, 1.0, 1.0, 1.0)

    def clear_screen(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def convert_mouse(self, mouse):
        mouse = (mouse - self.screen_offset) / self.screen_size
        mouse[1] = 1 - mouse[1]
        mouse = np.clip(mouse, 0, 1)
        return mouse

    def draw_lines(self, points, color, width, loop=False):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glColor4f(*color)

        width = width / 864 * self.screen_size[1]

        if width != 0:
            glLineWidth(width)
        if loop and width:
            glBegin(GL_LINE_LOOP)
        elif width == 0:
            glBegin(GL_POLYGON)
        else:
            glBegin(GL_LINE_STRIP)

        for point in points:
            glVertex2f(point[0], point[1])
        glEnd()
        glColor4f(1.0, 1.0, 1.0, 1.0)

    def draw_polygon(self, points, color):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glColor4f(*color)
        glBegin(GL_POLYGON)
        for point in points:
            glVertex2f(point[0], point[1])
        glEnd()
        glColor4f(1.0, 1.0, 1.0, 1.0)

    def draw_circle(self, position, radius, color, width=0):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glColor4f(*color)
        if width == 0:
            glBegin(GL_TRIANGLE_FAN)
            glVertex2f(position[0], position[1])
            for i in range(33):
                angle = 2 * 3.1415926 * i / 32
                dx = math.cos(angle) * radius
                dy = math.sin(angle) * radius * 16 / 9
                glVertex2f(position[0] + dx, position[1] + dy)
            glEnd()
        else:
            glLineWidth(width)
            glBegin(GL_LINE_LOOP)
            for i in range(32):
                angle = 2 * 3.1415926 * i / 32
                dx = math.cos(angle) * radius
                dy = math.sin(angle) * radius * 16 / 9
                glVertex2f(position[0] + dx, position[1] + dy)
            glEnd()
        glColor4f(1.0, 1.0, 1.0, 1.0)

    def load_pygame_surface(self, name, surface):
        surface = surface.convert_alpha()
        width, height = surface.get_size()
        image_data = pygame.image.tostring(surface, "RGBA", True)
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        try:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        except GLError:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, image_data)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.textures[name] = texture_id

    def generate_mipmaps(self, name):
        texture_id = self.textures[name]
        glBindTexture(GL_TEXTURE_2D, texture_id)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)

        glGenerateMipmap(GL_TEXTURE_2D)

    def draw_map_section(self, name, cam):
        texture_id = self.textures[name]
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        u1 = max(0, (cam[0] - 960) / 5045)
        v1 = max(0, (cam[1] - 540) / 5045)
        u2 = min(1, (cam[0] + 960) / 5045)
        v2 = min(1, (cam[1] + 540) / 5045)

        glBegin(GL_QUADS)
        glTexCoord2f(u1, v2);
        glVertex2f(0, 0)
        glTexCoord2f(u2, v2);
        glVertex2f(1, 0)
        glTexCoord2f(u2, v1);
        glVertex2f(1, 1)
        glTexCoord2f(u1, v1);
        glVertex2f(0, 1)
        glEnd()

        glDisable(GL_TEXTURE_2D)

    def save_screen(self):
        pixels = glReadPixels(self.screen_offset[0], self.screen_offset[1], self.screen_size[0], self.screen_size[1],
                              GL_RGBA, GL_UNSIGNED_BYTE)
        surface = pygame.image.fromstring(pixels, self.screen_size, "RGBA")
        surface = pygame.transform.flip(surface, False, True)
        return surface

    def load_text(self, text, color, size, position, name, outline=0, outline_color=(0, 0, 0), fix=None, width_limit=1, font=None, direction=None):

        px_size = max(1, int(round(size * self.screen_size[1] / 864)))

        font = pygame.font.Font("./assets/ari-w9500.ttf", px_size)

        base = font.render(text, True, color)
        text_size = base.get_size()

        if outline:
            thickness = outline
            width = text_size[0] + thickness * 2
            height = text_size[1] + thickness * 2
            text_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            outline_render = font.render(text, True, outline_color)

            if outline > 3:
                for angle in range(0, 360, 15):
                    dx = int(math.cos(math.radians(angle)) * thickness) + thickness
                    dy = int(math.sin(math.radians(angle)) * thickness) + thickness
                    text_surface.blit(outline_render, (dx, dy))
            else:
                for dx, dy in [(-thickness, 0), (thickness, 0), (0, -thickness), (0, thickness),
                               (-thickness, -thickness), (-thickness, thickness), (thickness, -thickness),
                               (thickness, thickness)]:
                    text_surface.blit(outline_render, (dx + thickness, dy + thickness))

            text_surface.blit(base, (thickness, thickness))
        else:
            text_surface = base

        # Trim the transparent padding so the texture hugs the actual glyphs.
        crop = text_surface.get_bounding_rect(min_alpha=1)
        if crop.width and crop.height:
            text_surface = text_surface.subsurface(crop).copy()

        px_w, px_h = text_surface.get_size()

        self.load_pygame_surface(name, text_surface)

        norm_h = px_h / self.screen_size[1]
        norm_w = px_w * self.text_scale / self.screen_size[0]
        if norm_w > width_limit:
            norm_w = width_limit

        text_size = (norm_w, norm_h)

        if fix == 'left':
            position = (position[0] + text_size[0] / 2, position[1])
        elif fix == 'right':
            position = (position[0] - text_size[0] / 2, position[1])

        self.rendered_text[name] = [name, position, text_size, direction]

    def move_text(self, name, position, fix=None):
        if fix == 'left':
            position = (position[0] + self.rendered_text[name][2][0] / 2, position[1])
        elif fix == 'right':
            position = (position[0] - self.rendered_text[name][2][0] / 2, position[1])

        self.rendered_text[name][1] = position

    def draw_text(self, name, alpha=None):
        self.draw_image(self.rendered_text[name][0], self.rendered_text[name][1], self.rendered_text[name][2],
                        alpha=alpha, direction=self.rendered_text[name][3])

    def update_texture(self, texture, name):
        height, width = texture.shape[:2]
        flipped = np.flipud(texture)
        if name in self.textures:
            texture_id = self.textures[name]
        else:
            texture_id = glGenTextures(1)
            self.textures[name] = texture_id
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, flipped)

    def zoom(self, scale, center, offset):
        glTranslatef(center[0], center[1], 0.0)
        glScalef(scale, scale, 1.0)
        glTranslatef(-center[0], -center[1], 0.0)

        glTranslatef(-offset[0], -offset[1], 0.0)

    def load_shaders(self):
        def compile_one(src, shader_type):
            shader = glCreateShader(shader_type)
            glShaderSource(shader, src)
            glCompileShader(shader)
            if not glGetShaderiv(shader, GL_COMPILE_STATUS):
                raise RuntimeError(glGetShaderInfoLog(shader))
            return shader

        def compile_two(vs_src, fs_src):
            program = glCreateProgram()
            vs = compile_one(vs_src, GL_VERTEX_SHADER)
            fs = compile_one(fs_src, GL_FRAGMENT_SHADER)

            glAttachShader(program, vs)
            glAttachShader(program, fs)
            glLinkProgram(program)

            if not glGetProgramiv(program, GL_LINK_STATUS):
                raise RuntimeError(glGetProgramInfoLog(program))

            glDeleteShader(vs)
            glDeleteShader(fs)
            return program

        w, h = self.screen_size

        # Framebuffer
        self.shader_buffer = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.shader_buffer)

        self.shader_buffer_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.shader_buffer_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, None)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.shader_buffer_texture, 0)

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("FBO incomplete")

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        vert_shader = """
        #version 120
        void main() {
            gl_TexCoord[0] = gl_MultiTexCoord0;
            gl_Position = ftransform();
        }
        """

        frag_shader = """
        #version 120
        uniform sampler2D screen;
        uniform vec2 texel;

        void main() {
            vec2 uv = gl_TexCoord[0].st;

            vec3 c = texture2D(screen, uv).rgb;

            float diff = 0.0;
            for (int x = -1; x <= 1; x++) {
                for (int y = -1; y <= 1; y++) {
                    if (x == 0 && y == 0) continue;
                    vec3 n = texture2D(screen, uv + vec2(x, y) * texel).rgb;
                    diff = max(diff, length(c - n));
                }
            }

            if (diff > 0.25)
                gl_FragColor = vec4(0, 0, 0, 1);
            else
                gl_FragColor = vec4(c, 1);
        }
        """

        invert_shader = """
        #version 120
        uniform sampler2D screen;

        void main() {
            vec3 c = texture2D(screen, gl_TexCoord[0].st).rgb;
            gl_FragColor = vec4(1.0 - c, 1);
        }
        """

        pixelation_shader = """
        #version 120
        uniform sampler2D screen;
        uniform vec2 texel; // size of one pixel in normalized UVs

        void main() {
            vec2 uv = gl_TexCoord[0].st;

            float px = 180.0; // number of square blocks along height
            float aspect = 16.0 / 9.0; // screen aspect ratio

            // scale UVs so blocks are square in screen space
            vec2 scaledUV = uv;
            scaledUV.x *= aspect;

            // floor to pixel grid
            scaledUV = floor(scaledUV * px) / px;

            // undo scaling
            scaledUV.x /= aspect;

            vec3 color = texture2D(screen, scaledUV).rgb;
            gl_FragColor = vec4(color, 1);
        }
        """

        rgb_shift_shader = """
        #version 120
        uniform sampler2D screen;
        uniform vec2 texel;

        void main() {
            vec2 uv = gl_TexCoord[0].st;

            float offset = 0.005;
            float r = texture2D(screen, uv + vec2(offset,0)).r;
            float g = texture2D(screen, uv).g;
            float b = texture2D(screen, uv - vec2(offset,0)).b;

            gl_FragColor = vec4(r, g, b, 1);
        }
        """

        vignette_shader = """
        #version 120
        uniform sampler2D screen;

        void main() {
            vec2 uv = gl_TexCoord[0].st;
            vec2 center = vec2(0.5, 0.5);

            float dist = distance(uv, center);
            float factor = smoothstep(0.8, 0.5, dist);

            vec3 color = texture2D(screen, uv).rgb * factor;
            gl_FragColor = vec4(color, 1);
        }
        """

        noise_shader = """
        #version 120
        uniform sampler2D screen;
        uniform float time;

        float rand(vec2 co){
            // scale co to a reasonable range
            return fract(sin(dot(co * 12.9898, vec2(78.233, 37.719))) * 43758.5453);
        }

        void main() {
            vec2 uv = gl_TexCoord[0].st;

            vec3 color = texture2D(screen, uv).rgb;

            float noise = rand(uv + vec2(time * 0.05 / 100000.0, time * 0.05 / 100000.0));

            // add small noise, clamp to [0,1]
            color += vec3(noise * 0.2);
            color = clamp(color, 0.0, 1.0);

            gl_FragColor = vec4(color, 1);
        }
        """

        wave_shader = """
        #version 120
        uniform sampler2D screen;
        uniform float time;

        void main() {
            vec2 uv = gl_TexCoord[0].st;
            uv.y += 0.03 * sin(uv.x * 30.0 + time / 1000.0);
            uv.x += 0.03 * cos(uv.y * 30.0 + time / 1000.0);

            vec3 color = texture2D(screen, uv).rgb;
            gl_FragColor = vec4(color, 1);
        }
        """

        self.shaders.append(compile_two(vert_shader, frag_shader))
        self.shaders.append(compile_two(vert_shader, wave_shader))
        self.shaders.append(compile_two(vert_shader, noise_shader))
        self.shaders.append(compile_two(vert_shader, vignette_shader))
        self.shaders.append(compile_two(vert_shader, rgb_shift_shader))
        self.shaders.append(compile_two(vert_shader, pixelation_shader))
        self.shaders.append(compile_two(vert_shader, invert_shader))

        # LINE TEXTURE
        _VERT = """
        #version 120
        varying vec2 lineUV;
        void main() {
            lineUV = gl_MultiTexCoord0.xy;
            gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
        }
        """

        _FRAG = """
        #version 120
        varying vec2 lineUV;
        uniform vec3 lineColor;

        float hash(vec2 p) {
            return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
        }
        float noise(vec2 p) {
            vec2 i = floor(p);
            vec2 f = fract(p);
            f = f * f * (3.0 - 2.0 * f);
            return mix(
                mix(hash(i),               hash(i + vec2(1, 0)), f.x),
                mix(hash(i + vec2(0, 1)),  hash(i + vec2(1, 1)), f.x),
                f.y
            );
        }

        void main() {
            float across = lineUV.y;  // -1 … +1 across the stroke

            // Rough, uneven edge using noise on the along-line coordinate
            float edgeNoise = (noise(vec2(lineUV.x * 60.0, 0.5)) - 0.5) * 0.18;
            float edgeDist  = abs(across) + edgeNoise;
            if (edgeDist > 1.0) discard;

            // Soft feathered falloff toward the edges
            float alpha = smoothstep(1.0, 0.55, edgeDist) * 0.88;

            // Worn ink texture variation
            float worn  = noise(vec2(lineUV.x * 30.0, across * 6.0)) * 0.14;
            vec3  color = lineColor * (0.82 + worn);

            // Faint center highlight — like ink slightly raised
            float centerGlow = (1.0 - abs(across) * 0.85) * 0.07;
            color += vec3(centerGlow);

            gl_FragColor = vec4(color, alpha);
        }
        """

        def _compile(src, kind):
            s = glCreateShader(kind)
            glShaderSource(s, src)
            glCompileShader(s)
            if not glGetShaderiv(s, GL_COMPILE_STATUS):
                raise RuntimeError(glGetShaderInfoLog(s).decode())
            return s

        prog = glCreateProgram()
        glAttachShader(prog, _compile(_VERT, GL_VERTEX_SHADER))
        glAttachShader(prog, _compile(_FRAG, GL_FRAGMENT_SHADER))
        glLinkProgram(prog)
        if not glGetProgramiv(prog, GL_LINK_STATUS):
            raise RuntimeError(glGetProgramInfoLog(prog).decode())

        self._line_shader = prog
        self._line_u_color = glGetUniformLocation(prog, "lineColor")

    def start_shader(self, n):
        self.shader_number = n
        w, h = self.screen_size
        glBindFramebuffer(GL_FRAMEBUFFER, self.shader_buffer)
        glViewport(0, 0, w, h)

        glClear(GL_COLOR_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def end_shader(self):
        w, h = self.screen_size
        ox, oy = self.screen_offset

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        glViewport(ox, oy, w, h)

        glClear(GL_COLOR_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, 1, 0, 1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glUseProgram(self.shaders[self.shader_number])

        t_loc = glGetUniformLocation(self.shaders[self.shader_number], "time")
        glUniform1f(t_loc, pygame.time.get_ticks())

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.shader_buffer_texture)
        glUniform1i(glGetUniformLocation(self.shaders[self.shader_number], "screen"), 0)

        glUniform2f(
            glGetUniformLocation(self.shaders[self.shader_number], "texel"),
            1.0 / w,
            1.0 / h
        )

        glBegin(GL_QUADS)
        glTexCoord2f(0, 0);
        glVertex2f(0, 0)
        glTexCoord2f(1, 0);
        glVertex2f(1, 0)
        glTexCoord2f(1, 1);
        glVertex2f(1, 1)
        glTexCoord2f(0, 1);
        glVertex2f(0, 1)
        glEnd()

        glUseProgram(0)

opengl_manager = OpenglManager()
