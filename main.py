import pygame
import random
import math
import sys
from managers.game_manager import GameManager, GameState

pygame.init()

screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("SPACE INVADERS")

# ---------------------------------------------------------------------------
# Background: Seamless organic nebula clouds, varied stars & planet
# ---------------------------------------------------------------------------

STAR_LAYERS = [
    {"count": 90, "speed": (0.1, 0.3), "radius": (1, 1), "alpha": (60, 120)},
    {"count": 60, "speed": (0.3, 0.8), "radius": (1, 2), "alpha": (110, 190)},
    {"count": 30, "speed": (0.8, 1.5), "radius": (2, 3), "alpha": (180, 255)},
]

star_colors = [
    (180, 140, 255),  # Light Violet
    (230, 110, 255),  # Pinkish Magenta
    (90, 210, 255),   # Cyan
    (255, 255, 255),  # Pure White
]

def make_star(layer):
    return {
        "x_ratio": random.random(),
        "y_ratio": random.random(),
        "speed": random.uniform(*layer["speed"]),
        "radius": random.randint(*layer["radius"]),
        "color": random.choice(star_colors),
        "alpha_base": random.randint(*layer["alpha"]),
        "twinkle_offset": random.uniform(0, math.tau),
    }

stars = [make_star(layer) for layer in STAR_LAYERS for _ in range(layer["count"])]

def make_radial_gradient(radius, color, max_alpha):
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    steps = 35
    for i in range(steps, 0, -1):
        t = i / steps
        r = int(radius * t)
        alpha = int(max_alpha * (1 - t) ** 2)
        if alpha <= 0 or r <= 0:
            continue
        pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
    return surf

# Organic Custom Nebula Clouds (Replaces tiled light streaks completely)
nebula_clouds = [
    (0.2, 0.3, 300, (80, 20, 130), 50),
    (0.7, 0.4, 380, (110, 30, 160), 45),
    (0.5, 0.8, 280, (25, 90, 150), 35),
]

nebula_surfaces = [
    (make_radial_gradient(rad, col, alpha), x, y, rad)
    for x, y, rad, col, alpha in nebula_clouds
]

_glow_cache = {}
def get_star_glow(radius, color):
    key = (radius, color)
    if key not in _glow_cache:
        _glow_cache[key] = make_radial_gradient(radius * 4, color, max_alpha=80)
    return _glow_cache[key]

