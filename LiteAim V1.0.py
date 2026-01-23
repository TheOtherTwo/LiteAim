import pygame
import random
import math
import time
import json
import os
import numpy as np

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
INFO = pygame.display.Info()
WIDTH, HEIGHT = INFO.current_w, INFO.current_h
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Pro Aim Trainer Ultimate")
CLOCK = pygame.time.Clock()
FPS = 144

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

FONT_LG = pygame.font.SysFont("Arial", 60, bold=True)
FONT_MD = pygame.font.SysFont("Arial", 40)
FONT_SM = pygame.font.SysFont("Arial", 24)

SCORE_FILE = "highscores.json"
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
        arr[i] = [int(amplitude), int(amplitude)]
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
        arr[i] = [int(amplitude), int(amplitude)]
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
        arr[i] = [int(amplitude), int(amplitude)]
    return pygame.sndarray.make_sound(arr)


POP_SOUND = generate_pop_sound()
SHIELD_BREAK_SOUND = generate_shield_break_sound()
TRACKING_SOUND = generate_tracking_sound()


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
            alpha = int(255 * self.life)
            size = int(3 * self.life)
            pygame.draw.circle(surface, (*self.color[:3], alpha), (int(self.x), int(self.y)), size)


class DataManager:
    @staticmethod
    def load_scores():
        if not os.path.exists(SCORE_FILE):
            return {}
        try:
            with open(SCORE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}

    @staticmethod
    def save_score(mode, score):
        data = DataManager.load_scores()
        if score > data.get(mode, 0):
            data[mode] = score
            with open(SCORE_FILE, 'w') as f:
                json.dump(data, f)
            return True
        return False


