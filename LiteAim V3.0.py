import pygame
import random
import math
import time
import json
import os
import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCORE_FILE = os.path.join(_SCRIPT_DIR, "highscores.json")


def _i16_sample(value, limit):
    v = int(round(value))
    return max(-limit, min(limit, v))


pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
INFO = pygame.display.Info()
WIDTH, HEIGHT = INFO.current_w, INFO.current_h
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("LiteAim V2.0")
CLOCK = pygame.time.Clock()
FPS = 120

COLOR_BG = (20, 20, 30)
COLOR_ACCENT = (0, 255, 200)
COLOR_TEXT = (240, 240, 240)
COLOR_RED = (235, 60, 60)
COLOR_GREEN = (60, 235, 100)
COLOR_ORANGE = (255, 165, 0)
COLOR_BLUE = (50, 150, 255)
COLOR_UI_BG = (40, 40, 50)
COLOR_SHIELD = (150, 150, 255)
COLOR_HEART = (255, 105, 180)
COLOR_PURPLE = (180, 60, 255)
COLOR_LIGHTNING = (255, 240, 80)
COLOR_FLASH = (255, 80, 80)
COLOR_MENU_PANEL = (26, 28, 38)
COLOR_MENU_PANEL_BORDER = (55, 62, 82)
COLOR_MENU_HEADER_BG = (14, 16, 24)

FONT_LG = pygame.font.SysFont("Arial", 60, bold=True)
FONT_MD = pygame.font.SysFont("Arial", 40)
FONT_SM = pygame.font.SysFont("Arial", 24)
FONT_XSM = pygame.font.SysFont("Arial", 18)

HEART_SPAWN_COOLDOWN = 12


def generate_pop_sound():
    sample_rate = 22050
    duration = 0.1
    frequency = 200
    frames = int(duration * sample_rate)
    arr = np.zeros((frames, 2), dtype=np.int16)
    max_sample = 2 ** (16 - 1) - 1
    for i in range(frames):
        t = float(i) / sample_rate
        amplitude = max_sample * math.exp(-35 * t) * math.sin(2 * math.pi * frequency * t)
        s = _i16_sample(amplitude, max_sample)
        arr[i] = [s, s]
    return pygame.sndarray.make_sound(arr)


def generate_shield_break_sound():
    sample_rate = 22050
    duration = 0.15
    frequency = 700
    frames = int(duration * sample_rate)
    arr = np.zeros((frames, 2), dtype=np.int16)
    max_sample = 2 ** (16 - 1) - 1
    for i in range(frames):
        t = float(i) / sample_rate
        amplitude = max_sample * math.exp(-25 * t) * math.sin(2 * math.pi * frequency * t)
        s = _i16_sample(amplitude, max_sample)
        arr[i] = [s, s]
    return pygame.sndarray.make_sound(arr)


def generate_tracking_sound():
    sample_rate = 22050
    duration = 0.05
    frequency = 400
    frames = int(duration * sample_rate)
    arr = np.zeros((frames, 2), dtype=np.int16)
    max_sample = 2 ** (16 - 1) - 1
    for i in range(frames):
        t = float(i) / sample_rate
        amplitude = max_sample * 0.3 * math.sin(2 * math.pi * frequency * t)
        s = _i16_sample(amplitude, max_sample)
        arr[i] = [s, s]
    return pygame.sndarray.make_sound(arr)


def generate_miss_sound():
    sample_rate = 22050
    duration = 0.18
    frequency = 120
    frames = int(duration * sample_rate)
    arr = np.zeros((frames, 2), dtype=np.int16)
    max_sample = 2 ** 15 - 1
    for i in range(frames):
        t = float(i) / sample_rate
        amplitude = max_sample * 0.6 * math.exp(-12 * t) * math.sin(2 * math.pi * frequency * t)
        s = _i16_sample(amplitude, max_sample)
        arr[i] = [s, s]
    return pygame.sndarray.make_sound(arr)

def generate_flash_sound():
    sample_rate = 22050
    duration = 0.06
    frequency = 900
    frames = int(duration * sample_rate)
    arr = np.zeros((frames, 2), dtype=np.int16)
    max_sample = 2 ** 15 - 1
    for i in range(frames):
        t = float(i) / sample_rate
        amplitude = max_sample * 0.4 * math.exp(-40 * t) * math.sin(2 * math.pi * frequency * t)
        s = _i16_sample(amplitude, max_sample)
        arr[i] = [s, s]
    return pygame.sndarray.make_sound(arr)

POP_SOUND = generate_pop_sound()
SHIELD_BREAK_SOUND = generate_shield_break_sound()
TRACKING_SOUND = generate_tracking_sound()
MISS_SOUND = generate_miss_sound()
FLASH_SOUND = generate_flash_sound()


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-5, 5)
        self.color = color
        self.life = 1.0
        self.decay = random.uniform(0.02, 0.05)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        self.vx *= 0.98
        self.vy *= 0.98

    def draw(self, surface):
        if self.life > 0:
            size = max(1, int(3 * self.life))
            pygame.draw.circle(surface, self.color[:3], (int(self.x), int(self.y)), size)