# Interactive Cosmic Planet (Intersects background nebula gas)
def draw_planet(radius):
    size = radius * 3
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    center = (size // 2, size // 2)

    # Atmosphere Outer Ring Glow
    for r in range(radius + 20, radius, -1):
        alpha = int(60 * (1 - (r - radius) / 20))
        pygame.draw.circle(surf, (170, 90, 255, alpha), center, r)

    pygame.draw.circle(surf, (35, 18, 60), center, radius)

    # Planet surface detail lines
    band_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(band_surf, (75, 35, 120, 180), (radius, radius), radius)
    pygame.draw.ellipse(band_surf, (120, 60, 180, 120), (10, radius - 20, radius * 1.8, 30))
    surf.blit(band_surf, (size // 2 - radius, size // 2 - radius))

    # Shadow Crescent
    shadow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(shadow_surf, (10, 5, 20, 220), (center[0] + 18, center[1] - 12), radius)
    surf.blit(shadow_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    return surf, size // 2

planet_radius = 90
planet_surf, planet_offset = draw_planet(planet_radius)

shooting_stars = []
SHOOTING_STAR_CHANCE = 0.012

def spawn_shooting_star():
    return {
        "x": random.uniform(0, screen_width * 0.7),
        "y": random.uniform(0, screen_height * 0.3),
        "vx": math.cos(0.5) * random.uniform(10, 15),
        "vy": math.sin(0.5) * random.uniform(10, 15),
        "life": 0,
        "max_life": random.randint(18, 30),
    }

# ---------------------------------------------------------------------------
# Gameplay Entities & State Management (Space Invaders Mechanics)
# ---------------------------------------------------------------------------

class SpaceInvadersGameplay:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.player_x = width // 2
        self.player_speed = 7
        self.player_width = 44
        self.player_height = 40
        
        self.lasers = []
        self.invader_lasers = []
        self.invaders = []
        self.explosions = []
        
        self.score = 0
        self.lives = 3
        self.wave = 1
        self.game_over = False
        self.score_saved = False
        
        self.invader_direction = 1
        self.invader_speed = 1.2
        self.invader_drop = 16
        self.last_shot_time = 0
        self.shoot_cooldown = 200  # milliseconds
        
        self._spawn_invaders()

    def _spawn_invaders(self):
        self.invaders.clear()
        self.invader_lasers.clear()
        rows = min(5, 3 + self.wave // 2)
        cols = 8
        spacing_x = 55
        spacing_y = 45
        start_x = (self.width - (cols * spacing_x)) // 2
        start_y = 70

        for r in range(rows):
            for c in range(cols):
                inv_type = 3 if r == 0 else (2 if r < 3 else 1)
                self.invaders.append({
                    "rect": pygame.Rect(start_x + c * spacing_x, start_y + r * spacing_y, 36, 30),
                    "type": inv_type,
                    "points": inv_type * 10
                })

    def handle_input(self, keys):
        if self.game_over:
            return

        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.player_x > 30:
            self.player_x -= self.player_speed
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.player_x < self.width - 30:
            self.player_x += self.player_speed

        now = pygame.time.get_ticks()
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and now - self.last_shot_time > self.shoot_cooldown:
            player_y = self.height - 60
            self.lasers.append(pygame.Rect(self.player_x - 3, player_y - 15, 6, 16))
            self.last_shot_time = now

    def update(self, db_manager, current_user):
        if self.game_over:
            if not self.score_saved and current_user and db_manager:
                try:
                    db_manager.save_score(current_user["id"], self.score)
                except Exception:
                    pass
                self.score_saved = True
            return

        player_y = self.height - 60
        player_rect = pygame.Rect(self.player_x - self.player_width // 2, player_y - self.player_height // 2, self.player_width, self.player_height)

        # Update Player Lasers
        for laser in self.lasers[:]:
            laser.y -= 10
            if laser.bottom < 0:
                self.lasers.remove(laser)

        # Update Invader Lasers
        for laser in self.invader_lasers[:]:
            laser.y += 6
            if laser.colliderect(player_rect):
                self.invader_lasers.remove(laser)
                self.lives -= 1
                self.explosions.append({"x": self.player_x, "y": player_y, "radius": 1, "max_radius": 30, "color": (255, 100, 100)})
                if self.lives <= 0:
                    self.game_over = True
            elif laser.top > self.height:
                self.invader_lasers.remove(laser)

        # Move Invaders
        move_down = False
        for inv in self.invaders:
            inv["rect"].x += int(self.invader_speed * self.invader_direction)
            if inv["rect"].right >= self.width - 25 or inv["rect"].left <= 25:
                move_down = True

        if move_down:
            self.invader_direction *= -1
            for inv in self.invaders:
                inv["rect"].y += self.invader_drop
                if inv["rect"].bottom >= player_y - 10:
                    self.game_over = True

        # Invader Random Shooting
        if self.invaders and random.random() < 0.02 + (self.wave * 0.005):
            shooter = random.choice(self.invaders)
            self.invader_lasers.append(pygame.Rect(shooter["rect"].centerx - 2, shooter["rect"].bottom, 5, 12))

        # Check Laser Collision with Invaders
        for laser in self.lasers[:]:
            for inv in self.invaders[:]:
                if laser.colliderect(inv["rect"]):
                    if laser in self.lasers:
                        self.lasers.remove(laser)
                    if inv in self.invaders:
                        self.score += inv["points"]
                        self.explosions.append({"x": inv["rect"].centerx, "y": inv["rect"].centery, "radius": 1, "max_radius": 18, "color": (220, 120, 255)})
                        self.invaders.remove(inv)
                    break

        # Check Wave Clear
        if not self.invaders:
            self.wave += 1
            self.invader_speed += 0.4
            self._spawn_invaders()

        # Update Explosion Particles
        for exp in self.explosions[:]:
            exp["radius"] += 2
            if exp["radius"] >= exp["max_radius"]:
                self.explosions.remove(exp)

    def draw(self, screen, scale):
        player_y = self.height - 60

        # Draw Explosions
        for exp in self.explosions:
            alpha = max(0, 255 - int((exp["radius"] / exp["max_radius"]) * 255))
            surf = pygame.Surface((exp["radius"] * 2, exp["radius"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*exp["color"], alpha), (exp["radius"], exp["radius"]), exp["radius"])
            screen.blit(surf, (exp["x"] - exp["radius"], exp["y"] - exp["radius"]))

        if not self.game_over:
            # Draw Player Ship
            ship_pts = [
                (self.player_x, player_y - 20),
                (self.player_x + 20, player_y + 15),
                (self.player_x + 10, player_y + 10),
                (self.player_x - 10, player_y + 10),
                (self.player_x - 20, player_y + 15),
            ]
            pygame.draw.polygon(screen, (190, 90, 255), ship_pts)
            pygame.draw.polygon(screen, (255, 255, 255), ship_pts, width=2)
            pygame.draw.circle(screen, (60, 210, 255), (self.player_x, player_y - 2), 5)

        # Draw Player Lasers
        for laser in self.lasers:
            pygame.draw.rect(screen, (255, 100, 255), laser, border_radius=3)
            pygame.draw.rect(screen, (255, 255, 255), laser.inflate(-2, -2), border_radius=2)

        # Draw Invader Lasers
        for laser in self.invader_lasers:
            pygame.draw.rect(screen, (255, 60, 60), laser, border_radius=2)

        # Draw Invaders
        for inv in self.invaders:
            r = inv["rect"]
            color = (255, 80, 180) if inv["type"] == 3 else ((120, 220, 255) if inv["type"] == 2 else (180, 100, 255))
            pygame.draw.rect(screen, color, r, border_radius=6)
            pygame.draw.rect(screen, (255, 255, 255), r, width=1, border_radius=6)
            # Eyes
            pygame.draw.circle(screen, (10, 5, 20), (r.x + 10, r.y + 12), 3)
            pygame.draw.circle(screen, (10, 5, 20), (r.right - 10, r.y + 12), 3)

        # ------------------------------------------------------------------
        # Modern gameplay HUD
        # ------------------------------------------------------------------
        hud_font = pygame.font.SysFont(
            "arial",
            max(14, int(17 * scale)),
            bold=True,
        )
        small_font = pygame.font.SysFont(
            "arial",
            max(9, int(10 * scale)),
            bold=True,
        )

        panel_height = max(48, int(54 * scale))
        panel = pygame.Surface((self.width, panel_height), pygame.SRCALPHA)
        panel.fill((8, 5, 20, 125))
        pygame.draw.line(
            panel,
            (120, 70, 190, 145),
            (0, panel_height - 1),
            (self.width, panel_height - 1),
            max(1, int(scale)),
        )
        screen.blit(panel, (0, 0))

        score_surf = hud_font.render(
            f"SCORE  {self.score:06d}",
            True,
            (255, 255, 255),
        )
        wave_surf = hud_font.render(
            f"WAVE  {self.wave:02d}",
            True,
            (210, 165, 255),
        )

        lives_text = "● " * self.lives
        lives_surf = hud_font.render(
            lives_text.strip(),
            True,
            (255, 110, 145),
        )

        label_color = (130, 112, 158)
        score_label = small_font.render("MISSION SCORE", True, label_color)
        wave_label = small_font.render("CURRENT WAVE", True, label_color)
        lives_label = small_font.render("HULL STATUS", True, label_color)

        left_x = int(28 * scale)
        center_x = self.width // 2
        right_x = self.width - int(28 * scale)

        screen.blit(score_label, (left_x, int(8 * scale)))
        screen.blit(score_surf, (left_x, int(22 * scale)))

        screen.blit(
            wave_label,
            wave_label.get_rect(
                midtop=(center_x, int(8 * scale))
            ),
        )
        screen.blit(
            wave_surf,
            wave_surf.get_rect(
                midtop=(center_x, int(22 * scale))
            ),
        )

        screen.blit(
            lives_label,
            lives_label.get_rect(
                top= int(8 * scale),
                right= right_x,
            ),
        )
        screen.blit(
            lives_surf,
            lives_surf.get_rect(
                top= int(22 * scale),
                right= right_x,
            ),
        )

        # Game-over overlay
        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((6, 3, 16, 205))
            screen.blit(overlay, (0, 0))

            card_width = int(min(self.width * 0.72, 500 * scale))
            card_height = int(210 * scale)
            card = pygame.Surface(
                (card_width, card_height),
                pygame.SRCALPHA,
            )

            pygame.draw.rect(
                card,
                (18, 10, 38, 245),
                card.get_rect(),
                border_radius=int(18 * scale),
            )
            pygame.draw.rect(
                card,
                (255, 76, 112, 190),
                card.get_rect(),
                width=max(2, int(2 * scale)),
                border_radius=int(18 * scale),
            )
            pygame.draw.line(
                card,
                (255, 150, 170, 190),
                (int(24 * scale), int(3 * scale)),
                (card_width - int(24 * scale), int(3 * scale)),
                max(1, int(2 * scale)),
            )

            card_rect = card.get_rect(
                center=(self.width // 2, self.height // 2)
            )
            screen.blit(card, card_rect)

            go_font = pygame.font.SysFont(
                "arial",
                max(28, int(40 * scale)),
                bold=True,
            )
            sub_font = pygame.font.SysFont(
                "arial",
                max(14, int(19 * scale)),
                bold=True,
            )
            hint_font = pygame.font.SysFont(
                "arial",
                max(10, int(12 * scale)),
            )

            go_surf = go_font.render(
                "GAME OVER",
                True,
                (255, 88, 120),
            )
            final_surf = sub_font.render(
                f"FINAL SCORE  {self.score:06d}",
                True,
                (255, 255, 255),
            )
            restart_surf = hint_font.render(
                "ENTER / R  RESTART     •     ESC  RETURN TO MENU",
                True,
                (195, 178, 222),
            )

            screen.blit(
                go_surf,
                go_surf.get_rect(
                    center=(
                        self.width // 2,
                        self.height // 2 - int(48 * scale),
                    )
                ),
            )
            screen.blit(
                final_surf,
                final_surf.get_rect(
                    center=(
                        self.width // 2,
                        self.height // 2 + int(4 * scale),
                    )
                ),
            )
            screen.blit(
                restart_surf,
                restart_surf.get_rect(
                    center=(
                        self.width // 2,
                        self.height // 2 + int(48 * scale),
                    )
                ),
            )

# ---------------------------------------------------------------------------
# Main Loop & Engine Setup
# ---------------------------------------------------------------------------

game = GameManager(screen, screen_width, screen_height)
gameplay = None

clock = pygame.time.Clock()
ticks = 0

running = True
while running:
    ticks += 1
    events = pygame.event.get()
    keys = pygame.key.get_pressed()

    for event in events:
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            screen_width, screen_height = event.w, event.h
            screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
            game.screen = screen
            game.width = screen_width
            game.height = screen_height
            if gameplay:
                gameplay.width = screen_width
                gameplay.height = screen_height

    # Dynamic Mouse Visibility: Naka-hide kapag naglalaro, naka-show kapag nasa Menu/Login
    if game.state == GameState.PLAYING and gameplay and not gameplay.game_over:
        pygame.mouse.set_visible(False)
    else:
        pygame.mouse.set_visible(True)

    screen.fill((10, 5, 20))

    # 1. Render Organic Nebula Clouds (No Tiling)
    for surf, x_ratio, y_ratio, rad in nebula_surfaces:
        screen.blit(surf, (int(screen_width * x_ratio) - rad, int(screen_height * y_ratio) - rad))

    # 2. Render Planet (Asymmetrically anchored on upper right)
    planet_x = int(screen_width * 0.76) - planet_offset
    planet_y = int(screen_height * 0.28) - planet_offset + int(math.sin(ticks * 0.02) * 6)
    screen.blit(planet_surf, (planet_x, planet_y))

    # 3. Layered Twinkling Stars
    for star in stars:
        star["y_ratio"] += star["speed"] / screen_height
        if star["y_ratio"] > 1.0:
            star["y_ratio"] = 0.0
            star["x_ratio"] = random.random()

        px = int(star["x_ratio"] * screen_width)
        py = int(star["y_ratio"] * screen_height)

        twinkle = (math.sin(ticks * 0.05 + star["twinkle_offset"]) + 1) / 2

        glow = get_star_glow(star["radius"], star["color"])
        glow_rect = glow.get_rect(center=(px, py))
        glow.set_alpha(int(120 * (0.3 + 0.7 * twinkle)))
        screen.blit(glow, glow_rect)

        core_color = tuple(min(255, int(c * (0.6 + 0.4 * twinkle))) for c in star["color"])
        pygame.draw.circle(screen, core_color, (px, py), star["radius"])

    # 4. Shooting Stars
    if random.random() < SHOOTING_STAR_CHANCE and len(shooting_stars) < 3:
        shooting_stars.append(spawn_shooting_star())

    for s in shooting_stars[:]:
        s["x"] += s["vx"]
        s["y"] += s["vy"]
        s["life"] += 1

        fade = max(0, 1 - (s["life"] / s["max_life"]))
        end_pos = (s["x"] - s["vx"] * 1.5, s["y"] - s["vy"] * 1.5)

        streak_surf = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        pygame.draw.line(streak_surf, (255, 220, 255, int(220 * fade)), (s["x"], s["y"]), end_pos, 2)
        screen.blit(streak_surf, (0, 0))

        if s["life"] >= s["max_life"] or s["x"] > screen_width or s["y"] > screen_height:
            shooting_stars.remove(s)

    # 5. UI & Gameplay Render Integration
    game.update(events)

    if game.state == GameState.PLAYING:
        # Initialize or reset gameplay session when entering PLAYING state
        if gameplay is None:
            gameplay = SpaceInvadersGameplay(screen_width, screen_height)

        # Handle Restart or Return to Menu on Game Over
        if gameplay.game_over:
            if keys[pygame.K_RETURN] or keys[pygame.K_r]:
                gameplay = SpaceInvadersGameplay(screen_width, screen_height)
            elif keys[pygame.K_ESCAPE]:
                game.state = GameState.MENU
                gameplay = None

        if gameplay:
            gameplay.handle_input(keys)
            gameplay.update(game.db if hasattr(game, "db") else None, game.current_user if hasattr(game, "current_user") else None)
            gameplay.draw(screen, game._get_scale() if hasattr(game, "_get_scale") else 1.0)
    else:
        gameplay = None
        game.render()

    pygame.display.update()
    clock.tick(60)

pygame.quit()
sys.exit()