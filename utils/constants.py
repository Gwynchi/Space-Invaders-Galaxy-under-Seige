"""
Constants & Configuration Module
Defines GameState, LayoutMetrics, and the strict Purple Palette.
"""

from enum import Enum, auto
from dataclasses import dataclass


class GameState(Enum):
    DEFAULT = auto()
    MENU = auto()
    LOGIN = auto()
    REGISTER = auto()
    PLAYING = auto()


@dataclass
class LayoutMetrics:
    s: float
    px: int
    title_x: int
    title_y: int
    deck_center_y: int
    col_w: int
    panel_left: int
    form_top: int
    label_h: int
    field_h: int
    gap: int
    status_h: int
    btn_h: int
    ship_x: int
    ship_y: int


@dataclass(frozen=True)
class PurplePalette:
    # Purple Spectrum
    BG_DARK: tuple = (19, 9, 36)          # Deep Night Purple
    BG_PANEL: tuple = (38, 18, 68)        # Dark Violet
    BORDER_PURPLE: tuple = (168, 85, 247)   # Vibrant Lavender
    PASTEL_PURPLE: tuple = (216, 180, 248) # Soft Pastel Violet
    SOFT_PURPLE: tuple = (192, 132, 252)   # Bright Purple Highlight
    HOVER_PURPLE: tuple = (126, 34, 206)   # Deep Royal Purple
    TEXT_WHITE: tuple = (250, 245, 255)    # Soft White / Lilac
    ERROR_TEXT: tuple = (244, 114, 182)    # Pastel Pinkish-Purple
    SUCCESS_TEXT: tuple = (192, 132, 252)  # Soft Violet Accent


PALETTE = PurplePalette()