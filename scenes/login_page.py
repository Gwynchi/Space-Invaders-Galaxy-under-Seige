from __future__ import annotations

import math
import random
import pygame
from utils.font_manager import FontManager
from utils.constants import GameState

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import RegisterScene/RegisterPage if available in your project structure
try:
    from scenes.register_page import RegisterPage
except ImportError:
    RegisterPage = None

# Colors
_BLACK = (3, 2, 15)
_VIOLET = (140, 70, 200)
_PURPLE_BORDER = (195, 110, 255)
_NEON_CYAN = (80, 230, 255)
_WHITE = (255, 255, 255)
_MAGENTA_GLOW = (220, 70, 200)

# Predefined registered users for validation
REGISTERED_USERS = ["admin", "player1", "commander", "pilot"]


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
        
        # Popup states ("unregistered", "missing_password", "missing_credentials")
        self.active_popup = None
        
        # Rects
        self.username_rect = pygame.Rect(0, 0, 0, 0)
        self.password_rect = pygame.Rect(0, 0, 0, 0)
        self.show_toggle_rect = pygame.Rect(0, 0, 0, 0)
        self.submit_rect = pygame.Rect(0, 0, 0, 0)
        self.back_rect = pygame.Rect(0, 0, 0, 0)
        self.register_link_rect = pygame.Rect(0, 0, 0, 0)
        self.popup_ok_rect = pygame.Rect(0, 0, 0, 0)

    def _init_galaxy_environment(self) -> None:
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

        for _ in range(45):
            self.galaxy_dust.append({
                "x": random.randint(0, self.width),
                "y": random.randint(0, self.height),
                "radius": random.uniform(1.5, 3.5),
                "speed_y": random.uniform(0.5, 1.8),
                "drift_x": random.uniform(-0.2, 0.2),
                "color": random.choice([(_VIOLET), (_NEON_CYAN), (_MAGENTA_GLOW), (_WHITE)]),
                "alpha": random.randint(90, 190)
            })

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
                
            icon_size = max(22, int(46 * scale * 0.55))
            if self.raw_profile_icon:
                self._scaled_profile_icon = pygame.transform.smoothscale(self.raw_profile_icon, (icon_size, icon_size))
            else:
                self._scaled_profile_icon = None
                
            if self.raw_padlock_icon:
                self._scaled_padlock_icon = pygame.transform.smoothscale(self.raw_padlock_icon, (icon_size, icon_size))
            else:
                self._scaled_padlock_icon = None

    def _handle_submission(self) -> None:
        u = self.username.strip()
        p = self.password.strip()
        
        if u and not p:
            self.active_popup = "missing_password"
        elif not u and p:
            self.active_popup = "unregistered"
        elif not u and not p:
            self.active_popup = "missing_credentials"
        else:
            if u.lower() not in REGISTERED_USERS:
                self.active_popup = "unregistered"
            else:
                self.game_manager.state = GameState.MENU
                self.game_manager.current_scene = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            
            if self.active_popup:
                if self.popup_ok_rect.collidepoint(pos):
                    self.active_popup = None
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
                self._handle_submission()
            elif self.register_link_rect.collidepoint(pos):
                if RegisterPage is not None:
                    self.game_manager.current_scene = RegisterPage(self.game_manager)
                else:
                    print("Redirect to Register Page clicked (RegisterPage class not imported)")

        elif event.type == pygame.KEYDOWN:
            if self.active_popup:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.active_popup = None
                return

            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_CTRL and event.key == pygame.K_a:
                self.selection_active = True
                return

            if event.key == pygame.K_TAB:
                self.active_field = "password" if self.active_field == "username" else "username"
                self.selection_active = False
                return

            if event.key == pygame.K_RETURN:
                self._handle_submission()
                return

            if self.active_field == "username":
                if event.key == pygame.K_BACKSPACE:
                    if self.selection_active:
                        self.username = ""
                        self.selection_active = False
                    else:
                        self.username = self.username[:-1]
                else:
                    if event.unicode and event.unicode.isprintable():
                        if self.selection_active:
                            self.username = ""
                            self.selection_active = False
                        if len(self.username) < 25:
                            self.username += event.unicode
            else:
                if event.key == pygame.K_BACKSPACE:
                    if self.selection_active:
                        self.password = ""
                        self.selection_active = False
                    else:
                        self.password = self.password[:-1]
                else:
                    if event.unicode and event.unicode.isprintable():
                        if self.selection_active:
                            self.password = ""
                            self.selection_active = False
                        if len(self.password) < 25:
                            self.password += event.unicode

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

        for star in self.galaxy_stars:
            star["y"] += star["speed"]
            if star["y"] > self.height:
                star["y"] = 0
                star["x"] = random.randint(0, self.width)

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

        for neb in self.galaxy_nebulae:
            neb["x"] += neb["speed_x"]
            neb["y"] += neb["speed_y"]
            if neb["y"] > self.height + neb["radius"]:
                neb["y"] = -neb["radius"]
                neb["x"] = random.randint(0, self.width)

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

    def draw(self, surface: pygame.Surface | None = None) -> None:
        surface = surface or self.game_manager.screen
        self.game_manager.default_page.render_background()
        self._render_starfield_effects()
        self._render_title_image_top()

        s = self.game_manager._get_scale()
        
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

        self._draw_techy_corners(surface, panel_rect, _PURPLE_BORDER, s, length=18)

        field_w = int(panel_w * 0.62)
        field_h = max(42, int(52 * s))
        field_x = panel_rect.centerx - field_w // 2

        # Username Input
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

        # Cyber Submit Button
        btn_w = int(field_w * 0.82)
        btn_h = max(44, int(52 * s))
        self.submit_rect = pygame.Rect(panel_rect.centerx - btn_w // 2, panel_rect.top + int(380 * s), btn_w, btn_h)
        
        mouse_pos = pygame.mouse.get_pos()
        btn_hovered = self.submit_rect.collidepoint(mouse_pos) and (self.active_popup is None)
        
        if btn_hovered:
            btn_fill = (80, 42, 145)
            btn_border = _NEON_CYAN
        else:
            btn_fill = (55, 24, 98)
            btn_border = _PURPLE_BORDER
            
        self._draw_cut_corner_rect(surface, self.submit_rect, fill=btn_fill, border=btn_border, scale=s, cut=10)
        
        inner_sub_rect = self.submit_rect.inflate(-int(4 * s), -int(4 * s))
        pygame.draw.rect(surface, (135, 75, 205), inner_sub_rect, width=1, border_radius=max(3, int(3 * s)))
        
        btn_font = FontManager.get_font(max(14, int(18 * s)), bold=True)
        shadow_surf = btn_font.render("→   L O G   I N", True, (15, 5, 30))
        surface.blit(shadow_surf, shadow_surf.get_rect(center=(self.submit_rect.centerx + 1, self.submit_rect.centery + 1)))
        
        btn_text = btn_font.render("→   L O G   I N", True, _WHITE if btn_hovered else (235, 220, 255))
        surface.blit(btn_text, btn_text.get_rect(center=self.submit_rect.center))

        # Register Link (Larger text layout)
        link_font = FontManager.get_font(max(12, int(15 * s)), bold=False)
        link_text_surf = link_font.render("Haven't registered to Space Invaders? ", True, (210, 195, 235))
        click_text_surf = link_font.render("Click Here!  >", True, _NEON_CYAN)
        
        total_w = link_text_surf.get_width() + click_text_surf.get_width()
        start_x = panel_rect.centerx - total_w // 2
        link_y = panel_rect.top + int(470 * s)
        
        surface.blit(link_text_surf, (start_x, link_y))
        click_x = start_x + link_text_surf.get_width()
        surface.blit(click_text_surf, (click_x, link_y))
        
        self.register_link_rect = pygame.Rect(click_x, link_y, click_text_surf.get_width(), click_text_surf.get_height())

        # Back Button
        self._draw_back_button(surface, s)

        # Active Popup Dialog
        if self.active_popup == "unregistered":
            self._render_popup(surface, s, "Account Not Registered", "You haven't registered yet!", _PURPLE_BORDER, icon_symbol="!")
        elif self.active_popup == "missing_password":
            self._render_popup(surface, s, "Password Required", "Please input your password!", _NEON_CYAN, icon_symbol="?")
        elif self.active_popup == "missing_credentials":
            self._render_popup(surface, s, "Input Required", "Please enter your username and password!", _NEON_CYAN, icon_symbol="?")

        if self.fade_alpha > 0:
            fade_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            fade_surf.fill((*_BLACK, self.fade_alpha))
            surface.blit(fade_surf, (0, 0))

    def _render_starfield_effects(self) -> None:
        screen = self.game_manager.screen

        for neb in self.galaxy_nebulae:
            neb_surf = pygame.Surface((int(neb["radius"] * 2), int(neb["radius"] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(neb_surf, (*neb["color"], 18), (int(neb["radius"]), int(neb["radius"])), int(neb["radius"]))
            screen.blit(neb_surf, (int(neb["x"] - neb["radius"]), int(neb["y"] - neb["radius"])))

        manager_stars = getattr(self.game_manager, "stars", [])
        if manager_stars:
            for star in manager_stars:
                star.render(screen, getattr(self.game_manager, "ticks", 0))
        else:
            for star in self.galaxy_stars:
                twinkle = math.sin(self.galaxy_timer * 2 + star["twinkle_offset"]) * 30
                brightness = max(40, min(200, int(star["brightness"] + twinkle)))
                pygame.draw.circle(screen, (brightness, brightness, brightness + 35), (int(star["x"]), int(star["y"])), star["size"])

        for dust in self.galaxy_dust:
            r = int(dust["radius"])
            dust_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(dust_surf, (*dust["color"], dust["alpha"]), (r + 1, r + 1), r)
            screen.blit(dust_surf, (int(dust["x"] - r), int(dust["y"] - r)))

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
            toggle_font = FontManager.get_font(max(11, int(13 * scale)), bold=True)
            toggle_str = "HIDE" if self.show_password else "SHOW"
            text_surf_toggle = toggle_font.render(toggle_str, True, _WHITE)
            
            padding_w = int(14 * scale)
            self.show_toggle_rect = pygame.Rect(
                rect.right - text_surf_toggle.get_width() - padding_w - int(6 * scale), 
                rect.top + int(6 * scale), 
                text_surf_toggle.get_width() + padding_w, 
                rect.height - int(12 * scale)
            )
            right_offset_limit = self.show_toggle_rect.left
            
            toggle_hover = self.show_toggle_rect.collidepoint(pygame.mouse.get_pos()) and (self.active_popup is None)
            toggle_bg_color = (70, 35, 120) if toggle_hover else (45, 22, 85)
            
            self._draw_cut_corner_rect(surface, self.show_toggle_rect, fill=toggle_bg_color, border=_NEON_CYAN if toggle_hover else border_color, scale=scale, cut=4)
            surface.blit(text_surf_toggle, text_surf_toggle.get_rect(center=self.show_toggle_rect.center))

        font = FontManager.get_font(max(15, int(17 * scale)), bold=False)
        if not text:
            display_text = placeholder
            color = (170, 150, 200)
        else:
            display_text = ("*" * len(text)) if is_password else text
            color = _WHITE
        
        text_surf = font.render(display_text, True, color)
        text_rect = text_surf.get_rect(midleft=(icon_rect.right + int(16 * scale), rect.centery))
        
        if is_active and self.selection_active and text:
            select_surf = pygame.Surface((text_surf.get_width() + 6, text_surf.get_height() + 4), pygame.SRCALPHA)
            select_surf.fill((80, 150, 255, 100))
            surface.blit(select_surf, (text_rect.x - 3, text_rect.y - 2))

        surface.blit(text_surf, text_rect)

        if is_active and self.cursor_visible and not self.selection_active:
            cursor_x = text_rect.right + 2 if text else (icon_rect.right + int(16 * scale))
            if cursor_x < right_offset_limit - 5:
                pygame.draw.line(surface, _NEON_CYAN, (cursor_x, rect.top + int(10 * scale)), (cursor_x, rect.bottom - int(10 * scale)), width=max(1, int(2 * scale)))

    def _draw_back_button(self, surface: pygame.Surface, scale: float) -> None:
        btn_w = int(110 * scale)
        btn_h = int(40 * scale)
        self.back_rect = pygame.Rect(int(30 * scale), int(28 * scale), btn_w, btn_h)
        
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.back_rect.collidepoint(mouse_pos) and (self.active_popup is None)
        fill_color = (65, 32, 110, 230) if hovered else (42, 20, 75, 200)
        border_color = _NEON_CYAN if hovered else _PURPLE_BORDER
        
        self._draw_cut_corner_rect(surface, self.back_rect, fill=fill_color, border=border_color, scale=scale, cut=6)
        
        font = FontManager.get_font(max(11, int(13 * scale)), bold=True)
        back_text = font.render("◄  BACK", True, _WHITE)
        surface.blit(back_text, back_text.get_rect(center=self.back_rect.center))

    def _draw_techy_corners(self, surface: pygame.Surface, rect: pygame.Rect, color, scale: float, length: int = 16) -> None:
        l = int(length * scale)
        th = max(1, int(2 * scale))
        
        pygame.draw.line(surface, color, rect.topleft, (rect.left + l, rect.top), width=th)
        pygame.draw.line(surface, color, rect.topleft, (rect.left, rect.top + l), width=th)
        pygame.draw.line(surface, color, (rect.right, rect.top), (rect.right - l, rect.top), width=th)
        pygame.draw.line(surface, color, (rect.right, rect.top), (rect.right, rect.top + l), width=th)
        pygame.draw.line(surface, color, (rect.left, rect.bottom), (rect.left + l, rect.bottom), width=th)
        pygame.draw.line(surface, color, (rect.left, rect.bottom), (rect.left, rect.bottom - l), width=th)
        pygame.draw.line(surface, color, rect.bottomright, (rect.right - l, rect.bottom), width=th)
        pygame.draw.line(surface, color, rect.bottomright, (rect.right, rect.bottom - l), width=th)

    def _render_popup(self, surface: pygame.Surface, scale: float, main_msg: str, sub_msg: str, border_col, icon_symbol: str = "!") -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((5, 3, 20, 210))
        surface.blit(overlay, (0, 0))

        pop_w = min(int(440 * scale), int(self.width * 0.78))
        pop_h = int(210 * scale)
        pop_rect = pygame.Rect((self.width - pop_w) // 2, (self.height - pop_h) // 2, pop_w, pop_h)

        pop_surf = pygame.Surface((pop_w, pop_h), pygame.SRCALPHA)
        c_cut = 18
        pop_points = [
            (c_cut, 0), (pop_w - c_cut, 0), (pop_w, c_cut),
            (pop_w, pop_h - c_cut), (pop_w - c_cut, pop_h),
            (c_cut, pop_h), (0, pop_h - c_cut), (0, c_cut)
        ]
        
        pygame.draw.polygon(pop_surf, (28, 12, 55, 245), pop_points)
        pygame.draw.polygon(pop_surf, border_col, pop_points, width=max(2, int(2 * scale)))
        surface.blit(pop_surf, pop_rect.topleft)

        self._draw_techy_corners(surface, pop_rect, border_col, scale, length=16)
        inner_trim = pop_rect.inflate(-int(8 * scale), -int(8 * scale))
        self._draw_techy_corners(surface, inner_trim, (border_col[0]//2, border_col[1]//2, border_col[2]//2), scale, length=8)

        badge_radius = int(18 * scale)
        badge_center = (pop_rect.centerx, pop_rect.top + int(38 * scale))
        pygame.draw.circle(surface, (50, 20, 90), badge_center, badge_radius)
        pygame.draw.circle(surface, border_col, badge_center, badge_radius, width=max(1, int(2 * scale)))
        
        badge_font = FontManager.get_font(max(13, int(16 * scale)), bold=True)
        badge_text = badge_font.render(icon_symbol, True, _WHITE)
        surface.blit(badge_text, badge_text.get_rect(center=badge_center))

        msg_font = FontManager.get_font(max(14, int(17 * scale)), bold=True)
        msg_surf = msg_font.render(main_msg, True, _WHITE)
        surface.blit(msg_surf, msg_surf.get_rect(center=(pop_rect.centerx, pop_rect.top + int(82 * scale))))

        sub_font = FontManager.get_font(max(11, int(13 * scale)), bold=False)
        sub_surf = sub_font.render(sub_msg, True, (225, 205, 255))
        surface.blit(sub_surf, sub_surf.get_rect(center=(pop_rect.centerx, pop_rect.top + int(114 * scale))))

        btn_w, btn_h = int(110 * scale), int(38 * scale)
        self.popup_ok_rect = pygame.Rect(pop_rect.centerx - btn_w // 2, pop_rect.bottom - int(52 * scale), btn_w, btn_h)
        
        mouse_pos = pygame.mouse.get_pos()
        ok_hover = self.popup_ok_rect.collidepoint(mouse_pos)
        ok_fill = (90, 45, 150) if ok_hover else (65, 30, 115)
        ok_border = _NEON_CYAN if ok_hover else border_col
        
        self._draw_cut_corner_rect(surface, self.popup_ok_rect, fill=ok_fill, border=ok_border, scale=scale, cut=6)
        ok_font = FontManager.get_font(max(12, int(14 * scale)), bold=True)
        ok_text = ok_font.render("O K", True, _WHITE if ok_hover else (235, 220, 255))
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