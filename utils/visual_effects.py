import math
import random
import pygame
from dataclasses import dataclass
from typing import Tuple

@dataclass(slots=True)
class Star:
    x: float
    y: float
    speed: float
    radius: int
    color: Tuple[int, int, int]
    alpha_base: int
    twinkle_speed: float
    twinkle_offset: float

    def update(self, bounds_height: int, bounds_width: int) -> None:
        self.y += self.speed
        if self.y > bounds_height:
            self.y = 0.0
            self.x = float(random.randint(0, bounds_width))

    def render(self, surface: pygame.Surface, ticks: int) -> None:
        twinkle = math.sin(ticks * self.twinkle_speed + self.twinkle_offset)
        alpha = int(max(40, min(255, self.alpha_base + twinkle * 50)))
        
        star_surf = pygame.Surface((self.radius * 2 + 2, self.radius * 2 + 2), pygame.SRCALPHA)
        color_alpha = (*self.color, alpha)
        pygame.draw.circle(star_surf, color_alpha, (self.radius + 1, self.radius + 1), self.radius)
        surface.blit(star_surf, (int(self.x) - self.radius, int(self.y) - self.radius))


@dataclass(slots=True)
class Laser:
    x: float
    y: float
    speed: float

    def update(self) -> None:
        self.y -= self.speed