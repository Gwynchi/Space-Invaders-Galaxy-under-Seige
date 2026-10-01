from __future__ import annotations
import os
import pygame
from typing import Optional

class DefaultPage:
    def __init__(self, screen: pygame.Surface, width: int, height: int) -> None:
        self.screen = screen
        self.width = width
        self.height = height
        self.bg_image: Optional[pygame.Surface] = None
        self._load_background()

    def _load_background(self) -> None:
        path = os.path.join("assets", "image", "main", "background_main.png")
        if os.path.exists(path):
            try:
                raw_image = pygame.image.load(path).convert()
                # Scale background and set an alpha/translucency level if desired
                scaled = pygame.transform.smoothscale(raw_image, (self.width, self.height))
                # Optional opacity tint (e.g., alpha 200 out of 255 for slightly dimmed/transparent feel)
                scaled.set_alpha(205) 
                self.bg_image = scaled
            except Exception as e:
                print(f"Warning: Could not load background image from {path}: {e}")
                self.bg_image = None
        else:
            self.bg_image = None

    def render_background(self) -> None:
        if self.screen.get_width() != self.width or self.screen.get_height() != self.height:
            self.width = self.screen.get_width()
            self.height = self.screen.get_height()
            self._load_background()

        # Fill base with a deep dark tone first
        self.screen.fill((3, 2, 15))
        
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))