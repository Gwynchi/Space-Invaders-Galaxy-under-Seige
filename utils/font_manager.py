import pygame
from typing import Dict, List, Tuple

class FontManager:
    _FONT_CACHE: Dict[Tuple[int, bool], pygame.font.Font] = {}

    FONT_MAP: Dict[str, List[str]] = {
        "S": ["01111", "10000", "01110", "00001", "11110"],
        "P": ["11110", "10001", "11110", "10000", "10000"],
        "A": ["01110", "10001", "11111", "10001", "10001"],
        "C": ["01111", "10000", "10000", "10000", "01111"],
        "E": ["11111", "10000", "11110", "10000", "11111"],
        "I": ["11111", "00100", "00100", "00100", "11111"],
        "N": ["10001", "11001", "10101", "10011", "10001"],
        "V": ["10001", "10001", "10001", "01010", "00100"],
        "D": ["11110", "10001", "10001", "10001", "11110"],
        "R": ["11110", "10001", "11110", "10010", "10001"],
        " ": ["00000", "00000", "00000", "00000", "00000"],
    }

    @classmethod
    def get_font(cls, size: float, bold: bool = False) -> pygame.font.Font:
        valid_size = max(8, int(size))
        key = (valid_size, bold)
        if key not in cls._FONT_CACHE:
            cls._FONT_CACHE[key] = pygame.font.SysFont("arial", valid_size, bold=bold)
        return cls._FONT_CACHE[key]

    @classmethod
    def make_pixel_word(cls, word: str, px: int) -> pygame.Surface:
        cells_w = len(word) * 6 - 1
        surf = pygame.Surface((cells_w * px, 5 * px), pygame.SRCALPHA)
        for i, ch in enumerate(word):
            grid = cls.FONT_MAP.get(ch, cls.FONT_MAP[" "])
            for ry, row in enumerate(grid):
                for cx, bit in enumerate(row):
                    if bit == "1":
                        surf.fill((255, 255, 255, 255), ((i * 6 + cx) * px, ry * px, px, px))
        return surf