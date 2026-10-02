from __future__ import annotations

import math
import random
import pygame
from utils.font_manager import FontManager
from utils.constants import GameState

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Colors
_BLACK = (3, 2, 15)
_VIOLET = (140, 70, 200)
_PURPLE_BORDER = (195, 110, 255)
_NEON_CYAN = (80, 230, 255)
_WHITE = (255, 255, 255)
_RED_ALERT = (255, 80, 80)
_MAGENTA_GLOW = (220, 70, 200)


class LoginScene:
    def __init__(self, game_manager) -> None:
        self.game_manager = game_manager
        self.width = game_manager.width
        self.height = game_manager.height
        
        self.fade_alpha = 255
        self.float_timer = 0.0
        self.galaxy_timer = 0.0
        
        # Local galaxy & starfield elements for deep space immersion
        self.galaxy_stars = []
        self.galaxy_dust = []
        self.galaxy_nebulae = []
        self.local_shooting_stars = []
        self._init_galaxy_environment()

        # Load assets once
        try:
            self.raw_panel_image = pygame.image.load("assets/image/text/System_Login.png").convert_alpha()
        except Exception:
            self.raw_panel_image = None
            
        try:
            self.raw_profile_icon = pygame.image.load("assets/image/elements/Profile_icon.png").convert_alpha()
        except Exception:
            self.raw_profile_icon = None
            
        try:
            self.raw_padlock_icon = pygame.image.load("assets/image/elements/padlock.png").convert_alpha()
        except Exception:
            self.raw_padlock_icon = None
            
        # Cached scaled assets to prevent lag
        self._cached_scale = -1
        self._scaled_panel = None
        self._scaled_profile_icon = None
        self._scaled_padlock_icon = None
        
        # Text fields
        self.username = ""
        self.password = ""
        self.active_field = "username"
        
        # Cursor & Selection state
        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.selection_active = False
        self.show_password = False
        
        # Popups
        self.show_success_popup = False
        self.show_unregistered_popup = False
        
        # Rects
        self.username_rect = pygame.Rect(0, 0, 0, 0)
        self.password_rect = pygame.Rect(0, 0, 0, 0)
        self.show_toggle_rect = pygame.Rect(0, 0, 0, 0)
        self.submit_rect = pygame.Rect(0, 0, 0, 0)
        self.back_rect = pygame.Rect(0, 0, 0, 0)
        self.register_link_rect = pygame.Rect(0, 0, 0, 0)
        self.popup_ok_rect = pygame.Rect(0, 0, 0, 0)

    def _init_galaxy_environment(self) -> None:
        # Reduced balanced background stars (cleaner, less cluttered)
        for _ in range(65):
            self.galaxy_stars.append({
                "x": random.randint(0, self.width),
                "y": random.randint(0, self.height),
                "size": random.choice([1, 1, 2]),
                "speed": random.uniform(0.05, 0.3),
                "brightness": random.randint(100, 200),
                "twinkle_speed": random.uniform(0.01, 0.04),
                "twinkle_offset": random.uniform(0, math.pi * 2)
            })

        # Downward-falling space dust particles for clear visibility
        for _ in range(45):
            self.galaxy_dust.append({
                "x": random.randint(0, self.width),
                "y": random.randint(0, self.height),
                "radius": random.uniform(1.5, 3.5),
                "speed_y": random.uniform(0.5, 1.8),  # Falling downward
                "drift_x": random.uniform(-0.2, 0.2),  # Gentle horizontal sway
                "color": random.choice([(_VIOLET), (_NEON_CYAN), (_MAGENTA_GLOW), (_WHITE)]),
                "alpha": random.randint(90, 190)       # More visible opacity
            })

        # Drifting nebula clouds for galaxy depth
        for _ in range(5):
            self.galaxy_nebulae.append({
                "x": random.randint(0, self.width),
                "y": random.randint(0, self.height),
                "radius": random.randint(180, 320),
                "color": random.choice([(70, 20, 100), (20, 50, 100), (90, 30, 90)]),
                "speed_x": random.uniform(-0.05, 0.05),
                "speed_y": random.uniform(0.02, 0.08)
            })

    def _update_asset_cache(self, scale: float, panel_w: int, panel_h: int) -> None:
        if self._cached_scale != scale:
            self._cached_scale = scale
            
            if self.raw_panel_image:
                self._scaled_panel = pygame.transform.smoothscale(self.raw_panel_image, (panel_w, panel_h))
            else:
                self._scaled_panel = None
                
            icon_size = max(20, int(42 * scale * 0.55))
            if self.raw_profile_icon:
                self._scaled_profile_icon = pygame.transform.smoothscale(self.raw_profile_icon, (icon_size, icon_size))
            else:
                self._scaled_profile_icon = None
                
            if self.raw_padlock_icon:
                self._scaled_padlock_icon = pygame.transform.smoothscale(self.raw_padlock_icon, (icon_size, icon_size))
            else:
                self._scaled_padlock_icon = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            
            if self.show_success_popup:
                if self.popup_ok_rect.collidepoint(pos):
                    self.game_manager.state = GameState.PLAYING
                    self.game_manager.current_scene = None
                return

            if self.show_unregistered_popup:
                if self.popup_ok_rect.collidepoint(pos):
                    self.show_unregistered_popup = False
                return

            if self.back_rect.collidepoint(pos):
                self.game_manager.current_scene = None
                self.game_manager.fade_alpha = 150
                return

            if self.show_toggle_rect.collidepoint(pos):
                self.show_password = not self.show_password
                return

            if self.username_rect.collidepoint(pos):
                self.active_field = "username"
                self.selection_active = False
            elif self.password_rect.collidepoint(pos):
                self.active_field = "password"
                self.selection_active = False
            elif self.submit_rect.collidepoint(pos):
                if self.username.strip() and self.password.strip():
                    if self.username.lower() == "unregistered" or len(self.username) < 4:
                        self.show_unregistered_popup = True
                    else:
                        self.show_success_popup = True
            elif self.register_link_rect.collidepoint(pos):
                print("Redirect to Register Page clicked")

        elif event.type == pygame.KEYDOWN:
            if self.show_success_popup or self.show_unregistered_popup:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.show_success_popup:
                        self.game_manager.state = GameState.PLAYING
                        self.game_manager.current_scene = None
                    else:
                        self.show_unregistered_popup = False
                return

            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_CTRL and event.key == pygame.K_a:
                self.selection_active = True
                return

            target_text = self.username if self.active_field == "username" else self.password

            if event.key == pygame.K_BACKSPACE:
                if self.selection_active:
                    target_text = ""
                    self.selection_active = False
                else:
                    target_text = target_text[:-1]
            elif event.key == pygame.K_TAB:
                self.active_field = "password" if self.active_field == "username" else "username"
                self.selection_active = False
            elif event.key == pygame.K_RETURN:
                if self.username.strip() and self.password.strip():
                    if self.username.lower() == "unregistered" or len(self.username) < 4:
                        self.show_unregistered_popup = True
                    else:
                        self.show_success_popup = True
            else:
                if event.unicode and event.unicode.isprintable():
                    if self.selection_active:
                        target_text = ""
                        self.selection_active = False
                    
                    if len(target_text) < 25:
                        target_text += event.unicode

            if self.active_field == "username":
                self.username = target_text
            else:
                self.password = target_text

    def update(self) -> None:
        self.width = self.game_manager.width
        self.height = self.game_manager.height
        
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 15)
            
        self.float_timer += 0.05
        self.galaxy_timer += 0.03
        self.cursor_timer += 0.03
        if self.cursor_timer >= 1.0:
            self.cursor_timer = 0.0
            self.cursor_visible = not self.cursor_visible

        if hasattr(self.game_manager, "ticks"):
            self.game_manager.ticks += 1
        else:
            setattr(self.game_manager, "ticks", 0)

        # Update galaxy stars movement
        for star in self.galaxy_stars:
            star["y"] += star["speed"]
            if star["y"] > self.height:
                star["y"] = 0
                star["x"] = random.randint(0, self.width)

        # Update downward-falling space dust particles
        for dust in self.galaxy_dust:
            dust["y"] += dust["speed_y"]
            dust["x"] += dust["drift_x"]
            if dust["y"] > self.height:
                dust["y"] = -10
                dust["x"] = random.randint(0, self.width)
            if dust["x"] < 0:
                dust["x"] = self.width
            elif dust["x"] > self.width:
                dust["x"] = 0

        # Update drifting nebulae
        for neb in self.galaxy_nebulae:
            neb["x"] += neb["speed_x"]
            neb["y"] += neb["speed_y"]
            if neb["y"] > self.height + neb["radius"]:
                neb["y"] = -neb["radius"]
                neb["x"] = random.randint(0, self.width)

        # Controlled frequency shooting stars
        if not getattr(self.game_manager, "shooting_stars", []) and random.random() < 0.015:
            self.local_shooting_stars.append({
                "x": random.randint(0, self.width),
                "y": random.randint(0, self.height // 2),
                "length": random.randint(90, 160),
                "speed": random.randint(12, 18),
                "alpha": 255
            })

        for ss in self.local_shooting_stars[:]:
            ss["x"] += ss["speed"]
            ss["y"] += ss["speed"] // 2
            ss["alpha"] -= 6
            if ss["alpha"] <= 0 or ss["x"] > self.width or ss["y"] > self.height:
                self.local_shooting_stars.remove(ss)

        for shooting_star in getattr(self.game_manager, "shooting_stars", []):
            if hasattr(shooting_star, "update"):
                shooting_star.update(self.width, self.height)

        for laser in getattr(self.game_manager, "bg_lasers", []):
            if hasattr(laser, "update"):
                laser.update(self.width, self.height)

    def draw(self, surface: pygame.Surface | None = None) -> None:
        surface = surface or self.game_manager.screen
        self.game_manager.default_page.render_background()
        self._render_starfield_effects()
        self._render_title_image_top()

        s = self.game_manager._get_scale()
        
        # Slightly increased base panel width and height for a bigger, comfortable layout
        panel_w = min(int(680 * s), int(self.width * 0.88))
        panel_h = min(int(630 * s), int(self.height * 0.88))
        
        self._update_asset_cache(s, panel_w, panel_h)

        panel_x = (self.width - panel_w) // 2
        float_offset = int(math.sin(self.float_timer) * (6 * s))
        panel_y = ((self.height - panel_h) // 2) + int(15 * s) + float_offset
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        if self._scaled_panel:
            surface.blit(self._scaled_panel, panel_rect.topleft)
        else:
            panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            c_cut = min(20, panel_w // 4, panel_h // 4)
            panel_points = [
                (c_cut, 0), (panel_w - c_cut, 0), (panel_w, c_cut),
                (panel_w, panel_h - c_cut), (panel_w - c_cut, panel_h),
                (c_cut, panel_h), (0, panel_h - c_cut), (0, c_cut)
            ]
            pygame.draw.polygon(panel_surf, (45, 30, 75, 200), panel_points)
            pygame.draw.polygon(panel_surf, _PURPLE_BORDER, panel_points, width=max(1, int(2 * s)))
            surface.blit(panel_surf, panel_rect.topleft)

        field_w = int(panel_w * 0.62)
        field_h = max(38, int(48 * s))
        field_x = panel_rect.centerx - field_w // 2

        # Username Input (adjusted vertical offsets for the slightly larger panel)
        self.username_rect = pygame.Rect(field_x, panel_rect.top + int(220 * s), field_w, field_h)
        self._draw_cyber_input(
            surface, self.username_rect, self.username, "username", 
            is_active=(self.active_field == "username"), is_password=False, 
            icon_img=self._scaled_profile_icon, scale=s
        )

        # Password Input
        self.password_rect = pygame.Rect(field_x, panel_rect.top + int(295 * s), field_w, field_h)
        self._draw_cyber_input(
            surface, self.password_rect, self.password, "password", 
            is_active=(self.active_field == "password"), is_password=not self.show_password, 
            icon_img=self._scaled_padlock_icon, scale=s, has_show_toggle=True
        )

        # Submit Button
        btn_w = int(field_w * 0.8)
        btn_h = max(38, int(45 * s))
        self.submit_rect = pygame.Rect(panel_rect.centerx - btn_w // 2, panel_rect.top + int(380 * s), btn_w, btn_h)
        
        mouse_pos = pygame.mouse.get_pos()
        btn_hovered = self.submit_rect.collidepoint(mouse_pos)
        btn_fill = (65, 32, 110) if btn_hovered else (48, 22, 85)
        btn_border = _NEON_CYAN if btn_hovered else _PURPLE_BORDER
        
        self._draw_cut_corner_rect(surface, self.submit_rect, fill=btn_fill, border=btn_border, scale=s, cut=8)
        
        btn_font = FontManager.get_font(max(12, int(15 * s)), bold=True)
        btn_text = btn_font.render("→   LOG IN", True, _WHITE)
        surface.blit(btn_text, btn_text.get_rect(center=self.submit_rect.center))

        # Register Link
        link_font = FontManager.get_font(max(10, int(12 * s)), bold=False)
        link_text_surf = link_font.render("Haven't registered to Space Invader yet? ", True, (210, 195, 235))
        click_text_surf = link_font.render("Click Here!  >", True, _NEON_CYAN)
        
        total_w = link_text_surf.get_width() + click_text_surf.get_width()
        start_x = panel_rect.centerx - total_w // 2
        link_y = panel_rect.top + int(475 * s)
        
        surface.blit(link_text_surf, (start_x, link_y))
        click_x = start_x + link_text_surf.get_width()
        surface.blit(click_text_surf, (click_x, link_y))
        
        self.register_link_rect = pygame.Rect(click_x, link_y, click_text_surf.get_width(), click_text_surf.get_height())

        # Back Button
        self._draw_back_button(surface, s)

        # Popups
        if self.show_success_popup:
            self._render_popup(surface, s, "Successfully logged in!", "Entering Space Invaders...", _NEON_CYAN)
        elif self.show_unregistered_popup:
            self._render_popup(surface, s, "Account Not Registered!", "Please sign up first before logging in.", _RED_ALERT)

        # Fade Overlay
        if self.fade_alpha > 0:
            fade_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            fade_surf.fill((*_BLACK, self.fade_alpha))
            surface.blit(fade_surf, (0, 0))

    def _render_starfield_effects(self) -> None:
        screen = self.game_manager.screen

        # 1. Render glowing moving galaxy nebula clouds
        for neb in self.galaxy_nebulae:
            neb_surf = pygame.Surface((int(neb["radius"] * 2), int(neb["radius"] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(neb_surf, (*neb["color"], 18), (int(neb["radius"]), int(neb["radius"])), int(neb["radius"]))
            screen.blit(neb_surf, (int(neb["x"] - neb["radius"]), int(neb["y"] - neb["radius"])))

        # 2. Render subtle background stars (non-intrusive)
        manager_stars = getattr(self.game_manager, "stars", [])
        if manager_stars:
            for star in manager_stars:
                star.render(screen, getattr(self.game_manager, "ticks", 0))
        else:
            for star in self.galaxy_stars:
                twinkle = math.sin(self.galaxy_timer * 2 + star["twinkle_offset"]) * 30
                brightness = max(40, min(200, int(star["brightness"] + twinkle)))
                pygame.draw.circle(screen, (brightness, brightness, brightness + 35), (int(star["x"]), int(star["y"])), star["size"])

        # 3. Render downward-falling space dust particles (clearly visible)
        for dust in self.galaxy_dust:
            r = int(dust["radius"])
            dust_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(dust_surf, (*dust["color"], dust["alpha"]), (r + 1, r + 1), r)
            screen.blit(dust_surf, (int(dust["x"] - r), int(dust["y"] - r)))

        # 4. Render shooting stars (infrequent & distinct)
        manager_shooting_stars = getattr(self.game_manager, "shooting_stars", [])
        if manager_shooting_stars:
            for shooting_star in manager_shooting_stars:
                shooting_star.render(screen)
        else:
            for ss in self.local_shooting_stars:
                end_x = ss["x"] - ss["length"]
                end_y = ss["y"] - (ss["length"] // 2)
                trail_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                pygame.draw.line(trail_surf, (255, 255, 255, max(0, min(255, ss["alpha"]))), (ss["x"], ss["y"]), (end_x, end_y), 2)
                screen.blit(trail_surf, (0, 0))

        # 5. Render background lasers if active
        for laser in getattr(self.game_manager, "bg_lasers", []):
            laser.render(screen)

    def _render_title_image_top(self) -> None:
        if self.game_manager.title_image:
            orig_w, orig_h = self.game_manager.title_image.get_size()
            max_w = int(self.width * 0.62)
            max_h = int(self.height * 0.26)
            scale_factor = min(max_w / orig_w, max_h / orig_h)
            target_w = max(1, int(orig_w * scale_factor))
            target_h = max(1, int(orig_h * scale_factor))
            scaled_img = pygame.transform.smoothscale(self.game_manager.title_image, (target_w, target_h))
            
            rect = scaled_img.get_rect(center=(self.width // 2, int(self.height * 0.14)))
            self.game_manager.screen.blit(scaled_img, rect)

    def _draw_cyber_input(self, surface: pygame.Surface, rect: pygame.Rect, text: str, placeholder: str, is_active: bool, is_password: bool, icon_img: pygame.Surface | None, scale: float, has_show_toggle: bool = False) -> None:
        fill_color = (25, 12, 50, 220)
        border_color = _NEON_CYAN if is_active else (160, 95, 230)
        
        field_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        c = 6
        points = [
            (c, 0), (rect.width - c, 0), (rect.width, c),
            (rect.width, rect.height - c), (rect.width - c, rect.height),
            (c, rect.height), (0, rect.height - c), (0, c)
        ]
        pygame.draw.polygon(field_surf, fill_color, points)
        pygame.draw.polygon(field_surf, border_color, points, width=max(1, int(2 * scale)))
        surface.blit(field_surf, rect.topleft)

        icon_w = int(rect.height * 0.95)
        icon_rect = pygame.Rect(rect.left, rect.top, icon_w, rect.height)
        icon_bg_surf = pygame.Surface((icon_rect.width, icon_rect.height), pygame.SRCALPHA)
        pygame.draw.polygon(icon_bg_surf, (45, 20, 80, 200), points)
        pygame.draw.polygon(icon_bg_surf, border_color, points, width=max(1, int(1 * scale)))
        surface.blit(icon_bg_surf, icon_rect.topleft)
        
        if icon_img:
            surface.blit(icon_img, icon_img.get_rect(center=icon_rect.center))

        right_offset_limit = rect.right
        if has_show_toggle:
            toggle_font = FontManager.get_font(max(10, int(12 * scale)), bold=True)
            toggle_str = "HIDE" if self.show_password else "SHOW"
            text_surf_toggle = toggle_font.render(toggle_str, True, _WHITE)
            
            padding_w = int(12 * scale)
            self.show_toggle_rect = pygame.Rect(
                rect.right - text_surf_toggle.get_width() - padding_w - int(6 * scale), 
                rect.top + int(6 * scale), 
                text_surf_toggle.get_width() + padding_w, 
                rect.height - int(12 * scale)
            )
            right_offset_limit = self.show_toggle_rect.left
            
            toggle_hover = self.show_toggle_rect.collidepoint(pygame.mouse.get_pos())
            toggle_bg_color = (70, 35, 120) if toggle_hover else (45, 22, 85)
            
            self._draw_cut_corner_rect(surface, self.show_toggle_rect, fill=toggle_bg_color, border=_NEON_CYAN if toggle_hover else border_color, scale=scale, cut=4)
            surface.blit(text_surf_toggle, text_surf_toggle.get_rect(center=self.show_toggle_rect.center))

        font = FontManager.get_font(max(11, int(13 * scale)), bold=False)
        if not text:
            display_text = placeholder
            color = (170, 150, 200)
        else:
            display_text = ("*" * len(text)) if is_password else text
            color = _WHITE
        
        text_surf = font.render(display_text, True, color)
        text_rect = text_surf.get_rect(midleft=(icon_rect.right + int(14 * scale), rect.centery))
        
        if is_active and self.selection_active and text:
            select_surf = pygame.Surface((text_surf.get_width() + 6, text_surf.get_height() + 4), pygame.SRCALPHA)
            select_surf.fill((80, 150, 255, 100))
            surface.blit(select_surf, (text_rect.x - 3, text_rect.y - 2))

        surface.blit(text_surf, text_rect)

        if is_active and self.cursor_visible and not self.selection_active:
            cursor_x = text_rect.right + 2 if text else (icon_rect.right + int(14 * scale))
            if cursor_x < right_offset_limit - 5:
                pygame.draw.line(surface, _NEON_CYAN, (cursor_x, rect.top + int(10 * scale)), (cursor_x, rect.bottom - int(10 * scale)), width=max(1, int(2 * scale)))

    def _draw_back_button(self, surface: pygame.Surface, scale: float) -> None:
        btn_w = int(110 * scale)
        btn_h = int(40 * scale)
        self.back_rect = pygame.Rect(int(30 * scale), int(28 * scale), btn_w, btn_h)
        
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.back_rect.collidepoint(mouse_pos)
        fill_color = (65, 32, 110, 230) if hovered else (42, 20, 75, 200)
        border_color = _NEON_CYAN if hovered else _PURPLE_BORDER
        
        self._draw_cut_corner_rect(surface, self.back_rect, fill=fill_color, border=border_color, scale=scale, cut=6)
        
        font = FontManager.get_font(max(11, int(13 * scale)), bold=True)
        back_text = font.render("◄  BACK", True, _WHITE)
        surface.blit(back_text, back_text.get_rect(center=self.back_rect.center))

    def _render_popup(self, surface: pygame.Surface, scale: float, main_msg: str, sub_msg: str, border_col) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((3, 2, 15, 180))
        surface.blit(overlay, (0, 0))

        pop_w = min(int(420 * scale), int(self.width * 0.75))
        pop_h = int(180 * scale)
        pop_rect = pygame.Rect((self.width - pop_w) // 2, (self.height - pop_h) // 2, pop_w, pop_h)

        pop_surf = pygame.Surface((pop_w, pop_h), pygame.SRCALPHA)
        pygame.draw.polygon(pop_surf, (45, 22, 85, 240), [
            (15, 0), (pop_w - 15, 0), (pop_w, 15), (pop_w, pop_h - 15),
            (pop_w - 15, pop_h), (15, pop_h), (0, pop_h - 15), (0, 15)
        ])
        pygame.draw.polygon(pop_surf, border_col, [
            (15, 0), (pop_w - 15, 0), (pop_w, 15), (pop_w, pop_h - 15),
            (pop_w - 15, pop_h), (15, pop_h), (0, pop_h - 15), (0, 15)
        ], width=2)
        surface.blit(pop_surf, pop_rect.topleft)

        msg_font = FontManager.get_font(max(12, int(14 * scale)), bold=True)
        msg_surf = msg_font.render(main_msg, True, _WHITE)
        surface.blit(msg_surf, msg_surf.get_rect(center=(pop_rect.centerx, pop_rect.top + int(55 * scale))))

        sub_font = FontManager.get_font(max(10, int(12 * scale)), bold=False)
        sub_surf = sub_font.render(sub_msg, True, (200, 185, 240))
        surface.blit(sub_surf, sub_surf.get_rect(center=(pop_rect.centerx, pop_rect.top + int(85 * scale))))

        btn_w, btn_h = int(100 * scale), int(34 * scale)
        self.popup_ok_rect = pygame.Rect(pop_rect.centerx - btn_w // 2, pop_rect.bottom - int(45 * scale), btn_w, btn_h)
        
        mouse_pos = pygame.mouse.get_pos()
        ok_hover = self.popup_ok_rect.collidepoint(mouse_pos)
        ok_fill = (65, 35, 110) if ok_hover else (48, 24, 90)
        
        self._draw_cut_corner_rect(surface, self.popup_ok_rect, fill=ok_fill, border=border_col, scale=scale, cut=6)
        ok_font = FontManager.get_font(max(11, int(13 * scale)), bold=True)
        ok_text = ok_font.render("OK", True, _WHITE)
        surface.blit(ok_text, ok_text.get_rect(center=self.popup_ok_rect.center))

    def _draw_cut_corner_rect(self, surface: pygame.Surface, rect: pygame.Rect, fill, border, scale: float, cut: int = 12) -> None:
        c = min(cut, rect.width // 4, rect.height // 2)
        points = [
            (rect.left + c, rect.top),
            (rect.right - c, rect.top),
            (rect.right, rect.top + c),
            (rect.right, rect.bottom - c),
            (rect.right - c, rect.bottom),
            (rect.left + c, rect.bottom),
            (rect.left, rect.bottom - c),
            (rect.left, rect.top + c),
        ]
        pygame.draw.polygon(surface, fill[:3], points)
        pygame.draw.polygon(surface, border, points, width=max(1, int(2 * scale)))