class Button:
    def __init__(self, x, y, w, h, text, action_code):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action_code
        self.hovered = False

    def draw(self, surface):
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
    def __init__(self, x, y, w, min_val, max_val, current, label):
        self.rect = pygame.Rect(x, y, w, 20)
        self.min = min_val
        self.max = max_val
        self.val = current
        self.label = label
        self.dragging = False
        self.handle_rect = pygame.Rect(0, y - 5, 10, 30)
        self.update_handle()

    def update_handle(self):
        ratio = (self.val - self.min) / (self.max - self.min)
        self.handle_rect.centerx = self.rect.x + (self.rect.width * ratio)

    def update(self, mouse_pos, click_held):
        if self.handle_rect.collidepoint(mouse_pos) and click_held:
            self.dragging = True
        if not click_held:
            self.dragging = False
        if self.dragging:
            rel_x = mouse_pos[0] - self.rect.x
            ratio = max(0, min(1, rel_x / self.rect.width))
            self.val = self.min + (self.max - self.min) * ratio
            self.update_handle()
        return self.val

    def draw(self, surface):
        val_surf = FONT_SM.render(f"{self.label}: {self.val:.1f}", True, COLOR_TEXT)
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

        self.crosshair_size = 15
        self.crosshair_color = COLOR_ACCENT
        self.crosshair_width = 2
        self.crosshair_gap = 5
        self.crosshair_dot = True

        self.slider = Slider(WIDTH // 2 - 150, HEIGHT - 210, 300, 0.1, 5.0, 1.0, "Sensitivity")
        self.volume_slider = Slider(WIDTH // 2 - 150, HEIGHT - 150, 300, 0.0, 1.0, 0.5, "Volume")

        btn_w, btn_h = 240, 60
        gap_x, gap_y = 20, 20
        start_x = WIDTH // 2 - btn_w - gap_x // 2
        start_y = HEIGHT // 2 - 150

        self.buttons = [
            Button(start_x, start_y, btn_w, btn_h, "1. Reflex Click", "START_1"),
            Button(start_x + btn_w + gap_x, start_y, btn_w, btn_h, "2. Smooth Tracking", "START_2"),
            Button(start_x, start_y + btn_h + gap_y, btn_w, btn_h, "3. Gridshot", "START_3"),
            Button(start_x + btn_w + gap_x, start_y + btn_h + gap_y, btn_w, btn_h, "4. Micro-Flick", "START_4"),
            Button(start_x, start_y + (btn_h + gap_y) * 2, btn_w, btn_h, "5. Target Switch", "START_5"),
            Button(start_x + btn_w + gap_x, start_y + (btn_h + gap_y) * 2, btn_w, btn_h, "6. Pressure", "START_6"),
            Button(WIDTH // 2 - 100, HEIGHT - 280, 200, 40, "Difficulty: Medium", "TOGGLE_DIFF"),
            Button(WIDTH // 2 - 100, HEIGHT - 80, 200, 50, "Crosshair", "CROSSHAIR"),
            Button(WIDTH // 2 + 110, HEIGHT - 80, 200, 50, "Exit", "EXIT")
        ]

        self.targets = []
        self.score = 0
        self.start_time = 0
        self.is_high_score = False
        self.hits = 0
        self.total_clicks = 0
        self.micro_state = 0
        self.lives = 3
        self.last_spawn = 0
        self.last_dir_change = 0
        self.base_fall_speed = 200
        self.speed_multiplier = 1.0
        self.last_life_count = 3
        self.last_heart_spawn = 0
        self.last_angle = 0
        self.last_tracking_sound = 0

        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        self.update_volume()

    def update_volume(self):
        pygame.mixer.music.set_volume(self.volume)
        POP_SOUND.set_volume(self.volume)
        SHIELD_BREAK_SOUND.set_volume(self.volume)
        TRACKING_SOUND.set_volume(self.volume)

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
        self.targets = [{'pos': (WIDTH // 2, HEIGHT // 2), 'r': 15, 'type': 'CENTER'}]

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
        self.spawn_target_mode6()

    def get_r_mode1(self):
        return [40, 25, 15][self.difficulty - 1]

    def get_diff_params_mode2(self):
        if self.difficulty == 1: return 45, 0, 150, 1500, math.pi / 2
        if self.difficulty == 2: return 30, 0, 250, 1000, math.pi / 2
        if self.difficulty == 3: return 25, 0, 300, 2000, math.pi / 3
        return 30, 0, 250, 1000, math.pi / 2

    def get_r_mode3(self):
        return [50, 40, 25][self.difficulty - 1]

    def get_mode4_params(self):
        if self.difficulty == 1: return 15, 100
        if self.difficulty == 2: return 10, 150
        if self.difficulty == 3: return 6, 250
        return 10, 150

    def get_mode5_params(self):
        if self.difficulty == 1: return 40, 80, 25
        if self.difficulty == 2: return 30, 140, 40
        if self.difficulty == 3: return 20, 220, 50
        return 30, 140, 40

    def get_mode6_params(self):
        if self.difficulty == 1: return 40, 200, 1.2, 5
        if self.difficulty == 2: return 30, 250, 0.8, 6
        if self.difficulty == 3: return 32, 250, 0.5, 7  # Made hard mode circles slightly smaller (35 -> 32)
        return 30, 250, 0.8, 6

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
        dist = random.uniform(spread / 2, spread)
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
        x = random.randint(r, WIDTH - r)
        is_heart = False
        if time.time() - self.last_heart_spawn > HEART_SPAWN_COOLDOWN and random.random() < 0.05:
            is_heart = True
            self.last_heart_spawn = time.time()
        has_shield = (self.difficulty == 3 and random.random() < 0.15)
        self.targets.append({
            'pos': [x, -r],
            'r': r,
            'has_shield': has_shield and not is_heart,
            'shielded': has_shield and not is_heart,
            'is_heart': is_heart
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
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.state == "MENU":
                        self.handle_menu_click()
                        self.slider.update(self.virtual_mouse, True)
                        self.volume_slider.update(self.virtual_mouse, True)
                    elif self.state == "CROSSHAIR":
                        self.handle_crosshair_click()
                    elif self.state in ["MODE1", "MODE3", "MODE4", "MODE6"]:
                        self.handle_click_modes()
            if event.type == pygame.MOUSEBUTTONUP:
                if self.state == "MENU":
                    self.slider.update(self.virtual_mouse, False)
                    self.volume_slider.update(self.virtual_mouse, False)

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
        colors = [(COLOR_ACCENT, "Cyan"), (COLOR_RED, "Red"), (COLOR_GREEN, "Green"), (COLOR_ORANGE, "Orange")]
        for i, (color, name) in enumerate(colors):
            color_rect = pygame.Rect(WIDTH // 2 - 200 + i * 100, HEIGHT // 2, 80, 30)
            if color_rect.collidepoint(mx, my):
                self.crosshair_color = color

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
                    self.targets = [{'pos': (WIDTH // 2, HEIGHT // 2), 'r': 15, 'type': 'CENTER'}]
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

    def update(self):
        dt = CLOCK.get_time() / 1000.0

        self.particles = [p for p in self.particles if p.life > 0]
        for particle in self.particles:
            particle.update()

        if self.state == "MENU":
            self.sensitivity = self.slider.update(self.virtual_mouse, pygame.mouse.get_pressed()[0])
            old_volume = self.volume
            self.volume = self.volume_slider.update(self.virtual_mouse, pygame.mouse.get_pressed()[0])
            if old_volume != self.volume:
                self.update_volume()
            for btn in self.buttons: btn.check_hover(self.virtual_mouse)

        elif self.state == "MODE2":
            self.update_mode2(dt)
        elif self.state == "MODE5":
            self.update_mode5(dt)
        elif self.state == "MODE6":
            self.update_mode6(dt)

        if self.state in ["MODE1", "MODE2", "MODE3", "MODE4", "MODE5"]:
            if time.time() - self.start_time > 30:
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
        r, base_fall_speed, spawn_rate, _ = self.get_mode6_params()
        if self.lives < self.last_life_count:
            self.speed_multiplier = 1.0
            self.last_life_count = self.lives
        self.speed_multiplier = min(2.0, self.speed_multiplier + 0.02 * dt)
        actual_fall_speed = base_fall_speed * self.speed_multiplier
        if time.time() - self.last_spawn > spawn_rate:
            self.spawn_target_mode6()
            self.last_spawn = time.time()
        for t in self.targets[:]:
            t['pos'][1] += actual_fall_speed * dt
            if t['pos'][1] > HEIGHT + r:
                self.lives -= 1
                self.targets.remove(t)
                if self.lives <= 0:
                    self.finish_game()

    def finish_game(self):
        self.is_high_score = DataManager.save_score(self.state.lower(), int(self.score))
        self.state = "GAMEOVER"

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

        # Draw only the dot crosshair
        pygame.draw.circle(SCREEN, self.crosshair_color, (cx, cy), 3)

        pygame.display.flip()

    def draw_menu(self):
        title = FONT_LG.render("ULTIMATE AIM TRAINER", True, COLOR_ACCENT)
        SCREEN.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
        scores = DataManager.load_scores()
        s_txt = f"Highscores -> Reflex: {scores.get('mode1', 0)} | Track: {scores.get('mode2', 0)} | Grid: {scores.get('mode3', 0)}"
        s_surf = FONT_SM.render(s_txt, True, (150, 150, 150))
        SCREEN.blit(s_surf, (WIDTH // 2 - s_surf.get_width() // 2, 160))
        for btn in self.buttons: btn.draw(SCREEN)
        self.slider.draw(SCREEN)
        self.volume_slider.draw(SCREEN)

    def draw_crosshair_menu(self):
        title = FONT_LG.render("CROSSHAIR COLOR", True, COLOR_ACCENT)
        SCREEN.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 100))

        colors = [(COLOR_ACCENT, "Cyan"), (COLOR_RED, "Red"), (COLOR_GREEN, "Green"), (COLOR_ORANGE, "Orange")]
        for i, (color, name) in enumerate(colors):
            color_rect = pygame.Rect(WIDTH // 2 - 200 + i * 100, HEIGHT // 2, 80, 30)
            pygame.draw.rect(SCREEN, color, color_rect, border_radius=5)
            if color == self.crosshair_color:
                pygame.draw.rect(SCREEN, (255, 255, 255), color_rect, 3, border_radius=5)
            else:
                pygame.draw.rect(SCREEN, (100, 100, 100), color_rect, 2, border_radius=5)

        preview_text = FONT_SM.render("Preview:", True, COLOR_TEXT)
        SCREEN.blit(preview_text, (WIDTH // 2 - 250, HEIGHT // 2 + 80))
        preview_x, preview_y = WIDTH // 2, HEIGHT // 2 + 150
        # Draw only the dot in preview
        pygame.draw.circle(SCREEN, self.crosshair_color, (preview_x, preview_y), 3)

        back_text = FONT_SM.render("Press ESC to return", True, (150, 150, 150))
        SCREEN.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, HEIGHT - 50))

    def draw_game(self):
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
                if t.get('is_heart', False):
                    color = COLOR_HEART
                elif t.get('shielded', False):
                    color = COLOR_SHIELD
                else:
                    color = COLOR_RED
            else:
                color = COLOR_RED
            pygame.draw.circle(SCREEN, color, pos, t['r'])
            pygame.draw.circle(SCREEN, (255, 255, 255), pos, t['r'], 2)
            if self.state == "MODE6" and t.get('shielded', False):
                shield_size = t['r'] * 0.8
                shield_points = [
                    (pos[0], pos[1] - shield_size),
                    (pos[0] - shield_size * 0.8, pos[1] - shield_size * 0.3),
                    (pos[0] - shield_size * 0.8, pos[1] + shield_size * 0.3),
                    (pos[0], pos[1] + shield_size * 0.6),
                    (pos[0] + shield_size * 0.8, pos[1] + shield_size * 0.3),
                    (pos[0] + shield_size * 0.8, pos[1] - shield_size * 0.3)
                ]
                pygame.draw.polygon(SCREEN, (255, 255, 255), shield_points, 2)
            if self.state == "MODE6" and t.get('is_heart', False):
                heart_size = t['r'] * 0.7
                pygame.draw.arc(SCREEN, (255, 255, 255),
                                (pos[0] - heart_size, pos[1] - heart_size / 2, heart_size, heart_size),
                                math.pi, 0, 2)
                pygame.draw.arc(SCREEN, (255, 255, 255),
                                (pos[0], pos[1] - heart_size / 2, heart_size, heart_size),
                                math.pi, 0, 2)
                pygame.draw.polygon(SCREEN, (255, 255, 255), [
                    (pos[0] - heart_size, pos[1]),
                    (pos[0], pos[1] + heart_size),
                    (pos[0] + heart_size, pos[1])
                ], 2)

        # Calculate accuracy
        accuracy = 0
        if self.total_clicks > 0:
            accuracy = int((self.hits / self.total_clicks) * 100)

        if self.state == "MODE6":
            hud = FONT_MD.render(f"Lives: {self.lives} | Score: {int(self.score)} | Accuracy: {accuracy}%", True,
                                 COLOR_TEXT)
        else:
            time_left = max(0, 30 - int(time.time() - self.start_time))
            hud = FONT_MD.render(f"Time: {time_left} | Score: {int(self.score)} | Accuracy: {accuracy}%", True,
                                 COLOR_TEXT)
        SCREEN.blit(hud, (20, 20))

    def draw_gameover(self):
        title = FONT_LG.render("SESSION FINISHED", True, COLOR_TEXT)
        SCREEN.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))

        # Calculate final accuracy
        accuracy = 0
        if self.total_clicks > 0:
            accuracy = int((self.hits / self.total_clicks) * 100)

        score_txt = FONT_MD.render(f"Final Score: {int(self.score)} | Accuracy: {accuracy}%", True, COLOR_ACCENT)
        SCREEN.blit(score_txt, (WIDTH // 2 - score_txt.get_width() // 2, HEIGHT // 3 + 80))
        if self.is_high_score:
            hs_txt = FONT_MD.render("NEW HIGH SCORE!", True, (255, 215, 0))
            SCREEN.blit(hs_txt, (WIDTH // 2 - hs_txt.get_width() // 2, HEIGHT // 3 + 130))
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