class DataManager:
    @staticmethod
    def load_scores():
        if not os.path.exists(SCORE_FILE):
            return {}
        try:
            with open(SCORE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            return {}

    @staticmethod
    def save_score(mode, score):
        data = DataManager.load_scores()
        if score > data.get(mode, 0):
            data[mode] = score
            try:
                with open(SCORE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
            except OSError:
                return False
            return True
        return False


class Button:
    def __init__(self, x, y, w, h, text, action_code, subtitle=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action_code
        self.subtitle = subtitle
        self.hovered = False

    def draw(self, surface):
        if self.subtitle is not None:
            bg = (40, 44, 58) if not self.hovered else COLOR_ACCENT
            border = (90, 96, 120) if not self.hovered else (180, 255, 235)
            title_col = COLOR_TEXT if not self.hovered else (12, 18, 16)
            sub_col = (145, 150, 170) if not self.hovered else (25, 45, 40)
            pygame.draw.rect(surface, bg, self.rect, border_radius=10)
            pygame.draw.rect(surface, border, self.rect, 2, border_radius=10)
            t1 = FONT_SM.render(self.text, True, title_col)
            t2 = FONT_XSM.render(self.subtitle, True, sub_col)
            gap = 3
            stack_h = t1.get_height() + gap + t2.get_height()
            ty = self.rect.centery - stack_h // 2
            surface.blit(t1, (self.rect.centerx - t1.get_width() // 2, ty))
            surface.blit(t2, (self.rect.centerx - t2.get_width() // 2, ty + t1.get_height() + gap))
            return
        color = COLOR_ACCENT if self.hovered else COLOR_UI_BG
        text_color = (0, 0, 0) if self.hovered else COLOR_TEXT
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=8)
        txt_surf = FONT_SM.render(self.text, True, text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)

    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)


class Slider:
    def __init__(self, x, y, w, min_val, max_val, current, label, decimals=1):
        self.rect = pygame.Rect(x, y, w, 20)
        self.min = min_val
        self.max = max_val
        self.val = current
        self.label = label
        self.decimals = decimals
        self.dragging = False
        self.handle_rect = pygame.Rect(0, y - 5, 10, 30)
        self.update_handle()

    def update_handle(self):
        ratio = (self.val - self.min) / (self.max - self.min)
        self.handle_rect.centerx = self.rect.x + (self.rect.width * ratio)

    def update(self, mouse_pos, click_held):
        if (self.handle_rect.collidepoint(mouse_pos) or self.rect.collidepoint(mouse_pos)) and click_held:
            self.dragging = True
        if not click_held:
            self.dragging = False
        if self.dragging:
            rel_x = mouse_pos[0] - self.rect.x
            ratio = max(0, min(1, rel_x / self.rect.width))
            self.val = self.min + (self.max - self.min) * ratio
            if self.decimals is not None:
                self.val = round(self.val, int(self.decimals))
            self.update_handle()
        return self.val

    def draw(self, surface):
        if self.decimals is None:
            val_text = f"{self.label}: {self.val}"
        else:
            val_text = f"{self.label}: {self.val:.{int(self.decimals)}f}"
        val_surf = FONT_SM.render(val_text, True, COLOR_TEXT)
        surface.blit(val_surf, (self.rect.x, self.rect.y - 30))
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=5)
        pygame.draw.rect(surface, COLOR_ACCENT, self.handle_rect, border_radius=5)


class Game:
    def __init__(self):
        self.state = "MENU"
        self.running = True
        self.virtual_mouse = [WIDTH // 2, HEIGHT // 2]
        self.sensitivity = 1.0
        self.difficulty = 2
        self.volume = 0.5
        self.particles = []

        self.crosshair_style = "dot"   # dot | classic | cross | gap
        self.crosshair_color = COLOR_ACCENT
        self.crosshair_size = 12
        self.crosshair_width = 2
        self.crosshair_gap = 4

        # Crosshair menu sliders (initialised later after we know layout)
        self.ch_size_slider = None
        self.ch_width_slider = None
        self.ch_gap_slider = None

        self.slider = Slider(WIDTH // 2 - 150, HEIGHT - 200, 300, 0.1, 5.0, 1.0, "Sensitivity", decimals=2)
        self.volume_slider = Slider(WIDTH // 2 - 150, HEIGHT - 152, 300, 0.0, 1.0, 0.5, "Volume", decimals=2)

        cols, rows = 3, 3
        cw, ch = 208, 78
        gx, gy = 12, 12
        grid_w = cols * cw + (cols - 1) * gx
        ox = WIDTH // 2 - grid_w // 2
        # Keep grid clear of header + highscore lines (see draw_menu)
        _grid_top_min = 112 + 52 + 14
        oy = max(min(int(HEIGHT * 0.24), 190), _grid_top_min)

        mode_specs = [
            ("Reflex", "Single target click", "START_1"),
            ("Tracking", "Stay on the ball", "START_2"),
            ("Gridshot", "Many static dots", "START_3"),
            ("Micro-flick", "Hub then flick", "START_4"),
            ("Target switch", "Drain moving HP", "START_5"),
            ("Pressure", "Lanes & lives", "START_6"),
            ("Angle holder", "Boxed track", "START_7"),
            ("Flash flick", "Reach safe zones", "START_8"),
            ("Vertex flick", "Track the triangle", "START_9"),
        ]
        self.buttons = []
        for i, (title, sub, act) in enumerate(mode_specs):
            c, r = i % cols, i // cols
            x = ox + c * (cw + gx)
            y = oy + r * (ch + gy)
            self.buttons.append(Button(x, y, cw, ch, title, act, subtitle=sub))

        diff_y = HEIGHT - 286
        foot_y = HEIGHT - 84
        self.buttons.extend([
            Button(WIDTH // 2 - 118, diff_y, 236, 38, "Difficulty: Medium", "TOGGLE_DIFF"),
            Button(WIDTH // 2 - 218, foot_y, 196, 46, "Crosshair", "CROSSHAIR"),
            Button(WIDTH // 2 + 22, foot_y, 196, 46, "Exit", "EXIT"),
        ])

        self.targets = []
        self.score = 0
        self.start_time = 0
        self.is_high_score = False
        self.hits = 0
        self.total_clicks = 0
        self.micro_state = 0
        self.m4_hover_start = None
        self.lives = 3
        self.last_spawn = 0
        self.last_dir_change = 0
        self.base_fall_speed = 200
        self.speed_multiplier = 1.0
        self.last_life_count = 3
        self.last_heart_spawn = 0
        self.last_reverser_spawn = 0
        self.last_angle = 0
        self.last_tracking_sound = 0
        self.mouse_held = False
        self._hud_cache = None
        self._hud_cache_key = None
        self._last_mode = "MODE1"

        # Mode 7 – Angle Holder
        self.m7_box_x = WIDTH // 2 - 80
        self.m7_box_y = HEIGHT // 2 - 150
        self.m7_box_w = 160
        self.m7_box_h = 300

        # Mode 8 – Flash Flick
        self.m8_flash_active = False
        self.m8_flash_pos = (WIDTH // 2, HEIGHT // 2)
        self.m8_flash_born = 0.0
        self.m8_next_flash = 0.0
        self.m8_reaction_times = []
        self.m8_false_flicks = 0
        self.m8_timeouts = 0
        self.m8_avg_rt = 0.0
        self.m8_need_center_reset = False
        self.m8_flash_side = None
        self.m8_target_side = None

        # Mode 9 – Vertex Flick
        # Triangles / position
        self.m9_tri_A = []           # list of 3 (x,y) vertices
        self.m9_tri_B = []
        self.m9_circle_vertex = 0    # destination vertex index (0-2)
        self.m9_active_tri = 0       # 0=A, 1=B
        # Hover / trigger
        self.m9_hover_accum = 0.0    # accumulated hover time
        self.m9_hover_target = 1.0   # randomised threshold for this move
        # Animation
        self.m9_anim_active = False  # True while dash animation is playing
        self.m9_anim_start = 0.0     # timestamp anim began
        self.m9_anim_duration = 0.0  # how long this dash takes
        self.m9_anim_from = (0.0, 0.0)  # pixel start of dash
        self.m9_anim_to   = (0.0, 0.0)  # pixel end of dash
        self.m9_anim_cross = False   # True if this is a cross-triangle dash (faster)
        # Jitter (visual only, offset applied to drawn position)
        self.m9_jitter_x = 0.0
        self.m9_jitter_y = 0.0
        self.m9_jitter_timer = 0.0   # countdown to next jitter sample
        # Twitch
        self.m9_twitch_return = None
        self.m9_twitch_origin = 0
        self.m9_twitch_streak = 0    # consecutive twitches in a row
        # Scoring
        self.m9_tracking_time = 0.0
        self.m9_total_stationary_time = 0.0
        # Hard – cross-triangle jump
        self.m9_cross_next = 0.0

        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        self.update_volume()

    def update_volume(self):
        pygame.mixer.music.set_volume(self.volume)
        POP_SOUND.set_volume(self.volume)
        SHIELD_BREAK_SOUND.set_volume(self.volume)
        TRACKING_SOUND.set_volume(self.volume)
        MISS_SOUND.set_volume(self.volume)
        FLASH_SOUND.set_volume(self.volume)

    # ── MODE 9 helpers ──────────────────────────────────────────────────────

    def get_mode9_params(self):
        """Returns (circle_r, hover_range, twitch_chance, two_triangles)
        hover_range is (min, max) seconds — a random value is drawn each move.
        Easy   diff=1: r=28, hover=0.8-1.0s,  twitch=0.0,   two_tri=False
        Medium diff=2: r=18, hover=0.33-0.5s, twitch=0.25,  two_tri=False
        Hard   diff=3: r=13, hover=0.25-0.33s,twitch=0.333, two_tri=True
        """
        if self.difficulty == 1:
            return 28, (0.8, 1.0),       0.0,   False
        if self.difficulty == 2:
            return 18, (1/3.0, 0.5),     0.25,  False
        return      13, (0.25, 1/3.0),   1/3.0, True

    def _build_triangle(self, cx, cy, size=160):
        verts = []
        for i in range(3):
            angle = math.radians(-90 + 120 * i)
            verts.append((cx + size * math.cos(angle),
                          cy + size * math.sin(angle)))
        return verts

    def _m9_roll_hover_target(self):
        """Draw a fresh randomised hover threshold."""
        _, hover_range, _, _ = self.get_mode9_params()
        self.m9_hover_target = random.uniform(*hover_range)

    def reset_mode9(self):
        self.common_reset("MODE9")
        _, _, _, two_tri = self.get_mode9_params()
        tri_size = 160
        if two_tri:
            cx_A, cx_B = WIDTH // 4, 3 * WIDTH // 4
        else:
            cx_A = cx_B = WIDTH // 2
        cy = HEIGHT // 2
        self.m9_tri_A = self._build_triangle(cx_A, cy, tri_size)
        self.m9_tri_B = self._build_triangle(cx_B, cy, tri_size)

        self.m9_circle_vertex   = 0
        self.m9_active_tri      = 0
        self.m9_hover_accum     = 0.0
        self.m9_anim_active     = False
        self.m9_anim_start      = 0.0
        self.m9_anim_duration   = 0.0
        self.m9_anim_from       = self.m9_tri_A[0]
        self.m9_anim_to         = self.m9_tri_A[0]
        self.m9_anim_cross      = False
        self.m9_jitter_x        = 0.0
        self.m9_jitter_y        = 0.0
        self.m9_jitter_timer    = 0.0
        self.m9_twitch_return   = None
        self.m9_twitch_origin   = 0
        self.m9_twitch_streak   = 0
        self.m9_tracking_time   = 0.0
        self.m9_total_stationary_time = 0.0
        self.m9_cross_next      = time.time() + random.uniform(5, 10)
        self._m9_roll_hover_target()

    def _m9_dest_pos(self):
        """Pixel position of the current destination vertex."""
        tri = self.m9_tri_A if self.m9_active_tri == 0 else self.m9_tri_B
        return tri[self.m9_circle_vertex]

    def _m9_visual_pos(self, now):
        """Interpolated visual position of the circle (used for draw + hit-test)."""
        if self.m9_anim_active:
            elapsed = now - self.m9_anim_start
            t = min(1.0, elapsed / max(self.m9_anim_duration, 1e-6))
            # Ease-out quad: fast start, gentle arrival
            t_ease = 1.0 - (1.0 - t) ** 2
            fx, fy = self.m9_anim_from
            tx, ty = self.m9_anim_to
            return (fx + (tx - fx) * t_ease,
                    fy + (ty - fy) * t_ease)
        return self._m9_dest_pos()

    def _m9_start_anim(self, from_pos, to_pos, is_cross, now):
        """Begin a dash animation between two pixel positions."""
        dist = math.hypot(to_pos[0] - from_pos[0], to_pos[1] - from_pos[1])
        # Speed: ~2200 px/s normal, ~3500 px/s cross-triangle
        speed = 3500.0 if is_cross else 2200.0
        self.m9_anim_duration = max(0.04, dist / speed)
        self.m9_anim_from     = from_pos
        self.m9_anim_to       = to_pos
        self.m9_anim_start    = now
        self.m9_anim_active   = True
        self.m9_anim_cross    = is_cross

    def _m9_do_move(self, now):
        """Trigger a vertex-to-vertex move (normal or twitch)."""
        _, _, twitch_chance, _ = self.get_mode9_params()
        from_pos = self._m9_visual_pos(now)
        other_verts = [v for v in range(3) if v != self.m9_circle_vertex]
        dest = random.choice(other_verts)

        # Each successive twitch halves the chance of the next one being a twitch
        # (streak=0 → full chance, streak=1 → half, streak=2 → quarter, etc.)
        adjusted_chance = twitch_chance * (0.5 ** self.m9_twitch_streak)
        is_twitch = (adjusted_chance > 0 and random.random() < adjusted_chance)

        if is_twitch:
            self.m9_twitch_streak += 1
            self.m9_twitch_origin = self.m9_circle_vertex
            self.m9_circle_vertex = dest
            tri = self.m9_tri_A if self.m9_active_tri == 0 else self.m9_tri_B
            self._m9_start_anim(from_pos, tri[dest], False, now)
            self.m9_twitch_return = now + self.m9_anim_duration + 0.07
        else:
            self.m9_twitch_streak = 0
            self.m9_circle_vertex = dest
            tri = self.m9_tri_A if self.m9_active_tri == 0 else self.m9_tri_B
            self._m9_start_anim(from_pos, tri[dest], False, now)
            self.m9_twitch_return = None

        self.m9_hover_accum = 0.0
        self._m9_roll_hover_target()

    def update_mode9(self, dt):
        now = time.time()
        r, _, _, two_tri = self.get_mode9_params()
        mx, my = self.virtual_mouse

        # ── Cross-triangle jump (hard, highest priority) ──────────────────────
        if two_tri and now >= self.m9_cross_next:
            from_pos = self._m9_visual_pos(now)
            self.m9_active_tri    = 1 - self.m9_active_tri
            self.m9_circle_vertex = random.randint(0, 2)
            tri = self.m9_tri_A if self.m9_active_tri == 0 else self.m9_tri_B
            self._m9_start_anim(from_pos, tri[self.m9_circle_vertex], True, now)
            self.m9_hover_accum   = 0.0
            self.m9_twitch_return = None
            self.m9_cross_next    = now + random.uniform(5, 10)
            self._m9_roll_hover_target()

        # ── Finish animation ──────────────────────────────────────────────────
        if self.m9_anim_active:
            elapsed = now - self.m9_anim_start
            if elapsed >= self.m9_anim_duration:
                self.m9_anim_active = False

        # ── Resolve pending twitch-return ─────────────────────────────────────
        if self.m9_twitch_return is not None and now >= self.m9_twitch_return:
            from_pos = self._m9_visual_pos(now)
            self.m9_circle_vertex = self.m9_twitch_origin
            tri = self.m9_tri_A if self.m9_active_tri == 0 else self.m9_tri_B
            self._m9_start_anim(from_pos, tri[self.m9_twitch_origin], False, now)
            self.m9_twitch_return = None
            self.m9_hover_accum   = 0.0

        # ── Visual position for hit-testing ──────────────────────────────────
        vx, vy = self._m9_visual_pos(now)
        dist = math.hypot(mx - vx, my - vy)
        on_circle = dist <= r

        # ── Jitter update (only when mouse is on circle and not animating) ────
        if on_circle and not self.m9_anim_active:
            self.m9_jitter_timer -= dt
            if self.m9_jitter_timer <= 0:
                amp = 1.8   # max pixel jitter
                self.m9_jitter_x = random.uniform(-amp, amp)
                self.m9_jitter_y = random.uniform(-amp, amp)
                self.m9_jitter_timer = 0.04  # resample every ~40ms
        else:
            # Smoothly decay jitter back to zero when not hovering
            decay = 1.0 - min(1.0, dt * 20)
            self.m9_jitter_x *= decay
            self.m9_jitter_y *= decay

        # ── Scoring ───────────────────────────────────────────────────────────
        # Count stationary time as: not animating OR past the SNAP_GRACE window.
        # Scoring is always allowed — pre-aiming during the dash scores too.
        SNAP_GRACE = 0.04
        past_grace = (not self.m9_anim_active) or \
                     (now - self.m9_anim_start >= SNAP_GRACE)

        if not self.m9_anim_active:
            self.m9_total_stationary_time += dt

        if on_circle and past_grace:
            self.m9_tracking_time += dt
            self.score += 10 * dt
            if now - self.last_tracking_sound > 0.1:
                TRACKING_SOUND.play()
                self.last_tracking_sound = now

        # ── Hover accumulation (only when fully stationary at dest) ──────────
        if on_circle and not self.m9_anim_active and self.m9_twitch_return is None:
            self.m9_hover_accum += dt
            if self.m9_hover_accum >= self.m9_hover_target:
                self._m9_do_move(now)

    # ── END MODE 9 helpers ──────────────────────────────────────────────────

    def create_particles(self, x, y, color, count=5):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def common_reset(self, mode_name):
        self.state = mode_name
        self.targets = []
        self.score = 0
        self.start_time = time.time()
        self.hits = 0
        self.total_clicks = 0
        self.is_high_score = False
        self.particles = []
        self._hud_cache = None
        self._hud_cache_key = None

    def reset_mode1(self):
        self.common_reset("MODE1")
        self.spawn_target_mode1()

    def reset_mode2(self):
        self.common_reset("MODE2")
        r, _, speed, _, _ = self.get_diff_params_mode2()
        angle = random.uniform(0, math.pi * 2)
        self.last_angle = angle
        self.targets = [{
            'pos': [WIDTH / 2, HEIGHT / 2],
            'vel': [math.cos(angle) * speed, math.sin(angle) * speed],
            'r': r
        }]
        self.last_dir_change = time.time()

    def reset_mode3(self):
        self.common_reset("MODE3")
        for _ in range(3):
            self.spawn_target_mode3()

    def reset_mode4(self):
        self.common_reset("MODE4")
        self.micro_state = 0
        self.m4_hover_start = None
        self.targets = [{'pos': (WIDTH // 2, HEIGHT // 2), 'r': 12, 'type': 'CENTER'}]

    def reset_mode5(self):
        self.common_reset("MODE5")
        for _ in range(3):
            self.spawn_target_mode5()

    def reset_mode6(self):
        self.common_reset("MODE6")
        self.lives = 3
        self.last_life_count = 3
        self.speed_multiplier = 1.0
        self.last_spawn = time.time()
        self.last_heart_spawn = time.time()
        self.last_reverser_spawn = time.time()
        self.spawn_target_mode6()

    def get_r_mode1(self):
        return [32, 20, 12][self.difficulty - 1]

    def get_diff_params_mode2(self):
        if self.difficulty == 1: return 36, 0, 150, 1500, math.pi / 2
        if self.difficulty == 2: return 24, 0, 250, 1000, math.pi / 2
        if self.difficulty == 3: return 20, 0, 300, 2000, math.pi / 3
        return 24, 0, 250, 1000, math.pi / 2

    def get_r_mode3(self):
        return [40, 32, 20][self.difficulty - 1]

    def get_mode4_params(self):
        if self.difficulty == 1: return 12, 55
        if self.difficulty == 2: return 8, 52
        if self.difficulty == 3: return 5, 70
        return 8, 52

    def get_mode5_params(self):
        if self.difficulty == 1: return 32, 80, 25
        if self.difficulty == 2: return 24, 140, 40
        if self.difficulty == 3: return 16, 220, 50
        return 24, 140, 40

    def reset_mode7(self):
        self.common_reset("MODE7")
        self.last_spawn = time.time() + 0.5  # short grace before first spawn

    def reset_mode8(self):
        self.common_reset("MODE8")
        self.lives = 3
        self.last_life_count = 3
        self.m8_flash_active = False
        self.m8_reaction_times = []
        self.m8_false_flicks = 0
        self.m8_timeouts = 0
        self.m8_need_center_reset = False
        self.m8_flash_side = None
        self.m8_target_side = None
        interval, _, _, _ = self.get_mode8_params()
        self.m8_next_flash = time.time() + random.uniform(*interval)

    def get_mode7_params(self):
        # returns: r, (speed_min, speed_max), stop_dist_ranges, ttl, band_weights([top,mid,bot])
        if self.difficulty == 1:
            return 16, (120, 190), {0: (35, 85), 1: (135, 235), 2: (35, 85)}, 4.5, [0, 100, 0]
        if self.difficulty == 2:
            return 13, (155, 250), {0: (30, 80), 1: (130, 220), 2: (30, 80)}, 3.5, [15, 70, 15]
        return 10, (190, 300), {0: (28, 75), 1: (120, 210), 2: (28, 75)}, 2.5, [25, 50, 25]

    def get_mode8_params(self):
        # returns: flash_interval_range, window, side_zone_width, center_reset_width
        if self.difficulty == 1: return (2.5, 4.5), 1.4, max(1, int(WIDTH * 0.17)), max(1, int(WIDTH * 0.18))
        if self.difficulty == 2: return (2.0, 3.5), 1.1, max(1, int(WIDTH * 0.13)), max(1, int(WIDTH * 0.15))
        return (1.5, 2.8), 0.85, max(1, int(WIDTH * 0.09)), max(1, int(WIDTH * 0.12))

    def spawn_target_mode7(self):
        r, (spd_min, spd_max), stop_dist_ranges, ttl, band_weights = self.get_mode7_params()
        box_x, box_y, box_w, box_h = self.m7_box_x, self.m7_box_y, self.m7_box_w, self.m7_box_h

        # Choose side: easy=right only, hard=both
        if self.difficulty == 3:
            side = random.choice([-1, 1])   # -1=left exit, 1=right exit
        else:
            side = 1

        # Height band: weighted choice of top/mid/bot third
        band = random.choices([0, 1, 2], weights=band_weights)[0]
        band_h = box_h // 3
        if self.difficulty == 1:
            y = box_y + band_h + band_h // 2
        else:
            y = box_y + band * band_h + random.randint(r + 2, band_h - r - 2)
            y = max(box_y + r, min(box_y + box_h - r, y))

        # Spawn position: edge of box on chosen side
        if side == 1:
            spawn_x = box_x + box_w
        else:
            spawn_x = box_x

        band_speed_mul = {0: 1.0, 1: 1.2, 2: 0.7}
        speed = random.uniform(spd_min, spd_max) * band_speed_mul[band]
        stop_dist = random.uniform(*stop_dist_ranges[band])
        stop_x = spawn_x + side * stop_dist

        self.targets.append({
            'pos': [float(spawn_x), float(y)],
            'r': r,
            'side': side,
            'speed': speed,
            'stop_x': stop_x,
            'moving': True,
            'born': time.time(),
            'ttl': ttl,
            'spawn_time': time.time(),
            'band': band,
        })

    def update_mode7(self, dt):
        now = time.time()
        # Spawn rate: one target at a time up to 2 max
        max_t = 2
        if len(self.targets) < max_t and now - self.last_spawn > 1.9:
            self.spawn_target_mode7()
            self.last_spawn = now

        for t in self.targets[:]:
            if t['moving']:
                t['pos'][0] += t['side'] * t['speed'] * dt
                if t['side'] == 1 and t['pos'][0] >= t['stop_x']:
                    t['pos'][0] = t['stop_x']
                    t['moving'] = False
                elif t['side'] == -1 and t['pos'][0] <= t['stop_x']:
                    t['pos'][0] = t['stop_x']
                    t['moving'] = False
            # Expire if TTL exceeded
            if now - t['born'] > t['ttl']:
                self.targets.remove(t)

    def update_mode8(self, dt):
        now = time.time()
        interval, window, safe_w, center_w = self.get_mode8_params()
        mx = self.virtual_mouse[0]
        center_l = WIDTH // 2 - center_w // 2
        center_r = WIDTH // 2 + center_w // 2
        in_center = center_l <= mx <= center_r
        in_left = mx < safe_w
        in_right = mx > WIDTH - safe_w
        in_target = (self.m8_target_side == "left" and in_left) or (self.m8_target_side == "right" and in_right)
        in_wrong = (self.m8_flash_side == "left" and in_left) or (self.m8_flash_side == "right" and in_right)

        if self.m8_need_center_reset:
            if in_center:
                self.m8_need_center_reset = False
                self.m8_next_flash = now + random.uniform(*interval)
            return

        if self.m8_flash_active:
            elapsed = now - self.m8_flash_born
            if elapsed > window:
                self.m8_flash_active = False
                self.m8_timeouts += 1
                self.lives -= 1
                MISS_SOUND.play()
                self.last_life_count = self.lives
                if self.lives <= 0:
                    self.m8_avg_rt = (sum(self.m8_reaction_times) / len(self.m8_reaction_times)) if self.m8_reaction_times else 0
                    self.finish_game()
                    return
                self.m8_need_center_reset = True
            else:
                if in_target:
                    rt = now - self.m8_flash_born
                    self.m8_reaction_times.append(rt)
                    pts = max(100, int(1000 * (1.0 - rt / window) ** 1.5))
                    self.score += pts
                    self.hits += 1
                    FLASH_SOUND.play()
                    self.m8_flash_active = False
                    self.m8_need_center_reset = True
                elif in_wrong:
                    self.m8_false_flicks += 1
                    self.lives -= 1
                    MISS_SOUND.play()
                    self.last_life_count = self.lives
                    self.m8_flash_active = False
                    self.m8_need_center_reset = True
                    if self.lives <= 0:
                        self.m8_avg_rt = (sum(self.m8_reaction_times) / len(self.m8_reaction_times)) if self.m8_reaction_times else 0
                        self.finish_game()
                        return
        else:
            if now >= self.m8_next_flash and in_center:
                self.m8_flash_side = random.choice(["left", "right"])
                self.m8_target_side = "right" if self.m8_flash_side == "left" else "left"
                if self.m8_flash_side == "left":
                    # Between right edge of centre zone and left edge of safe zone
                    band_left  = center_l - 14
                    band_right = safe_w + 14
                    fx = random.randint(min(band_right, band_left), max(band_right, band_left))
                else:
                    # Between right edge of safe zone and left edge of centre zone
                    band_left  = WIDTH - safe_w - 14
                    band_right = center_r + 14
                    fx = random.randint(min(band_left, band_right), max(band_left, band_right))
                fy = HEIGHT // 2 + random.randint(-int(HEIGHT * 0.1), int(HEIGHT * 0.1))
                self.m8_flash_pos = (fx, fy)
                self.m8_flash_born = now
                self.m8_flash_active = True

    def get_mode6_params(self):
        if self.difficulty == 1: return 34, 200, 1.2, 5
        if self.difficulty == 2: return 26, 250, 0.8, 6
        if self.difficulty == 3: return 22, 250, 0.5, 7
        return 26, 250, 0.8, 6

    def spawn_target_mode1(self):
        r = self.get_r_mode1()
        sigma = HEIGHT / (4 + self.difficulty * 2)
        x = random.randint(100, WIDTH - 100)
        y = max(100, min(HEIGHT - 100, int(random.gauss(HEIGHT // 2, sigma))))
        self.targets = [{'pos': (x, y), 'r': r}]

    def spawn_target_mode3(self):
        r = self.get_r_mode3()
        padding = 10
        for _ in range(10):
            x = random.randint(r + padding + 50, WIDTH - r - padding - 50)
            y = random.randint(r + padding + 50, HEIGHT - r - padding - 50)
            valid_spawn = True
            for t in self.targets:
                dist = math.hypot(x - t['pos'][0], y - t['pos'][1])
                if dist < r + t['r'] + padding:
                    valid_spawn = False
                    break
            if valid_spawn:
                self.targets.append({'pos': (x, y), 'r': r})
                break

    def spawn_target_mode4(self):
        r, spread = self.get_mode4_params()
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(spread * 0.35, spread * 0.75)
        cx, cy = WIDTH // 2, HEIGHT // 2
        x = cx + math.cos(angle) * dist
        y = cy + math.sin(angle) * dist
        self.targets = [{'pos': (x, y), 'r': r, 'type': 'FLICK'}]

    def spawn_target_mode5(self):
        r, speed, hp = self.get_mode5_params()
        x = random.randint(r, WIDTH - r)
        y = random.randint(r, HEIGHT - r)
        angle = random.uniform(0, math.pi * 2)
        vel = [math.cos(angle) * speed, math.sin(angle) * speed]
        self.targets.append({'pos': [x, y], 'vel': vel, 'r': r, 'hp': hp, 'max_hp': hp})

    def spawn_target_mode6(self):
        r, _, _, max_circles = self.get_mode6_params()
        if len(self.targets) >= max_circles:
            return
        now = time.time()
        y = random.randint(r, HEIGHT - r)
        is_heart = False
        heart_chance = 0.035 if self.difficulty == 3 else 0.05
        if now - self.last_heart_spawn > HEART_SPAWN_COOLDOWN and random.random() < heart_chance:
            is_heart = True
            self.last_heart_spawn = now
        has_shield = (self.difficulty == 3 and random.random() < 0.15)
        is_reverser = False
        is_lightning = False
        if self.difficulty == 3 and not is_heart and not has_shield:
            roll = random.random()
            if roll < 0.12:
                is_reverser = True
            elif roll < 0.19:
                is_lightning = True
        elif self.difficulty == 2 and not is_heart:
            if random.random() < 0.12:
                is_reverser = True
        # All targets spawn from the left edge and travel right
        x = -r
        _, base_spd, _, _ = self.get_mode6_params()
        # Reversers get a fixed speed unaffected by the time-based multiplier
        if is_lightning:
            spawn_speed = base_spd * 3.5   # starts very fast
        elif is_reverser:
            spawn_speed = base_spd
        else:
            spawn_speed = base_spd * self.speed_multiplier
        self.targets.append({
            'pos': [x, y],
            'r': r,
            'direction': 1,
            'speed': spawn_speed,
            'has_shield': has_shield and not is_heart,
            'shielded': has_shield and not is_heart,
            'is_heart': is_heart,
            'is_reverser': is_reverser,
            'is_lightning': is_lightning,
            'next_reverse': now + random.uniform(0.3, 0.8) if is_reverser else None,
        })

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == "MENU":
                        self.running = False
                    elif self.state == "CROSSHAIR":
                        self.state = "MENU"
                    else:
                        self.state = "MENU"
            if event.type == pygame.MOUSEMOTION:
                self.virtual_mouse[0] += event.rel[0] * self.sensitivity
                self.virtual_mouse[1] += event.rel[1] * self.sensitivity
                self.virtual_mouse[0] = max(0, min(WIDTH, self.virtual_mouse[0]))
                self.virtual_mouse[1] = max(0, min(HEIGHT, self.virtual_mouse[1]))
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.mouse_held = True
                if self.state == "MENU":
                    self.handle_menu_click()
                elif self.state == "CROSSHAIR":
                    self.handle_crosshair_click()
                elif self.state in ["MODE1", "MODE3", "MODE4", "MODE6", "MODE7"]:
                    self.handle_click_modes()
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.mouse_held = False

    def handle_menu_click(self):
        for btn in self.buttons:
            if btn.rect.collidepoint(self.virtual_mouse):
                if btn.action == "START_1":
                    self.reset_mode1()
                elif btn.action == "START_2":
                    self.reset_mode2()
                elif btn.action == "START_3":
                    self.reset_mode3()
                elif btn.action == "START_4":
                    self.reset_mode4()
                elif btn.action == "START_5":
                    self.reset_mode5()
                elif btn.action == "START_6":
                    self.reset_mode6()
                elif btn.action == "START_7":
                    self.reset_mode7()
                elif btn.action == "START_8":
                    self.reset_mode8()
                elif btn.action == "START_9":
                    self.reset_mode9()
                elif btn.action == "EXIT":
                    self.running = False
                elif btn.action == "TOGGLE_DIFF":
                    self.difficulty = (self.difficulty % 3) + 1
                    labels = {1: "Difficulty: Easy", 2: "Difficulty: Medium", 3: "Difficulty: Hard"}
                    btn.text = labels[self.difficulty]
                elif btn.action == "CROSSHAIR":
                    self.state = "CROSSHAIR"

    def handle_crosshair_click(self):
        mx, my = self.virtual_mouse
        col_left = WIDTH // 2 - 420
        row_y = 160

        # Style buttons
        styles = ["dot", "classic", "cross", "gap"]
        for i, sty in enumerate(styles):
            bx = col_left + i * 155
            by = row_y + 30
            if pygame.Rect(bx, by, 140, 40).collidepoint(mx, my):
                self.crosshair_style = sty

        # Colour buttons
        row_y += 110
        ch_colors = [
            COLOR_ACCENT, COLOR_RED, COLOR_GREEN,
            COLOR_ORANGE, (255, 255, 255), (255, 255, 0),
        ]
        for i, clr in enumerate(ch_colors):
            bx = col_left + i * 110
            by = row_y + 30
            if pygame.Rect(bx, by, 95, 36).collidepoint(mx, my):
                self.crosshair_color = clr

    def handle_click_modes(self):
        self.total_clicks += 1
        mx, my = self.virtual_mouse
        hit = None

        if self.state == "MODE4":
            t = self.targets[0]
            dist = math.hypot(mx - t['pos'][0], my - t['pos'][1])
            if dist <= t['r']:
                self.hits += 1
                if t['type'] == 'CENTER':
                    POP_SOUND.play()
                    self.create_particles(t['pos'][0], t['pos'][1], COLOR_BLUE, 3)
                    self.spawn_target_mode4()
                else:
                    self.score += 1
                    self.targets = [{'pos': (WIDTH // 2, HEIGHT // 2), 'r': 12, 'type': 'CENTER'}]
                    SHIELD_BREAK_SOUND.play()
                    self.create_particles(t['pos'][0], t['pos'][1], COLOR_ORANGE, 5)
            return

        for t in self.targets:
            dist = math.hypot(mx - t['pos'][0], my - t['pos'][1])
            if dist <= t['r']:
                hit = t
                break

        if hit:
            self.hits += 1
            if hit.get('is_heart', False):
                if self.lives < 3: self.lives += 1
                self.score += 200
                self.targets.remove(hit)
                POP_SOUND.play()
                self.create_particles(hit['pos'][0], hit['pos'][1], COLOR_HEART, 7)
                return

            if self.state == "MODE6" and hit.get('shielded', False):
                hit['shielded'] = False
                self.score += 50
                SHIELD_BREAK_SOUND.play()
                self.create_particles(hit['pos'][0], hit['pos'][1], COLOR_SHIELD, 4)
                return

            self.score += 100
            self.targets.remove(hit)
            POP_SOUND.play()
            self.create_particles(hit['pos'][0], hit['pos'][1], COLOR_RED, 5)

            if self.state == "MODE1": self.spawn_target_mode1()
            if self.state == "MODE3": self.spawn_target_mode3()
            if self.state == "MODE7":
                # Bonus for clicking quickly (more points the sooner after it stops)
                age = time.time() - hit['born']
                ttl = hit['ttl']
                bonus = max(0, int(300 * (1.0 - age / ttl) ** 1.5))
                self.score += bonus

    def update(self):
        dt = CLOCK.get_time() / 1000.0

        self.particles = [p for p in self.particles if p.life > 0]
        for particle in self.particles:
            particle.update()

        if self.state == "MENU":
            self.sensitivity = self.slider.update(self.virtual_mouse, self.mouse_held)
            old_volume = self.volume
            self.volume = self.volume_slider.update(self.virtual_mouse, self.mouse_held)
            if old_volume != self.volume:
                self.update_volume()
            for btn in self.buttons: btn.check_hover(self.virtual_mouse)

        elif self.state == "CROSSHAIR":
            if self.ch_size_slider is not None:
                self.crosshair_size  = int(self.ch_size_slider.update(self.virtual_mouse, self.mouse_held))
                self.crosshair_width = int(self.ch_width_slider.update(self.virtual_mouse, self.mouse_held))
                self.crosshair_gap   = int(self.ch_gap_slider.update(self.virtual_mouse, self.mouse_held))

        elif self.state == "MODE4":
            # Micro-flick: first (centre) target triggers automatically when held over.
            if self.targets:
                t = self.targets[0]
                if t.get('type') == 'CENTER':
                    mx, my = self.virtual_mouse
                    dist = math.hypot(mx - t['pos'][0], my - t['pos'][1])
                    if dist <= t['r']:
                        if self.m4_hover_start is None:
                            self.m4_hover_start = time.time()
                        elif time.time() - self.m4_hover_start >= 0.12:
                            self.total_clicks += 1
                            self.hits += 1
                            POP_SOUND.play()
                            self.create_particles(t['pos'][0], t['pos'][1], COLOR_BLUE, 3)
                            self.spawn_target_mode4()
                            self.m4_hover_start = None
                    else:
                        self.m4_hover_start = None

        elif self.state == "MODE2":
            self.update_mode2(dt)
        elif self.state == "MODE5":
            self.update_mode5(dt)
        elif self.state == "MODE6":
            self.update_mode6(dt)
        elif self.state == "MODE7":
            self.update_mode7(dt)
        elif self.state == "MODE8":
            self.update_mode8(dt)
        elif self.state == "MODE9":
            self.update_mode9(dt)

        if self.state in ["MODE1", "MODE2", "MODE3", "MODE4", "MODE5", "MODE7"]:
            if time.time() - self.start_time > 30:
                self.finish_game()

        if self.state == "MODE9":
            if time.time() - self.start_time > 60:
                self.finish_game()

    def update_mode2(self, dt):
        t = self.targets[0]
        r, _, speed, change_freq, max_angle_change = self.get_diff_params_mode2()

        t['pos'][0] += t['vel'][0] * dt
        t['pos'][1] += t['vel'][1] * dt

        if t['pos'][0] < r or t['pos'][0] > WIDTH - r:
            t['vel'][0] *= -1
            t['pos'][0] = max(r, min(WIDTH - r, t['pos'][0]))
        if t['pos'][1] < r or t['pos'][1] > HEIGHT - r:
            t['vel'][1] *= -1
            t['pos'][1] = max(r, min(HEIGHT - r, t['pos'][1]))

        if (time.time() - self.last_dir_change) * 1000 > change_freq:
            new_angle = random.uniform(0, math.pi * 2)
            angle_diff = (new_angle - self.last_angle) % (2 * math.pi)
            if angle_diff > math.pi: angle_diff -= 2 * math.pi
            if abs(angle_diff) > max_angle_change:
                if angle_diff > 0:
                    new_angle = self.last_angle + max_angle_change
                else:
                    new_angle = self.last_angle - max_angle_change
            t['vel'] = [math.cos(new_angle) * speed, math.sin(new_angle) * speed]
            self.last_angle = new_angle
            self.last_dir_change = time.time()

        dist = math.hypot(self.virtual_mouse[0] - t['pos'][0], self.virtual_mouse[1] - t['pos'][1])
        if dist <= r:
            self.score += (100 * dt)
            t['active'] = True
            if time.time() - self.last_tracking_sound > 0.1:
                TRACKING_SOUND.play()
                self.last_tracking_sound = time.time()
        else:
            t['active'] = False

    def update_mode5(self, dt):
        mx, my = self.virtual_mouse
        r, _, _ = self.get_mode5_params()
        dead_targets = []
        for t in self.targets:
            t['pos'][0] += t['vel'][0] * dt
            t['pos'][1] += t['vel'][1] * dt
            if t['pos'][0] < r or t['pos'][0] > WIDTH - r:
                t['vel'][0] *= -1
                t['pos'][0] = max(r, min(WIDTH - r, t['pos'][0]))
            if t['pos'][1] < r or t['pos'][1] > HEIGHT - r:
                t['vel'][1] *= -1
                t['pos'][1] = max(r, min(HEIGHT - r, t['pos'][1]))
            dist = math.hypot(mx - t['pos'][0], my - t['pos'][1])
            if dist <= r:
                t['hp'] -= dt * 30
                t['active'] = True
                self.score += 50 * dt
                if t['hp'] <= 0:
                    dead_targets.append(t)
            else:
                t['active'] = False
        for dt_target in dead_targets:
            self.targets.remove(dt_target)
            self.score += 500
            POP_SOUND.play()
            self.create_particles(dt_target['pos'][0], dt_target['pos'][1], COLOR_GREEN, 6)
            self.spawn_target_mode5()

    def update_mode6(self, dt):
        r, base_speed, spawn_rate, _ = self.get_mode6_params()
        if self.lives < self.last_life_count:
            self.speed_multiplier = 1.0
            self.last_life_count = self.lives
        self.speed_multiplier = min(2.0, self.speed_multiplier + 0.02 * dt)
        actual_speed = base_speed * self.speed_multiplier
        now = time.time()

        if now - self.last_spawn > spawn_rate:
            self.spawn_target_mode6()
            self.last_spawn = now

        for t in self.targets[:]:
            if t.get('is_reverser') and t['next_reverse'] and now >= t['next_reverse']:
                if t['direction'] == 1:
                    t['direction'] = -1
                    t['speed'] = base_speed * random.uniform(0.5, 0.9)
                    t['next_reverse'] = now + random.uniform(0.25, 0.5)
                else:
                    t['direction'] = 1
                    t['speed'] = base_speed * random.uniform(0.8, 1.2)
                    t['next_reverse'] = now + random.uniform(0.8, 1.8)

            move_speed = t['speed'] if (t.get('is_reverser') or t.get('is_lightning')) else actual_speed
            # Lightning: decelerates as it approaches the right side
            if t.get('is_lightning'):
                progress = max(0.0, min(1.0, t['pos'][0] / WIDTH))
                decel = 1.0 - progress * 0.82   # slows to ~18% speed at right edge
                t['pos'][0] += t['direction'] * move_speed * decel * dt
            else:
                t['pos'][0] += t['direction'] * move_speed * dt

            if t['pos'][0] < -r * 3:
                self.targets.remove(t)
                continue
            if t['pos'][0] > WIDTH + r:
                self.lives -= 1
                self.targets.remove(t)
                if self.lives <= 0:
                    self.finish_game()

    def finish_game(self):
        self._last_mode = self.state
        if self.state == "MODE8":
            self.m8_avg_rt = (sum(self.m8_reaction_times) / len(self.m8_reaction_times)) if self.m8_reaction_times else 0
        self.is_high_score = DataManager.save_score(self.state.lower(), int(self.score))
        self.state = "GAMEOVER"

    def _draw_crosshair(self, surface, cx, cy):
        """Draw the crosshair at (cx, cy) using current settings."""
        color = self.crosshair_color
        size  = self.crosshair_size
        width = self.crosshair_width
        gap   = self.crosshair_gap
        style = self.crosshair_style

        if style == "dot":
            pygame.draw.circle(surface, color, (cx, cy), max(2, width + 1))

        elif style == "classic":
            # Four lines from centre outward, no gap
            pygame.draw.line(surface, color, (cx - size, cy), (cx + size, cy), width)
            pygame.draw.line(surface, color, (cx, cy - size), (cx, cy + size), width)
            pygame.draw.circle(surface, color, (cx, cy), max(1, width // 2))

        elif style == "cross":
            # Four lines with a centre gap, no dot
            pygame.draw.line(surface, color, (cx - size, cy), (cx - gap, cy), width)
            pygame.draw.line(surface, color, (cx + gap, cy), (cx + size, cy), width)
            pygame.draw.line(surface, color, (cx, cy - size), (cx, cy - gap), width)
            pygame.draw.line(surface, color, (cx, cy + gap), (cx, cy + size), width)

        elif style == "gap":
            # Gap cross plus centre dot
            pygame.draw.line(surface, color, (cx - size, cy), (cx - gap, cy), width)
            pygame.draw.line(surface, color, (cx + gap, cy), (cx + size, cy), width)
            pygame.draw.line(surface, color, (cx, cy - size), (cx, cy - gap), width)
            pygame.draw.line(surface, color, (cx, cy + gap), (cx, cy + size), width)
            pygame.draw.circle(surface, color, (cx, cy), max(1, width // 2 + 1))

    def draw(self):
        SCREEN.fill(COLOR_BG)

        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "CROSSHAIR":
            self.draw_crosshair_menu()
        elif self.state == "GAMEOVER":
            self.draw_gameover()
        else:
            self.draw_game()

        for particle in self.particles:
            particle.draw(SCREEN)

        cx, cy = int(self.virtual_mouse[0]), int(self.virtual_mouse[1])
        if self.state in ("MENU", "GAMEOVER", "CROSSHAIR"):
            # Plain cursor so the player can see where they're pointing in menus
            pygame.draw.circle(SCREEN, (220, 220, 220), (cx, cy), 4)
            pygame.draw.circle(SCREEN, (0, 0, 0), (cx, cy), 4, 1)
        else:
            self._draw_crosshair(SCREEN, cx, cy)

        pygame.display.flip()

    def draw_menu(self):
        hdr_h = 112
        pygame.draw.rect(SCREEN, COLOR_MENU_HEADER_BG, (0, 0, WIDTH, hdr_h))
        pygame.draw.line(SCREEN, COLOR_ACCENT, (WIDTH // 5, hdr_h - 2), (4 * WIDTH // 5, hdr_h - 2), 2)

        title = FONT_LG.render("LITEAIM V2.0", True, COLOR_TEXT)
        SCREEN.blit(title, (WIDTH // 2 - title.get_width() // 2, 22))
        sub = FONT_XSM.render("Choose a drill — mouse to select", True, (120, 128, 150))
        SCREEN.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 78))

        scores = DataManager.load_scores()
        hi1 = (
            f"Bests — Reflex {scores.get('mode1', 0)} · Track {scores.get('mode2', 0)} · "
            f"Grid {scores.get('mode3', 0)} · Micro {scores.get('mode4', 0)} · Switch {scores.get('mode5', 0)}"
        )
        hi2 = (
            f"Pressure {scores.get('mode6', 0)} · Angles {scores.get('mode7', 0)} · "
            f"Flash {scores.get('mode8', 0)} · Vertex {scores.get('mode9', 0)}"
        )
        hy = hdr_h + 8
        for i, line in enumerate((hi1, hi2)):
            s_surf = FONT_XSM.render(line, True, (135, 140, 160))
            SCREEN.blit(s_surf, (WIDTH // 2 - s_surf.get_width() // 2, hy + i * 22))

        if len(self.buttons) >= 9:
            panel = self.buttons[0].rect.union(self.buttons[8].rect).inflate(36, 32)
            pygame.draw.rect(SCREEN, COLOR_MENU_PANEL, panel, border_radius=18)
            pygame.draw.rect(SCREEN, COLOR_MENU_PANEL_BORDER, panel, 2, border_radius=18)

        for btn in self.buttons:
            btn.draw(SCREEN)

        bar = pygame.Rect(WIDTH // 2 - 340, HEIGHT - 238, 680, 118)
        pygame.draw.rect(SCREEN, (20, 22, 32), bar, border_radius=14)
        pygame.draw.rect(SCREEN, (48, 52, 68), bar, 1, border_radius=14)
        self.slider.draw(SCREEN)
        self.volume_slider.draw(SCREEN)

    def draw_crosshair_menu(self):
        title = FONT_LG.render("CROSSHAIR CUSTOMISER", True, COLOR_ACCENT)
        SCREEN.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        col_left = WIDTH // 2 - 420
        col_right = WIDTH // 2 + 80
        row_y = 160

        # --- Style buttons ---
        style_label = FONT_SM.render("Style:", True, COLOR_TEXT)
        SCREEN.blit(style_label, (col_left, row_y))
        styles = ["dot", "classic", "cross", "gap"]
        style_labels = ["Dot", "Classic", "Cross", "Gap Cross"]
        for i, (sty, lbl) in enumerate(zip(styles, style_labels)):
            bx = col_left + i * 155
            by = row_y + 30
            bw, bh = 140, 40
            br = pygame.Rect(bx, by, bw, bh)
            selected = (self.crosshair_style == sty)
            pygame.draw.rect(SCREEN, COLOR_ACCENT if selected else COLOR_UI_BG, br, border_radius=6)
            pygame.draw.rect(SCREEN, (255, 255, 255), br, 2, border_radius=6)
            t_surf = FONT_SM.render(lbl, True, (0, 0, 0) if selected else COLOR_TEXT)
            SCREEN.blit(t_surf, (bx + bw // 2 - t_surf.get_width() // 2, by + bh // 2 - t_surf.get_height() // 2))

        # --- Colour buttons ---
        row_y += 110
        col_label = FONT_SM.render("Colour:", True, COLOR_TEXT)
        SCREEN.blit(col_label, (col_left, row_y))
        ch_colors = [
            (COLOR_ACCENT,  "Cyan"),
            (COLOR_RED,     "Red"),
            (COLOR_GREEN,   "Green"),
            (COLOR_ORANGE,  "Orange"),
            ((255,255,255), "White"),
            ((255,255,0),   "Yellow"),
        ]
        for i, (clr, name) in enumerate(ch_colors):
            bx = col_left + i * 110
            by = row_y + 30
            bw, bh = 95, 36
            cr = pygame.Rect(bx, by, bw, bh)
            pygame.draw.rect(SCREEN, clr, cr, border_radius=6)
            sel = (self.crosshair_color == clr)
            pygame.draw.rect(SCREEN, (255, 255, 255) if sel else (80, 80, 80), cr, 3 if sel else 1, border_radius=6)
            n_surf = FONT_SM.render(name, True, (0, 0, 0))
            SCREEN.blit(n_surf, (bx + bw // 2 - n_surf.get_width() // 2, by + bh // 2 - n_surf.get_height() // 2))

        # --- Sliders (lazy-init) ---
        slider_x = col_left
        if self.ch_size_slider is None:
            self.ch_size_slider  = Slider(slider_x, row_y + 110, 600, 4, 30, self.crosshair_size,  "Size")
            self.ch_width_slider = Slider(slider_x, row_y + 175, 600, 1, 8,  self.crosshair_width, "Thickness")
            self.ch_gap_slider   = Slider(slider_x, row_y + 240, 600, 0, 20, self.crosshair_gap,   "Gap")

        self.ch_size_slider.draw(SCREEN)
        self.ch_width_slider.draw(SCREEN)
        self.ch_gap_slider.draw(SCREEN)

        # --- Live preview ---
        prev_x = WIDTH - 170
        prev_y = HEIGHT // 2 + 40
        prev_label = FONT_MD.render("Preview", True, COLOR_TEXT)
        SCREEN.blit(prev_label, (prev_x - prev_label.get_width() // 2, prev_y - 120))
        # Draw a dark box behind preview
        pygame.draw.rect(SCREEN, (30, 30, 40), (prev_x - 80, prev_y - 80, 160, 160), border_radius=10)
        pygame.draw.rect(SCREEN, (60, 60, 70), (prev_x - 80, prev_y - 80, 160, 160), 2, border_radius=10)
        self._draw_crosshair(SCREEN, prev_x, prev_y)

        back_text = FONT_SM.render("Press ESC to return", True, (150, 150, 150))
        SCREEN.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, HEIGHT - 50))

    def draw_game(self):
        # ── MODE 7: Angle Holder ────────────────────────────────────────────
        if self.state == "MODE7":
            bx, by, bw, bh = self.m7_box_x, self.m7_box_y, self.m7_box_w, self.m7_box_h
            # Draw box with band dividers
            pygame.draw.rect(SCREEN, (50, 50, 70), (bx, by, bw, bh), border_radius=4)
            pygame.draw.rect(SCREEN, COLOR_ACCENT, (bx, by, bw, bh), 2, border_radius=4)
            band_h = bh // 3
            for i in range(1, 3):
                pygame.draw.line(SCREEN, (80, 80, 100), (bx, by + band_h * i), (bx + bw, by + band_h * i), 1)
            # Band labels
            for i, lbl in enumerate(["Top", "Mid", "Bot"]):
                ls = FONT_XSM.render(lbl, True, (100, 100, 130))
                SCREEN.blit(ls, (bx + bw // 2 - ls.get_width() // 2, by + band_h * i + band_h // 2 - ls.get_height() // 2))
            for t in self.targets:
                pos = (int(t['pos'][0]), int(t['pos'][1]))
                # Fade colour as TTL expires
                age_ratio = min(1.0, (time.time() - t['born']) / t['ttl'])
                r_col = int(235 * (1.0 - age_ratio) + 235 * age_ratio)
                g_col = int(60 * (1.0 - age_ratio))
                b_col = int(60 * (1.0 - age_ratio))
                color = (r_col, g_col, b_col)
                pygame.draw.circle(SCREEN, color, pos, t['r'])
                pygame.draw.circle(SCREEN, (255, 255, 255), pos, t['r'], 2)
                # TTL arc indicator
                angle_span = (1.0 - age_ratio) * 2 * math.pi
                if angle_span > 0.1:
                    arc_r = pygame.Rect(pos[0] - t['r'] - 5, pos[1] - t['r'] - 5, (t['r'] + 5) * 2, (t['r'] + 5) * 2)
                    pygame.draw.arc(SCREEN, COLOR_ACCENT, arc_r, math.pi / 2, math.pi / 2 + angle_span, 2)

        # ── MODE 8: Flash Flick ─────────────────────────────────────────────
        elif self.state == "MODE8":
            _, window, safe_w, center_w = self.get_mode8_params()
            # Safe zones
            zone_col = (30, 60, 30)
            pygame.draw.rect(SCREEN, zone_col, (0, 0, safe_w, HEIGHT))
            pygame.draw.rect(SCREEN, zone_col, (WIDTH - safe_w, 0, safe_w, HEIGHT))
            pygame.draw.line(SCREEN, (60, 120, 60), (safe_w, 0), (safe_w, HEIGHT), 2)
            pygame.draw.line(SCREEN, (60, 120, 60), (WIDTH - safe_w, 0), (WIDTH - safe_w, HEIGHT), 2)
            lbl_l = FONT_SM.render("LEFT", True, (60, 180, 60))
            lbl_r = FONT_SM.render("RIGHT", True, (60, 180, 60))
            SCREEN.blit(lbl_l, (safe_w // 2 - lbl_l.get_width() // 2, HEIGHT // 2))
            SCREEN.blit(lbl_r, (WIDTH - safe_w // 2 - lbl_r.get_width() // 2, HEIGHT // 2))
            center_l = WIDTH // 2 - center_w // 2
            pygame.draw.rect(SCREEN, (40, 40, 70), (center_l, 0, center_w, HEIGHT), 1)
            c_lbl = FONT_XSM.render("RESET ZONE", True, (130, 130, 180))
            SCREEN.blit(c_lbl, (WIDTH // 2 - c_lbl.get_width() // 2, 24))
            # Flash dot
            if self.m8_flash_active:
                elapsed = time.time() - self.m8_flash_born
                fade = max(0.2, 1.0 - elapsed / window)
                radius = max(6, int(18 * fade))
                pygame.draw.circle(SCREEN, COLOR_FLASH, self.m8_flash_pos, radius)
                pygame.draw.circle(SCREEN, (255, 180, 180), self.m8_flash_pos, radius, 2)
                # Urgency ring that shrinks as time runs out
                ring_r = int(radius * 2.5 * fade)
                if ring_r > radius:
                    pygame.draw.circle(SCREEN, (180, 40, 40), self.m8_flash_pos, ring_r, 1)
                target_txt = FONT_SM.render(
                    f"Flash {self.m8_flash_side.upper()} -> Flick {self.m8_target_side.upper()}",
                    True, COLOR_TEXT)
                SCREEN.blit(target_txt, (WIDTH // 2 - target_txt.get_width() // 2, 56))
            elif self.m8_need_center_reset:
                reset_txt = FONT_SM.render("Return crosshair to centre to arm next flash", True, COLOR_TEXT)
                SCREEN.blit(reset_txt, (WIDTH // 2 - reset_txt.get_width() // 2, 56))
            else:
                arm_txt = FONT_SM.render("Hold centre, wait for side flash", True, COLOR_TEXT)
                SCREEN.blit(arm_txt, (WIDTH // 2 - arm_txt.get_width() // 2, 56))
            # Lives
            for i in range(self.lives):
                pygame.draw.circle(SCREEN, COLOR_HEART, (30 + i * 35, 35), 12)

        # ── MODE 9: Vertex Flick ─────────────────────────────────────────────
        elif self.state == "MODE9":
            r, _, _, two_tri = self.get_mode9_params()
            now_d = time.time()

            # Ghost dots at each vertex (implied triangle)
            def draw_ghost_tri(verts):
                for vx, vy in verts:
                    pygame.draw.circle(SCREEN, (55, 58, 78), (int(vx), int(vy)), 5)

            if two_tri:
                draw_ghost_tri(self.m9_tri_A)
                draw_ghost_tri(self.m9_tri_B)
                pygame.draw.line(SCREEN, (40, 44, 60), (WIDTH // 2, 80), (WIDTH // 2, HEIGHT - 80), 1)
            else:
                draw_ghost_tri(self.m9_tri_A)

            # Visual position (interpolated during animation)
            vx, vy = self._m9_visual_pos(now_d)

            # ── Motion blur ghost trail ───────────────────────────────────────
            if self.m9_anim_active:
                elapsed = now_d - self.m9_anim_start
                dur     = max(self.m9_anim_duration, 1e-6)
                t_now   = min(1.0, elapsed / dur)
                fx, fy  = self.m9_anim_from
                tx, ty  = self.m9_anim_to

                NUM_GHOSTS = 5
                for gi in range(NUM_GHOSTS):
                    # Each ghost is at an earlier position along the path
                    lag = (gi + 1) / (NUM_GHOSTS + 1)   # 1/(N+1) .. N/(N+1)
                    gt  = max(0.0, t_now - lag * 0.35)  # how far back in time
                    gt_ease = 1.0 - (1.0 - gt) ** 2
                    gx = fx + (tx - fx) * gt_ease
                    gy = fy + (ty - fy) * gt_ease
                    # Fade and shrink older ghosts
                    alpha_frac = (1.0 - lag) * 0.45     # 0.45 → 0.09 opacity
                    ghost_r    = max(2, int(r * (0.55 + 0.35 * (1.0 - lag))))
                    # Blend ghost colour with bg (20,20,30)
                    base = COLOR_ACCENT
                    gc = (
                        int(20 + (base[0] - 20) * alpha_frac),
                        int(20 + (base[1] - 20) * alpha_frac),
                        int(30 + (base[2] - 30) * alpha_frac),
                    )
                    pygame.draw.circle(SCREEN, gc, (int(gx), int(gy)), ghost_r)

            # ── Main circle (with jitter offset when hovering) ────────────────
            jx = int(vx + self.m9_jitter_x)
            jy = int(vy + self.m9_jitter_y)

            circ_col = COLOR_ACCENT
            pygame.draw.circle(SCREEN, circ_col, (jx, jy), r)
            pygame.draw.circle(SCREEN, (255, 255, 255), (jx, jy), r, 2)

        # ── ALL OTHER MODES ─────────────────────────────────────────────────
        else:
            for t in self.targets:
                pos = (int(t['pos'][0]), int(t['pos'][1]))
                if self.state in ["MODE2", "MODE5"]:
                    color = COLOR_GREEN if t.get('active') else COLOR_RED
                    if self.state == "MODE5":
                        hp_pct = max(0, t['hp'] / t['max_hp'])
                        bar_w = 40
                        pygame.draw.rect(SCREEN, (50, 50, 50), (pos[0] - 20, pos[1] - t['r'] - 15, bar_w, 8))
                        pygame.draw.rect(SCREEN, COLOR_GREEN, (pos[0] - 20, pos[1] - t['r'] - 15, bar_w * hp_pct, 8))
                elif self.state == "MODE4":
                    color = COLOR_BLUE if t['type'] == 'CENTER' else COLOR_ORANGE
                elif self.state == "MODE6":
                    if t.get('is_heart'):       color = COLOR_HEART
                    elif t.get('is_lightning'): color = COLOR_LIGHTNING
                    elif t.get('is_reverser'):  color = COLOR_PURPLE
                    elif t.get('shielded'):     color = COLOR_SHIELD
                    else:                       color = COLOR_RED
                else:
                    color = COLOR_RED
                pygame.draw.circle(SCREEN, color, pos, t['r'])
                pygame.draw.circle(SCREEN, (255, 255, 255), pos, t['r'], 2)

                if self.state == "MODE6":
                    if t.get('shielded'):
                        ss = t['r'] * 0.8
                        sp = [(pos[0], pos[1]-ss),(pos[0]-ss*.8,pos[1]-ss*.3),(pos[0]-ss*.8,pos[1]+ss*.3),
                              (pos[0], pos[1]+ss*.6),(pos[0]+ss*.8,pos[1]+ss*.3),(pos[0]+ss*.8,pos[1]-ss*.3)]
                        pygame.draw.polygon(SCREEN, (255, 255, 255), sp, 2)
                    elif t.get('is_heart'):
                        if t.get('_heart_r') != t['r']:
                            s = t['r'] * 0.55
                            cx_h, cy_h = 0, s * 0.1
                            pts = []
                            for i in range(33):
                                a = (i / 32) * 2 * math.pi
                                pts.append((cx_h + s*16*(math.sin(a)**3)/16,
                                            cy_h - s*(13*math.cos(a)-5*math.cos(2*a)-2*math.cos(3*a)-math.cos(4*a))/16))
                            t['_heart_pts'] = pts; t['_heart_r'] = t['r']
                        offset_pts = [(pos[0]+px, pos[1]+py) for px,py in t['_heart_pts']]
                        pygame.draw.polygon(SCREEN, (255, 255, 255), offset_pts, 2)
                    elif t.get('is_reverser'):
                        d = t['direction']; ar = t['r'] * 0.55
                        pygame.draw.polygon(SCREEN, (255,255,255), [
                            (pos[0]+d*ar, pos[1]),
                            (pos[0]-d*ar*0.3, pos[1]-ar*0.45),
                            (pos[0]-d*ar*0.3, pos[1]+ar*0.45)], 2)
                    elif t.get('is_lightning'):
                        # Draw ⚡ symbol
                        lx, ly, ls = pos[0], pos[1], int(t['r'] * 0.65)
                        bolt = [(lx+ls*0.2, ly-ls),(lx-ls*0.3, ly),(lx+ls*0.1, ly),
                                (lx-ls*0.2, ly+ls),(lx+ls*0.3, ly),(lx-ls*0.1, ly),(lx+ls*0.2, ly-ls)]
                        pygame.draw.polygon(SCREEN, (255, 255, 255), bolt, 2)

        # ── HUD ─────────────────────────────────────────────────────────────
        accuracy = min(100, (self.hits * 100 // self.total_clicks) if self.total_clicks > 0 else 0)

        if self.state == "MODE9":
            time_left = max(0, 60 - int(time.time() - self.start_time))
            track_pct = int(self.m9_tracking_time * 100 / self.m9_total_stationary_time) \
                        if self.m9_total_stationary_time > 0 else 0
            track_pct = min(100, track_pct)
            hud_key = (time_left, int(self.score), track_pct)
            if hud_key != self._hud_cache_key:
                self._hud_cache = FONT_MD.render(
                    f"Time: {time_left} | Score: {int(self.score)} | Tracking: {track_pct}%",
                    True, COLOR_TEXT)
                self._hud_cache_key = hud_key
            SCREEN.blit(self._hud_cache, (20, 20))
        elif self.state == "MODE6":
            hud_key = (self.lives, int(self.score), accuracy)
            if hud_key != self._hud_cache_key:
                self._hud_cache = FONT_MD.render(
                    f"Lives: {self.lives} | Score: {int(self.score)} | Accuracy: {accuracy}%",
                    True, COLOR_TEXT)
                self._hud_cache_key = hud_key
            SCREEN.blit(self._hud_cache, (20, 20))
        elif self.state == "MODE8":
            avg_rt = (sum(self.m8_reaction_times) / len(self.m8_reaction_times)) if self.m8_reaction_times else 0
            errs = self.m8_false_flicks + self.m8_timeouts
            hud_key = (self.lives, int(self.score), int(avg_rt * 1000), self.hits, errs)
            if hud_key != self._hud_cache_key:
                self._hud_cache = FONT_SM.render(
                    f"Lives: {self.lives} | Score: {int(self.score)} | Good: {self.hits} | "
                    f"Errors: {errs} | Avg RT: {avg_rt * 1000:.0f}ms",
                    True, COLOR_TEXT)
                self._hud_cache_key = hud_key
            SCREEN.blit(self._hud_cache, (20, 20))
        else:
            time_left = max(0, 30 - int(time.time() - self.start_time))
            hud_key = (time_left, int(self.score), accuracy)
            if hud_key != self._hud_cache_key:
                self._hud_cache = FONT_MD.render(
                    f"Time: {time_left} | Score: {int(self.score)} | Accuracy: {accuracy}%",
                    True, COLOR_TEXT)
                self._hud_cache_key = hud_key
            SCREEN.blit(self._hud_cache, (20, 20))

    def draw_gameover(self):
        title = FONT_LG.render("SESSION FINISHED", True, COLOR_TEXT)
        SCREEN.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))

        if self.state == "GAMEOVER" and hasattr(self, '_last_mode') and self._last_mode == "MODE8":
            avg_ms = int(self.m8_avg_rt * 1000)
            errs = self.m8_false_flicks + self.m8_timeouts
            line1 = f"Score: {int(self.score)} | Avg Reaction: {avg_ms}ms"
            line2 = f"Good reactions: {self.hits} | Errors (false safe / too slow): {errs}"
        elif self.state == "GAMEOVER" and hasattr(self, '_last_mode') and self._last_mode == "MODE9":
            track_pct = int(self.m9_tracking_time * 100 / self.m9_total_stationary_time) \
                        if self.m9_total_stationary_time > 0 else 0
            track_pct = min(100, track_pct)
            line1 = f"Final Score: {int(self.score)} | Tracking Accuracy: {track_pct}%"
            line2 = None
        else:
            accuracy = min(100, (self.hits * 100 // self.total_clicks) if self.total_clicks > 0 else 0)
            line1 = f"Final Score: {int(self.score)} | Accuracy: {accuracy}%"
            line2 = None

        score_txt = FONT_MD.render(line1, True, COLOR_ACCENT)
        SCREEN.blit(score_txt, (WIDTH // 2 - score_txt.get_width() // 2, HEIGHT // 3 + 80))
        if line2:
            l2_txt = FONT_MD.render(line2, True, COLOR_ACCENT)
            SCREEN.blit(l2_txt, (WIDTH // 2 - l2_txt.get_width() // 2, HEIGHT // 3 + 130))
        if self.is_high_score:
            hs_txt = FONT_MD.render("NEW HIGH SCORE!", True, (255, 215, 0))
            hs_y = HEIGHT // 3 + (180 if line2 else 130)
            SCREEN.blit(hs_txt, (WIDTH // 2 - hs_txt.get_width() // 2, hs_y))
        info = FONT_SM.render("Press ESC to return to Menu", True, (100, 100, 100))
        SCREEN.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT - 100))


if __name__ == "__main__":
    game = Game()
    while game.running:
        game.handle_input()
        game.update()
        game.draw()
        CLOCK.tick(FPS)
    pygame.quit()