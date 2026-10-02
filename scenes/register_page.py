from __future__ import annotations

import math
import random
import re
import pygame
from utils.font_manager import FontManager
from utils.constants import GameState

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import LoginScene and ProfilePage safely
try:
    from scenes.login_page import LoginScene
except ImportError:
    LoginScene = None

try:
    from scenes.profile_page import ProfilePage
except ImportError:
    ProfilePage = None

# Colors
_BLACK = (3, 2, 15)
_VIOLET = (140, 70, 200)
_PURPLE_BORDER = (195, 110, 255)
_NEON_CYAN = (80, 230, 255)
_WHITE = (255, 255, 255)
_MAGENTA_GLOW = (220, 70, 200)


class RegisterPage:
    def __init__(self, game_manager) -> None:
        self.game_manager = game_manager
        self.width = game_manager.width
        self.height = game_manager.height
        
        # Smooth transition states (Fade-in starts fully opaque and clears out)
        self.fade_alpha = 255  
        self.transitioning_out = False
        self.next_scene = None
        
        self.float_timer = 0.0
        self.galaxy_timer = 0.0
        
        # Local galaxy & starfield elements for deep space immersion
        self.galaxy_stars = []
        self.galaxy_dust = []
        self.galaxy_nebulae = []
        self._init_galaxy_environment()

        # Load assets once
        try:
            self.raw_panel_image = pygame.image.load("assets/image/text/REGISTER.png").convert_alpha()
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
        self.name = ""
        self.username = ""
        self.password = ""
        self.confirm_password = ""
        self.active_field = "name"
        
        # Cursor & Selection state
        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.selection_active = False
        self.show_password = False
        
        # Popup states
        self.active_popup = None
        self.popup_anim_timer = 0.0
        
        # Rects
        self.name_rect = pygame.Rect(0, 0, 0, 0)
        self.username_rect = pygame.Rect(0, 0, 0, 0)
        self.password_rect = pygame.Rect(0, 0, 0, 0)
        self.confirm_rect = pygame.Rect(0, 0, 0, 0)
        self.show_toggle_rect = pygame.Rect(0, 0, 0, 0)
        self.submit_rect = pygame.Rect(0, 0, 0, 0)
        self.back_rect = pygame.Rect(0, 0, 0, 0)
        self.popup_ok_rect = pygame.Rect(0, 0, 0, 0)
        self.popup_yes_rect = pygame.Rect(0, 0, 0, 0)
        self.popup_no_rect = pygame.Rect(0, 0, 0, 0)

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
                
            icon_size = max(20, int(40 * scale * 0.55))
            if self.raw_profile_icon:
                self._scaled_profile_icon = pygame.transform.smoothscale(self.raw_profile_icon, (icon_size, icon_size))
            else:
                self._scaled_profile_icon = None
                
            if self.raw_padlock_icon:
                self._scaled_padlock_icon = pygame.transform.smoothscale(self.raw_padlock_icon, (icon_size, icon_size))
            else:
                self._scaled_padlock_icon = None

    def _set_popup(self, popup_type: str | None) -> None:
        if self.active_popup != popup_type:
            self.active_popup = popup_type
            if popup_type is not None:
                self.popup_anim_timer = 0.0

    def _is_username_taken(self, username: str) -> bool:
        if not username or len(username.strip()) < 8:
            return False
        try:
            db = getattr(self.game_manager, "db", None)
            if db:
                if hasattr(db, "check_username"):
                    return db.check_username(username.strip())
                elif hasattr(db, "username_exists"):
                    return db.username_exists(username.strip())
                elif hasattr(db, "is_username_taken"):
                    return db.is_username_taken(username.strip())
        except Exception:
            pass
        return False

    def _handle_submission(self) -> None:
        n = self.name.strip()
        u = self.username.strip()
        p = self.password.strip()
        cp = self.confirm_password.strip()
        
        # 1. Check empty fields
        if not n or not u or not p or not cp:
            self._set_popup("missing_fields")
            return
            
        # 2. Check username length (must be at least 8 characters)
        if len(u) < 8:
            self._set_popup("username_invalid")
            return

        # 3. Check if username is already taken
        if self._is_username_taken(u):
            self._set_popup("username_taken")
            return

        # 4. Check password length (at least 8 chars), contains numbers, and contains special characters
        has_number = bool(re.search(r'\d', p))
        has_special = bool(re.search(r'[^A-Za-z0-9]', p))
        if len(p) < 8 or not has_number or not has_special:
            self._set_popup("password_invalid")
            return

        # 5. Check matching passwords
        if p != cp:
            self._set_popup("password_mismatch")
            return

        # 6. Save to MySQL Database using DBManager
        try:
            db = getattr(self.game_manager, "db", None)
            if db:
                success, message = db.register_user(n, u, p)
                if not success:
                    msg_lower = message.lower()
                    if "exist" in msg_lower or "taken" in msg_lower or "duplicate" in msg_lower or "already" in msg_lower:
                        self._set_popup("username_taken")
                    else:
                        print(f"Registration failed: {message}")
                        self._set_popup("username_invalid")
                    return
            else:
                print("Warning: Database manager not found in game_manager.")
        except Exception as e:
            print(f"Database connection error: {e}")
            self._set_popup("username_taken")
            return

        # 7. Satisfaction confirmation prompt or direct success
        self._set_popup("satisfaction_prompt")

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.transitioning_out:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            
            if self.active_popup:
                if self.active_popup == "satisfaction_prompt":
                    if self.popup_yes_rect.collidepoint(pos):
                        self._set_popup("success")
                        return
                    elif self.popup_no_rect.collidepoint(pos):
                        self._set_popup(None)
                        return
                elif self.active_popup == "success":
                    if self.popup_ok_rect.collidepoint(pos):
                        self.transitioning_out = True
                        if ProfilePage is not None:
                            self.next_scene = ProfilePage(self.game_manager)
                        else:
                            self.next_scene = None
                    return
                else:
                    if self.popup_ok_rect.collidepoint(pos):
                        self._set_popup(None)
                    return

            if self.back_rect.collidepoint(pos):
                self.transitioning_out = True
                if LoginScene is not None:
                    self.next_scene = LoginScene(self.game_manager)
                else:
                    self.next_scene = None
                return

            if self.show_toggle_rect.collidepoint(pos):
                self.show_password = not self.show_password
                return

            # Clicking fields updates active field and resets selection
            if self.name_rect.collidepoint(pos):
                self.active_field = "name"
                self.selection_active = False
            elif self.username_rect.collidepoint(pos):
                self.active_field = "username"
                self.selection_active = False
            elif self.password_rect.collidepoint(pos):
                self.active_field = "password"
                self.selection_active = False
            elif self.confirm_rect.collidepoint(pos):
                self.active_field = "confirm_password"
                self.selection_active = False
            elif self.submit_rect.collidepoint(pos):
                self._handle_submission()

        elif event.type == pygame.KEYDOWN:
            if self.active_popup:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.active_popup == "satisfaction_prompt":
                        self._set_popup("success")
                    elif self.active_popup == "success":
                        self.transitioning_out = True
                        if ProfilePage is not None:
                            self.next_scene = ProfilePage(self.game_manager)
                        else:
                            self.next_scene = None
                    else:
                        self._set_popup(None)
                return

            fields_order = ["name", "username", "password", "confirm_password"]
            
            # Check for CTRL + A (Select All)
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_CTRL and event.key == pygame.K_a:
                self.selection_active = True
                return

            if event.key == pygame.K_TAB:
                current_idx = fields_order.index(self.active_field)
                self.active_field = fields_order[(current_idx + 1) % len(fields_order)]
                self.selection_active = False
                return

            if event.key == pygame.K_RETURN:
                self._handle_submission()
                return

            target_str = getattr(self, self.active_field)
            
            # Handle Backspace or Delete
            if event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                if self.selection_active:
                    setattr(self, self.active_field, "")
                    self.selection_active = False
                else:
                    if event.key == pygame.K_BACKSPACE and target_str:
                        setattr(self, self.active_field, target_str[:-1])
            else:
                if event.unicode and event.unicode.isprintable():
                    if self.selection_active:
                        target_str = ""
                        self.selection_active = False
                    if len(target_str) < 25:
                        setattr(self, self.active_field, target_str + event.unicode)

    def update(self) -> None:
        self.width = self.game_manager.width
        self.height = self.game_manager.height
        
        # Handle smooth fade transitions
        if self.transitioning_out:
            self.fade_alpha = min(255, self.fade_alpha + 25)
            if self.fade_alpha >= 255:
                self.game_manager.current_scene = self.next_scene
                return
        elif self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 20)
            
        self.float_timer += 0.05
        self.galaxy_timer += 0.03
        self.cursor_timer += 0.03
        
        if self.active_popup:
            self.popup_anim_timer = min(1.0, self.popup_anim_timer + 0.12)

        if self.cursor_timer >= 1.0:
            self.cursor_timer = 0.0
            self.cursor_visible = not self.cursor_visible

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

    def draw(self, surface: pygame.Surface | None = None) -> None:
        surface = surface or self.game_manager.screen
        self.game_manager.default_page.render_background()
        self._render_starfield_effects()
        self._render_title_image_top()

        s = self.game_manager._get_scale()
        
        panel_w = min(int(920 * s), int(self.width * 0.98))
        if self.raw_panel_image:
            orig_w, orig_h = self.raw_panel_image.get_size()
            panel_h = int(orig_h * (panel_w / orig_w))
        else:
            panel_h = min(int(660 * s), int(self.height * 0.90))
        
        self._update_asset_cache(s, panel_w, panel_h)

        panel_x = (self.width - panel_w) // 2
        float_offset = int(math.sin(self.float_timer) * (6 * s))
        panel_y = ((self.height - panel_h) // 2) + int(28 * s) + float_offset
        
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
            pygame.draw.polygon(panel_surf, _PURPLE_BORDER, panel_points, width=max(2, int(3 * s)))
            surface.blit(panel_surf, panel_rect.topleft)

        self._draw_techy_corners(surface, panel_rect, _PURPLE_BORDER, s, length=18)

        field_w = int(panel_w * 0.48)
        field_h = max(38, int(46 * s))
        field_x = panel_rect.centerx - field_w // 2

        start_y = panel_rect.top + int(190 * s)
        spacing_y = int(62 * s)

        # 1. Name Input
        self.name_rect = pygame.Rect(field_x, start_y, field_w, field_h)
        self._draw_cyber_input(
            surface, self.name_rect, self.name, "Full Name", 
            is_active=(self.active_field == "name"), is_password=False, 
            icon_img=self._scaled_profile_icon, scale=s
        )

        # 2. Username Input with Flashing Red (Taken) or Flashing Green (Available + 8+ chars) Outline
        self.username_rect = pygame.Rect(field_x, start_y + spacing_y, field_w, field_h)
        u_trimmed = self.username.strip()
        
        if len(u_trimmed) >= 8:
            # Use math.sin wave for flashing effect based on galaxy_timer
            flash_wave = (math.sin(self.galaxy_timer * 10) + 1) / 2 # ranges from 0.0 to 1.0
            if self._is_username_taken(u_trimmed):
                # Flash between intense red and dark red/maroon
                r_val = int(120 + 135 * flash_wave)
                username_border = (r_val, int(30 * (1 - flash_wave)), int(30 * (1 - flash_wave)))
            else:
                # Flash between vibrant green and emerald green
                g_val = int(150 + 105 * flash_wave)
                username_border = (int(30 * (1 - flash_wave)), g_val, int(50 * (1 - flash_wave)))
        else:
            username_border = _NEON_CYAN if (self.active_field == "username") else (160, 95, 230)

        self._draw_cyber_input(
            surface, self.username_rect, self.username, "Username (min 8 chars)", 
            is_active=(self.active_field == "username"), is_password=False, 
            icon_img=self._scaled_profile_icon, scale=s, custom_border=username_border
        )

        # 3. Password Input
        self.password_rect = pygame.Rect(field_x, start_y + spacing_y * 2, field_w, field_h)
        self._draw_cyber_input(
            surface, self.password_rect, self.password, "Password (8+ chars, num, symbol)", 
            is_active=(self.active_field == "password"), is_password=not self.show_password, 
            icon_img=self._scaled_padlock_icon, scale=s, has_show_toggle=True
        )

        # 4. Re-type Password Input
        self.confirm_rect = pygame.Rect(field_x, start_y + spacing_y * 3, field_w, field_h)
        self._draw_cyber_input(
            surface, self.confirm_rect, self.confirm_password, "Re-type Password", 
            is_active=(self.active_field == "confirm_password"), is_password=not self.show_password, 
            icon_img=self._scaled_padlock_icon, scale=s
        )

        btn_w = int(field_w * 0.70)
        btn_h = max(40, int(48 * s))
        self.submit_rect = pygame.Rect(panel_rect.centerx - btn_w // 2, start_y + spacing_y * 4 + int(10 * s), btn_w, btn_h)
        
        mouse_pos = pygame.mouse.get_pos()
        btn_hovered = self.submit_rect.collidepoint(mouse_pos) and (self.active_popup is None) and not self.transitioning_out
        
        btn_fill = (80, 42, 145) if btn_hovered else (55, 24, 98)
        btn_border = _NEON_CYAN if btn_hovered else _PURPLE_BORDER
            
        self._draw_cut_corner_rect(surface, self.submit_rect, fill=btn_fill, border=btn_border, scale=s, cut=10)
        
        inner_sub_rect = self.submit_rect.inflate(-int(4 * s), -int(4 * s))
        pygame.draw.rect(surface, (135, 75, 205), inner_sub_rect, width=2, border_radius=max(3, int(3 * s)))
        
        btn_font = FontManager.get_font(max(14, int(17 * s)), bold=True)
        shadow_surf = btn_font.render("→   R E G I S T E R", True, (15, 5, 30))
        surface.blit(shadow_surf, shadow_surf.get_rect(center=(self.submit_rect.centerx + 1, self.submit_rect.centery + 1)))
        
        btn_text = btn_font.render("→   R E G I S T E R", True, _WHITE if btn_hovered else (235, 220, 255))
        surface.blit(btn_text, btn_text.get_rect(center=self.submit_rect.center))

        # Back Button
        self._draw_back_button(surface, s)

        # Active Popup Dialogs
        if self.active_popup == "missing_fields":
            self._render_popup(surface, s, "Incomplete Details", "Please fill in all input fields!", _NEON_CYAN, icon_symbol="?")
        elif self.active_popup == "username_invalid":
            self._render_popup(surface, s, "Username Error", "Username must be at least 8 characters long!", _PURPLE_BORDER, icon_symbol="!")
        elif self.active_popup == "username_taken":
            self._render_popup(surface, s, "Account is already Created", "Username is Already taken!", (255, 80, 80), icon_symbol="!")
        elif self.active_popup == "password_invalid":
            self._render_popup(surface, s, "Password Error", "Password needs 8+ chars, numbers & special symbols!", _PURPLE_BORDER, icon_symbol="!")
        elif self.active_popup == "password_mismatch":
            self._render_popup(surface, s, "Password Mismatch", "Retyped password does not match!", _PURPLE_BORDER, icon_symbol="!")
        elif self.active_popup == "satisfaction_prompt":
            self._render_yes_no_popup(surface, s, "Confirmation", "Are you satisfied?")
        elif self.active_popup == "success":
            self._render_popup(surface, s, "Success", "You have successfully registered!", _NEON_CYAN, icon_symbol="✓")

        # Smooth transition fade overlay
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

    def _render_title_image_top(self) -> None:
        if self.game_manager.title_image:
            orig_w, orig_h = self.game_manager.title_image.get_size()
            max_w = int(self.width * 0.58)
            max_h = int(self.height * 0.18)
            scale_factor = min(max_w / orig_w, max_h / orig_h)
            target_w = max(1, int(orig_w * scale_factor))
            target_h = max(1, int(orig_h * scale_factor))
            scaled_img = pygame.transform.smoothscale(self.game_manager.title_image, (target_w, target_h))
            
            rect = scaled_img.get_rect(center=(self.width // 2, int(self.height * 0.13)))
            self.game_manager.screen.blit(scaled_img, rect)

    def _draw_cyber_input(self, surface: pygame.Surface, rect: pygame.Rect, text: str, placeholder: str, is_active: bool, is_password: bool, icon_img: pygame.Surface | None, scale: float, has_show_toggle: bool = False, custom_border=None) -> None:
        fill_color = (25, 12, 50, 220)
        border_color = custom_border if custom_border is not None else (_NEON_CYAN if is_active else (160, 95, 230))
        
        field_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        c = 6
        points = [
            (c, 0), (rect.width - c, 0), (rect.width, c),
            (rect.width, rect.height - c), (rect.width - c, rect.height),
            (c, rect.height), (0, rect.height - c), (0, c)
        ]
        pygame.draw.polygon(field_surf, fill_color, points)
        # Thicker border width set to 3.5x - 4x scale for a bolder outline
        pygame.draw.polygon(field_surf, border_color, points, width=max(2, int(3.5 * scale)))
        surface.blit(field_surf, rect.topleft)

        icon_w = int(rect.height * 0.95)
        icon_rect = pygame.Rect(rect.left, rect.top, icon_w, rect.height)
        icon_bg_surf = pygame.Surface((icon_rect.width, icon_rect.height), pygame.SRCALPHA)
        pygame.draw.polygon(icon_bg_surf, (45, 20, 80, 200), points)
        pygame.draw.polygon(icon_bg_surf, border_color, points, width=max(2, int(2 * scale)))
        surface.blit(icon_bg_surf, icon_rect.topleft)
        
        if icon_img:
            surface.blit(icon_img, icon_img.get_rect(center=icon_rect.center))

        right_offset_limit = rect.right
        if has_show_toggle:
            toggle_font = FontManager.get_font(max(10, int(11 * scale)), bold=True)
            toggle_str = "HIDE" if self.show_password else "SHOW"
            text_surf_toggle = toggle_font.render(toggle_str, True, _WHITE)
            
            toggle_w = text_surf_toggle.get_width() + int(14 * scale)
            toggle_h = rect.height - int(10 * scale)
            self.show_toggle_rect = pygame.Rect(
                rect.right - toggle_w - int(6 * scale), 
                rect.top + (rect.height - toggle_h) // 2, 
                toggle_w, 
                toggle_h
            )
            right_offset_limit = self.show_toggle_rect.left - int(8 * scale)
            
            toggle_hover = self.show_toggle_rect.collidepoint(pygame.mouse.get_pos()) and (self.active_popup is None) and not self.transitioning_out
            toggle_bg_color = (70, 35, 120) if toggle_hover else (45, 22, 85)
            
            self._draw_cut_corner_rect(surface, self.show_toggle_rect, fill=toggle_bg_color, border=_NEON_CYAN if toggle_hover else border_color, scale=scale, cut=4)
            surface.blit(text_surf_toggle, text_surf_toggle.get_rect(center=self.show_toggle_rect.center))

        font = FontManager.get_font(max(14, int(16 * scale)), bold=False)
        if not text:
            display_text = placeholder
            color = (170, 150, 200)
        else:
            display_text = ("*" * len(text)) if is_password else text
            color = _WHITE
        
        text_surf = font.render(display_text, True, color)
        text_rect = text_surf.get_rect(midleft=(icon_rect.right + int(14 * scale), rect.centery))
        
        if text_rect.right > right_offset_limit:
            max_text_w = right_offset_limit - text_rect.left
            if max_text_w > 0 and text_surf.get_width() > max_text_w:
                text_surf = text_surf.subsurface((text_surf.get_width() - max_text_w, 0, max_text_w, text_surf.get_height()))
                text_rect = text_surf.get_rect(midleft=(right_offset_limit - max_text_w, rect.centery))

        if is_active and self.selection_active and text:
            select_surf = pygame.Surface((text_surf.get_width() + 6, text_surf.get_height() + 4), pygame.SRCALPHA)
            select_surf.fill((80, 150, 255, 100))
            surface.blit(select_surf, (text_rect.x - 3, text_rect.y - 2))

        surface.blit(text_surf, text_rect)

        if is_active and self.cursor_visible and not self.selection_active:
            cursor_x = text_rect.right + 2 if text else (icon_rect.right + int(14 * scale))
            if cursor_x < right_offset_limit:
                pygame.draw.line(surface, _NEON_CYAN, (cursor_x, rect.top + int(8 * scale)), (cursor_x, rect.bottom - int(8 * scale)), width=max(1, int(2 * scale)))

    def _draw_back_button(self, surface: pygame.Surface, scale: float) -> None:
        btn_w = int(110 * scale)
        btn_h = int(40 * scale)
        self.back_rect = pygame.Rect(int(30 * scale), int(28 * scale), btn_w, btn_h)
        
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.back_rect.collidepoint(mouse_pos) and (self.active_popup is None) and not self.transitioning_out
        fill_color = (65, 32, 110, 230) if hovered else (42, 20, 75, 200)
        border_color = _NEON_CYAN if hovered else _PURPLE_BORDER
        
        self._draw_cut_corner_rect(surface, self.back_rect, fill=fill_color, border=border_color, scale=scale, cut=6)
        
        font = FontManager.get_font(max(11, int(13 * scale)), bold=True)
        back_text = font.render("◄  BACK", True, _WHITE)
        surface.blit(back_text, back_text.get_rect(center=self.back_rect.center))

    def _draw_techy_corners(self, surface: pygame.Surface, rect: pygame.Rect, color, scale: float, length: int = 16) -> None:
        l = int(length * scale)
        th = max(2, int(3 * scale))
        
        pygame.draw.line(surface, color, rect.topleft, (rect.left + l, rect.top), width=th)
        pygame.draw.line(surface, color, rect.topleft, (rect.left, rect.top + l), width=th)
        pygame.draw.line(surface, color, (rect.right, rect.top), (rect.right - l, rect.top), width=th)
        pygame.draw.line(surface, color, (rect.right, rect.top), (rect.right, rect.top + l), width=th)
        pygame.draw.line(surface, color, (rect.left, rect.bottom), (rect.left + l, rect.bottom), width=th)
        pygame.draw.line(surface, color, (rect.left, rect.bottom), (rect.left, rect.bottom - l), width=th)
        pygame.draw.line(surface, color, rect.bottomright, (rect.right - l, rect.bottom), width=th)
        pygame.draw.line(surface, color, rect.bottomright, (rect.right, rect.bottom - l), width=th)

    def _render_popup(self, surface: pygame.Surface, scale: float, main_msg: str, sub_msg: str, border_col, icon_symbol: str = "!") -> None:
        anim_progress = min(1.0, self.popup_anim_timer)
        ease_scale = 0.85 + (0.15 * anim_progress)
        alpha_val = int(220 * anim_progress)

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((5, 3, 20, alpha_val))
        surface.blit(overlay, (0, 0))

        pop_w = int(460 * scale)
        pop_h = int(230 * scale)
        
        actual_pop_w = int(pop_w * ease_scale)
        actual_pop_h = int(pop_h * ease_scale)
        
        pop_rect = pygame.Rect((self.width - actual_pop_w) // 2, (self.height - actual_pop_h) // 2, actual_pop_w, actual_pop_h)

        pop_surf = pygame.Surface((actual_pop_w, actual_pop_h), pygame.SRCALPHA)
        c_cut = int(14 * ease_scale)
        pop_points = [
            (c_cut, 0), (actual_pop_w - c_cut, 0), (actual_pop_w, c_cut),
            (actual_pop_w, actual_pop_h - c_cut), (actual_pop_w - c_cut, actual_pop_h),
            (c_cut, actual_pop_h), (0, actual_pop_h - c_cut), (0, c_cut)
        ]
        
        pygame.draw.polygon(pop_surf, (28, 12, 55, int(250 * anim_progress)), pop_points)
        pygame.draw.polygon(pop_surf, border_col, pop_points, width=max(2, int(3 * scale)))
        surface.blit(pop_surf, pop_rect.topleft)

        self._draw_techy_corners(surface, pop_rect, border_col, scale, length=14)

        badge_radius = int(18 * scale)
        badge_center = (pop_rect.centerx, pop_rect.top + int(36 * scale))
        pygame.draw.circle(surface, (50, 20, 90), badge_center, badge_radius)
        pygame.draw.circle(surface, border_col, badge_center, badge_radius, width=max(2, int(2 * scale)))
        
        badge_font = FontManager.get_font(max(15, int(20 * scale)), bold=True)
        badge_text = badge_font.render(icon_symbol, True, _WHITE)
        surface.blit(badge_text, badge_text.get_rect(center=badge_center))

        msg_font = FontManager.get_font(max(17, int(21 * scale)), bold=True)
        msg_surf = msg_font.render(main_msg, True, _WHITE)
        surface.blit(msg_surf, msg_surf.get_rect(center=(pop_rect.centerx, pop_rect.top + int(86 * scale))))

        sub_font = FontManager.get_font(max(12, int(15 * scale)), bold=False)
        sub_surf = sub_font.render(sub_msg, True, (240, 220, 255))
        surface.blit(sub_surf, sub_surf.get_rect(center=(pop_rect.centerx, pop_rect.top + int(116 * scale))))

        btn_w, btn_h = int(140 * scale), int(38 * scale)
        self.popup_ok_rect = pygame.Rect(pop_rect.centerx - btn_w // 2, pop_rect.bottom - int(56 * scale), btn_w, btn_h)
        
        mouse_pos = pygame.mouse.get_pos()
        ok_hover = self.popup_ok_rect.collidepoint(mouse_pos)
        ok_fill = (90, 45, 150) if ok_hover else (65, 30, 115)
        ok_border = _NEON_CYAN if ok_hover else border_col
        
        self._draw_cut_corner_rect(surface, self.popup_ok_rect, fill=ok_fill, border=ok_border, scale=scale, cut=6)
        ok_font = FontManager.get_font(max(14, int(17 * scale)), bold=True)
        ok_text = ok_font.render("O K", True, _WHITE if ok_hover else (235, 220, 255))
        surface.blit(ok_text, ok_text.get_rect(center=self.popup_ok_rect.center))

    def _render_yes_no_popup(self, surface: pygame.Surface, scale: float, main_msg: str, sub_msg: str) -> None:
        anim_progress = min(1.0, self.popup_anim_timer)
        ease_scale = 0.85 + (0.15 * anim_progress)
        alpha_val = int(220 * anim_progress)

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((5, 3, 20, alpha_val))
        surface.blit(overlay, (0, 0))

        pop_w = int(460 * scale)
        pop_h = int(230 * scale)
        
        actual_pop_w = int(pop_w * ease_scale)
        actual_pop_h = int(pop_h * ease_scale)
        
        pop_rect = pygame.Rect((self.width - actual_pop_w) // 2, (self.height - actual_pop_h) // 2, actual_pop_w, actual_pop_h)

        pop_surf = pygame.Surface((actual_pop_w, actual_pop_h), pygame.SRCALPHA)
        c_cut = int(14 * ease_scale)
        pop_points = [
            (c_cut, 0), (actual_pop_w - c_cut, 0), (actual_pop_w, c_cut),
            (actual_pop_w, actual_pop_h - c_cut), (actual_pop_w - c_cut, actual_pop_h),
            (c_cut, actual_pop_h), (0, actual_pop_h - c_cut), (0, c_cut)
        ]
        
        pygame.draw.polygon(pop_surf, (28, 12, 55, int(250 * anim_progress)), pop_points)
        pygame.draw.polygon(pop_surf, _NEON_CYAN, pop_points, width=max(2, int(3 * scale)))
        surface.blit(pop_surf, pop_rect.topleft)

        self._draw_techy_corners(surface, pop_rect, _NEON_CYAN, scale, length=14)

        badge_radius = int(18 * scale)
        badge_center = (pop_rect.centerx, pop_rect.top + int(36 * scale))
        pygame.draw.circle(surface, (50, 20, 90), badge_center, badge_radius)
        pygame.draw.circle(surface, _NEON_CYAN, badge_center, badge_radius, width=max(2, int(2 * scale)))
        
        badge_font = FontManager.get_font(max(15, int(20 * scale)), bold=True)
        badge_text = badge_font.render("?", True, _WHITE)
        surface.blit(badge_text, badge_text.get_rect(center=badge_center))

        msg_font = FontManager.get_font(max(17, int(21 * scale)), bold=True)
        msg_surf = msg_font.render(main_msg, True, _WHITE)
        surface.blit(msg_surf, msg_surf.get_rect(center=(pop_rect.centerx, pop_rect.top + int(86 * scale))))

        sub_font = FontManager.get_font(max(12, int(15 * scale)), bold=False)
        sub_surf = sub_font.render(sub_msg, True, (240, 220, 255))
        surface.blit(sub_surf, sub_surf.get_rect(center=(pop_rect.centerx, pop_rect.top + int(116 * scale))))

        btn_w, btn_h = int(110 * scale), int(38 * scale)
        spacing = int(20 * scale)
        total_w = (btn_w * 2) + spacing
        start_x = pop_rect.centerx - total_w // 2
        btn_y = pop_rect.bottom - int(56 * scale)

        self.popup_yes_rect = pygame.Rect(start_x, btn_y, btn_w, btn_h)
        self.popup_no_rect = pygame.Rect(start_x + btn_w + spacing, btn_y, btn_w, btn_h)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Yes Button
        yes_hover = self.popup_yes_rect.collidepoint(mouse_pos)
        self._draw_cut_corner_rect(surface, self.popup_yes_rect, fill=(90, 45, 150) if yes_hover else (65, 30, 115), border=_NEON_CYAN, scale=scale, cut=6)
        yes_font = FontManager.get_font(max(14, int(17 * scale)), bold=True)
        yes_text = yes_font.render("YES", True, _WHITE if yes_hover else (235, 220, 255))
        surface.blit(yes_text, yes_text.get_rect(center=self.popup_yes_rect.center))

        # No Button
        no_hover = self.popup_no_rect.collidepoint(mouse_pos)
        self._draw_cut_corner_rect(surface, self.popup_no_rect, fill=(130, 30, 70) if no_hover else (100, 20, 50), border=_PURPLE_BORDER, scale=scale, cut=6)
        no_text = yes_font.render("NO", True, _WHITE if no_hover else (235, 220, 255))
        surface.blit(no_text, no_text.get_rect(center=self.popup_no_rect.center))

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
        pygame.draw.polygon(surface, border, points, width=max(2, int(3 * scale)))