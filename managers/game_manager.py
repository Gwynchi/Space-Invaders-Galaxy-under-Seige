"""
Game Manager - Pure UI / Menu & Login Shell
===========================================
"""
from __future__ import annotations

import math
import os
import random
import sys
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

import pygame

from utils.constants import GameState, LayoutMetrics, PALETTE
from utils.font_manager import FontManager
from utils.visual_effects import Star
from scenes.default_page import DefaultPage
from scenes.login_page import LoginScene
from scenes.register_page import RegisterPage


if TYPE_CHECKING:
    from managers.db_manager import DBManager
else:
    try:
        from managers.db_manager import DBManager
    except ImportError:
        class DBManager:
            pass


# Colors (Customized Purple Theme)
_BLACK = (3, 2, 15)
_PANEL = (22, 10, 45)
_PANEL_ACTIVE = (55, 20, 95)
_VIOLET = (140, 70, 200)
_PURPLE_BORDER = (195, 110, 255)
_NEON_CYAN = (80, 230, 255)
_WHITE = (255, 255, 255)
_MUTED = (172, 151, 213)


def _cut_corner_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    fill: Tuple[int, int, int],
    border: Tuple[int, int, int],
    scale: float,
    cut: Optional[int] = None,
) -> None:
    """Draws a futuristic UI panel with cut corners and neon border accents[cite: 3, 4]."""
    c = cut if cut is not None else max(8, int(18 * scale))
    c = min(c, rect.width // 4, rect.height // 2)

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

    pygame.draw.polygon(surface, fill, points)
    pygame.draw.polygon(surface, border, points, width=max(1, int(2 * scale)))

    accent_len = max(7, int(rect.height * 0.25))
    pygame.draw.line(
        surface, _VIOLET,
        (rect.left + 2, rect.centery - accent_len),
        (rect.left + 2, rect.centery + accent_len),
        max(1, int(scale)),
    )
    pygame.draw.line(
        surface, _PURPLE_BORDER,
        (rect.right - 2, rect.centery - accent_len),
        (rect.right - 2, rect.centery + accent_len),
        max(1, int(scale)),
    )


class EnhancedButton:
    """Manages interactive menu buttons with custom hover states, icons, and cut corners[cite: 3, 4]."""
    def __init__(
        self,
        text: str,
        rect_fn: Callable[[], pygame.Rect],
        *,
        is_primary: bool = False,
        show_bullet: bool = True,
        icon: Optional[str] = None,
    ) -> None:
        self.text = text
        self.rect_fn = rect_fn
        self.is_primary = is_primary
        self.show_bullet = show_bullet
        self.icon = icon
        self.hovered = False

    def update(self, mouse_pos: Tuple[int, int], events: List[pygame.event.Event]) -> None:
        del events
        self.hovered = self.rect_fn().collidepoint(mouse_pos)

    def clicked(self, event: pygame.event.Event) -> bool:
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hovered

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        rect = self.rect_fn()
        scale = max(0.75, rect.height / 50.0)
        c = max(8, int(rect.height * 0.28))

        if self.hovered:
            fill_color = (40, 18, 75) if self.is_primary else (30, 14, 60)
            border_color = _NEON_CYAN if self.is_primary else _PURPLE_BORDER
            text_color = _WHITE
        else:
            fill_color = (30, 12, 60) if self.is_primary else _PANEL
            border_color = _PURPLE_BORDER if self.is_primary else _VIOLET
            text_color = _WHITE if self.is_primary else (225, 205, 255)

        _cut_corner_panel(
            surface,
            rect,
            fill=fill_color,
            border=border_color,
            scale=scale,
            cut=c,
        )

        inner_rect = rect.inflate(-int(4 * scale), -int(4 * scale))
        inner_border = (120, 50, 190) if not self.hovered else _PURPLE_BORDER
        pygame.draw.rect(surface, inner_border, inner_rect, width=1, border_radius=max(4, int(4 * scale)))

        icon_color = _NEON_CYAN if (self.hovered and self.is_primary) else (_PURPLE_BORDER if self.hovered else _VIOLET)
        self._draw_icon(surface, rect, icon_color, scale)

        text_rect = rect.copy()
        text_rect.centerx += int(rect.height * 0.05)
        
        shadow_surf = font.render(self.text, True, (15, 5, 30))
        surface.blit(shadow_surf, shadow_surf.get_rect(center=(text_rect.centerx + 1, text_rect.centery + 1)))
        
        text_surf = font.render(self.text, True, text_color)
        surface.blit(text_surf, text_surf.get_rect(center=text_rect.center))

    def _draw_icon(self, surface: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int], scale: float) -> None:
        cx = rect.left + int(rect.height * 0.75)
        cy = rect.centery
        size = max(5, int(rect.height * 0.16))

        if self.icon == "play":
            pygame.draw.polygon(surface, color, [(cx - size, cy - size - 2), (cx - size, cy + size + 2), (cx + size + 2, cy)])
        elif self.icon == "user":
            head_r = max(3, int(rect.height * 0.105))
            pygame.draw.circle(surface, color, (cx, cy - size // 2), head_r)
            body_rect = pygame.Rect(cx - head_r * 2, cy + head_r // 2, head_r * 4, head_r * 2)
            pygame.draw.arc(surface, color, body_rect, 0, 3.14, width=max(1, int(2 * scale)))
        elif self.icon == "gear":
            radius = max(5, int(rect.height * 0.15))
            pygame.draw.circle(surface, color, (cx, cy), radius, width=max(2, int(2 * scale)))
            pygame.draw.circle(surface, color, (cx, cy), max(2, int(radius * 0.4)))
        elif self.show_bullet:
            bullet_size = max(3, int(rect.height * 0.09))
            diamond_points = [
                (cx, cy - bullet_size),
                (cx + bullet_size, cy),
                (cx, cy + bullet_size),
                (cx - bullet_size, cy)
            ]
            pygame.draw.polygon(surface, color, diamond_points)


class GameManager:
    """Controls overall game states, navigation scenes, popups, and the custom hardware cursor[cite: 4]."""
    def __init__(self, screen: pygame.Surface, width: int, height: int) -> None:
        self.screen = screen
        self.width = width
        self.height = height

        self.state = GameState.DEFAULT
        self.default_page = DefaultPage(screen, width, height)
        self.current_scene = None

        self.ticks = 0
        self.db = DBManager()
        self.current_user: Optional[Dict[str, Any] | str] = None

        self.show_quit_popup = False
        self.fade_alpha = 255

        if not pygame.font.get_init():
            pygame.font.init()

        self.title_image: Optional[pygame.Surface] = None
        self._load_title_image()

        self.buttons = {
            "login": EnhancedButton("L O G I N", lambda: self._menu_button_rect(0), is_primary=True, icon="play"),
            "register": EnhancedButton("R E G I S T E R", lambda: self._menu_button_rect(1), icon="user"),
            "quit": EnhancedButton("Q U I T   A P P", lambda: self._menu_button_rect(2), icon="gear"),
            "confirm_quit": EnhancedButton("YES", self._popup_yes_rect, is_primary=True, show_bullet=False),
            "cancel_quit": EnhancedButton("NO", self._popup_no_rect, show_bullet=False),
        }

        self.raw_cursor_matrix = [
            [1, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 0, 0, 0, 0, 0, 0],
            [1, 2, 1, 0, 0, 0, 0, 0],
            [1, 2, 2, 1, 0, 0, 0, 0],
            [1, 2, 2, 2, 1, 0, 0, 0],
            [1, 2, 2, 1, 1, 1, 0, 0],
            [1, 2, 1, 1, 0, 0, 0, 0],
            [1, 1, 0, 0, 0, 0, 0, 0],
        ]

        self.stars = self._init_starfield()
        
        # Initialize and set the native hardware cursor[cite: 4]
        self._cached_cursor = self._get_scaled_cursor()
        pygame.mouse.set_cursor(self._cached_cursor)
        pygame.mouse.set_visible(True)

    def _load_title_image(self) -> None:
        path = os.path.join("assets", "image", "text", "text_bg.png")
        if os.path.exists(path):
            try:
                self.title_image = pygame.image.load(path).convert_alpha()
            except Exception as e:
                print(f"Warning: Could not load title image from {path}: {e}")
                self.title_image = None
        else:
            self.title_image = None

    def _sync_dimensions(self) -> None:
        cur_w = self.screen.get_width()
        cur_h = self.screen.get_height()
        if cur_w != self.width or cur_h != self.height:
            self.width = cur_w
            self.height = cur_h
            self._cached_cursor = self._get_scaled_cursor()
            pygame.mouse.set_cursor(self._cached_cursor)

    def _get_scale(self) -> float:
        return max(0.5, min(self.width / 1080.0, self.height / 720.0))

    def _get_layout(self) -> LayoutMetrics:
        s = self._get_scale()
        col_w = min(int(540 * s), max(int(260 * s), int(self.width * 0.55)))
        center_x = self.width // 2
        return LayoutMetrics(
            s=s,
            px=max(8, int(12 * s)),
            title_x=center_x,
            title_y=int(self.height * 0.18),
            deck_center_y=int(self.height * 0.52),
            col_w=col_w,
            panel_left=center_x - col_w // 2,
            form_top=int(self.height * 0.33),
            label_h=max(16, int(20 * s)),
            field_h=max(36, int(44 * s)),
            gap=max(8, int(14 * s)),
            status_h=max(18, int(22 * s)),
            btn_h=max(38, int(46 * s)),
            ship_x=0,
            ship_y=0,
        )

    def _menu_button_rect(self, index: int) -> pygame.Rect:
        layout = self._get_layout()
        h = max(36, int(48 * layout.s))
        gap = max(8, int(12 * layout.s))
        y = int(self.height * 0.52) + index * (h + gap)
        
        btn_w = int(layout.col_w * 0.70)
        btn_x = layout.panel_left + (layout.col_w - btn_w) // 2
        return pygame.Rect(btn_x, y, btn_w, h)

    def _popup_rect(self) -> pygame.Rect:
        s = self._get_scale()
        width = min(int(460 * s), int(self.width * 0.8))
        height = int(180 * s)
        return pygame.Rect((self.width - width) // 2, (self.height - height) // 2, width, height)

    def _popup_yes_rect(self) -> pygame.Rect:
        p = self._popup_rect()
        s = self._get_scale()
        width, height = int(110 * s), int(36 * s)
        return pygame.Rect(p.centerx - width - int(10 * s), p.bottom - height - int(16 * s), width, height)

    def _popup_no_rect(self) -> pygame.Rect:
        p = self._popup_rect()
        s = self._get_scale()
        width, height = int(110 * s), int(36 * s)
        return pygame.Rect(p.centerx + int(10 * s), p.bottom - height - int(16 * s), width, height)

    def _init_starfield(self) -> List[Star]:
        star_colors = ((145, 100, 255), (205, 160, 255), (80, 210, 255), (255, 110, 220))
        stars = []
        for _ in range(70):
            layer = random.choices((1, 2, 3), weights=(0.5, 0.3, 0.2))[0]
            stars.append(
                Star(
                    x=float(random.randint(0, max(1080, self.width))),
                    y=float(random.randint(0, max(720, self.height))),
                    speed=0.15 if layer == 1 else (0.45 if layer == 2 else 0.8),
                    radius=layer,
                    color=random.choice(star_colors),
                    alpha_base=random.randint(100, 200),
                    twinkle_speed=0.05,
                    twinkle_offset=random.uniform(0, math.tau),
                )
            )
        return stars

    def _get_scaled_cursor(self) -> pygame.Cursor:
        scale = self._get_scale()
        size = max(14, int(22 * scale))
        color_map = {0: (0, 0, 0, 0), 1: (*_VIOLET, 255), 2: (*_WHITE, 255)}
        raw = pygame.Surface((8, 8), pygame.SRCALPHA)
        for y, row in enumerate(self.raw_cursor_matrix):
            for x, value in enumerate(row):
                raw.set_at((x, y), color_map[value])
        scaled_surf = pygame.transform.scale(raw, (size, size))
        return pygame.Cursor((0, 0), scaled_surf)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.current_scene and hasattr(self.current_scene, "handle_event"):
            self.current_scene.handle_event(event)

    def update(self, events: List[pygame.event.Event]) -> None:
        """Updates frame state, transitions, starfields, and menu buttons[cite: 3, 4]."""
        self._sync_dimensions()
        self.ticks += 1
        
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 8)

        mouse_pos = pygame.mouse.get_pos()

        if self.current_scene:
            for event in events:
                if hasattr(self.current_scene, "handle_event"):
                    self.current_scene.handle_event(event)
            if hasattr(self.current_scene, "update"):
                try:
                    self.current_scene.update(events)
                except TypeError:
                    self.current_scene.update()
            return

        for star in self.stars:
            star.update(self.height, self.width)

        if self.show_quit_popup:
            self.buttons["confirm_quit"].update(mouse_pos, events)
            self.buttons["cancel_quit"].update(mouse_pos, events)
            for event in events:
                if self.buttons["confirm_quit"].clicked(event):
                    pygame.quit()
                    sys.exit()
                if self.buttons["cancel_quit"].clicked(event):
                    self.show_quit_popup = False
            return

        match self.state:
            case GameState.DEFAULT | GameState.MENU:
                for key in ("login", "register", "quit"):
                    self.buttons[key].update(mouse_pos, events)
                for event in events:
                    if self.buttons["login"].clicked(event):
                        self.current_scene = LoginScene(self)
                        print("Login button clicked - Opening Login Page...")
                    elif self.buttons["register"].clicked(event):
                        self.current_scene = RegisterPage(self)
                        print("Register button clicked - Opening Register Page...")
                    elif self.buttons["quit"].clicked(event):
                        self.show_quit_popup = True

    def render(self) -> None:
        """Renders the active scene or menu elements, and side frames[cite: 4]."""
        self._sync_dimensions()
        
        if self.current_scene and hasattr(self.current_scene, "draw"):
            self.current_scene.draw(self.screen)
            return

        self.default_page.render_background()
        self._render_starfield()
        self._render_title_image()

        match self.state:
            case GameState.DEFAULT | GameState.MENU:
                self._render_menu()

        if self.show_quit_popup:
            self._render_quit_popup()

        self._render_side_frames()

        if self.fade_alpha > 0:
            fade_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            fade_surface.fill((*_BLACK, self.fade_alpha))
            self.screen.blit(fade_surface, (0, 0))

    def _render_starfield(self) -> None:
        for star in self.stars:
            star.render(self.screen, self.ticks)

    def _render_title_image(self) -> None:
        if self.title_image:
            orig_w, orig_h = self.title_image.get_size()
            max_w = int(self.width * 0.80)
            max_h = int(self.height * 0.97)
            
            scale_w = max_w / orig_w
            scale_h = max_h / orig_h
            scale_factor = min(scale_w, scale_h)
            
            target_w = max(1, int(orig_w * scale_factor))
            target_h = max(1, int(orig_h * scale_factor))
            
            scaled_img = pygame.transform.smoothscale(self.title_image, (target_w, target_h))
            rect = scaled_img.get_rect(center=(self.width // 2, int(self.height * 0.43)))
            self.screen.blit(scaled_img, rect)

    def _render_side_frames(self) -> None:
        s = self._get_scale()
        margin = int(24 * s)
        l = margin
        t = margin
        r = self.width - margin
        b = self.height - margin

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        cyan = (80, 230, 255, 255)
        magenta = (230, 40, 230, 255)
        purple_inner = (140, 70, 200, 255)

        sz = int(60 * s)
        th = max(3, int(5 * s))
        inner_th = max(1, int(2 * s))

        # --- TOP-LEFT CORNER ---
        pygame.draw.line(overlay, cyan, (l, t), (l + sz, t), th)
        pygame.draw.line(overlay, cyan, (l, t), (l, t + sz), th)
        pygame.draw.line(overlay, magenta, (l + sz + int(4*s), t), (l + sz + int(16*s), t), th)
        pygame.draw.line(overlay, magenta, (l, t + sz + int(4*s)), (l, t + sz + int(16*s)), th)
        
        isz = int(35 * s)
        pygame.draw.line(overlay, purple_inner, (l + int(12*s), t + int(12*s)), (l + isz, t + int(12*s)), inner_th)
        pygame.draw.line(overlay, purple_inner, (l + int(12*s), t + int(12*s)), (l + int(12*s), t + isz), inner_th)

        # --- TOP-RIGHT CORNER ---
        pygame.draw.line(overlay, cyan, (r - sz, t), (r, t), th)
        pygame.draw.line(overlay, cyan, (r, t), (r, t + sz), th)
        pygame.draw.line(overlay, magenta, (r - sz - int(16*s), t), (r - sz - int(4*s), t), th)
        pygame.draw.line(overlay, magenta, (r, t + sz + int(4*s)), (r, t + sz + int(16*s)), th)
        pygame.draw.line(overlay, purple_inner, (r - isz, t + int(12*s)), (r - int(12*s), t + int(12*s)), inner_th)
        pygame.draw.line(overlay, purple_inner, (r - int(12*s), t + int(12*s)), (r - int(12*s), t + isz), inner_th)

        # --- BOTTOM-LEFT CORNER ---
        pygame.draw.line(overlay, cyan, (l, b), (l + sz, b), th)
        pygame.draw.line(overlay, cyan, (l, b - sz), (l, b), th)
        pygame.draw.line(overlay, magenta, (l + sz + int(4*s), b), (l + sz + int(16*s), b), th)
        pygame.draw.line(overlay, magenta, (l, b - sz - int(16*s)), (l, b - sz - int(4*s)), th)
        pygame.draw.line(overlay, purple_inner, (l + int(12*s), b - int(12*s)), (l + isz, b - int(12*s)), inner_th)
        pygame.draw.line(overlay, purple_inner, (l + int(12*s), b - isz), (l + int(12*s), b - int(12*s)), inner_th)

        # --- BOTTOM-RIGHT CORNER ---
        pygame.draw.line(overlay, cyan, (r - sz, b), (r, b), th)
        pygame.draw.line(overlay, cyan, (r, b - sz), (r, b), th)
        pygame.draw.line(overlay, magenta, (r - sz - int(16*s), b), (r - sz - int(4*s), b), th)
        pygame.draw.line(overlay, magenta, (r, b - sz - int(16*s)), (r, b - sz - int(4*s)), th)
        pygame.draw.line(overlay, purple_inner, (r - isz, b - int(12*s)), (r - int(12*s), b - int(12*s)), inner_th)
        pygame.draw.line(overlay, purple_inner, (r - int(12*s), b - isz), (r - int(12*s), b - int(12*s)), inner_th)

        self.screen.blit(overlay, (0, 0))

    def _render_menu(self) -> None:
        layout = self._get_layout()
        menu_font = FontManager.get_font(max(12, int(18 * layout.s)), bold=True)
        for key in ("login", "register", "quit"):
            self.buttons[key].draw(self.screen, menu_font)

    def _render_quit_popup(self) -> None:
        s = self._get_scale()
        rect = self._popup_rect()
        backdrop = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        backdrop.fill((3, 0, 15, 220))
        self.screen.blit(backdrop, (0, 0))

        _cut_corner_panel(self.screen, rect, fill=(35, 12, 65), border=_PURPLE_BORDER, scale=s, cut=max(10, int(16 * s)))

        title_font = FontManager.get_font(max(12, int(15 * s)), bold=True)
        message = title_font.render("EXIT APP?", True, _WHITE)
        self.screen.blit(message, message.get_rect(center=(rect.centerx, rect.top + int(48 * s))))

        button_font = FontManager.get_font(max(10, int(13 * s)), bold=True)
        self.buttons["confirm_quit"].draw(self.screen, button_font)
        self.buttons["cancel_quit"].draw(self.screen, button_font)