import pygame

class Button:
    """Modern reusable neon button used by the menu and account screens."""

    # Shared sci-fi palette.
    PRIMARY = (132, 48, 218)
    PRIMARY_HOVER = (176, 72, 255)
    PRIMARY_PRESSED = (104, 34, 178)

    SECONDARY = (18, 12, 34)
    SECONDARY_HOVER = (42, 24, 68)

    BORDER = (155, 96, 232)
    BORDER_HOVER = (64, 218, 255)

    TEXT = (255, 255, 255)
    TEXT_DIM = (208, 195, 232)

    def __init__(self, label, get_rect_func, is_primary=False):
        self.label = label
        self.get_rect_func = get_rect_func
        self.is_primary = is_primary

        self.hovered = False
        self.pressed = False
        self._hover_anim = 0.0

    def rect(self):
        """Return the button's current responsive rectangle."""
        return self.get_rect_func()

    def update(self, mouse_pos, events=None):
        """Update hover/press animation without changing click behavior."""
        rect = self.rect()
        self.hovered = rect.collidepoint(mouse_pos)

        target = 1.0 if self.hovered else 0.0
        self._hover_anim += (target - self._hover_anim) * 0.22

        if events:
            for event in events:
                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and self.hovered
                ):
                    self.pressed = True

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.pressed = False

    def draw(self, screen, font):
        """Draw the button with a soft glow, border, and pressed state."""
        rect = self.rect()

        if self.is_primary:
            base = self.PRIMARY
            hover = self.PRIMARY_HOVER
            border = self.BORDER_HOVER if self.hovered else (242, 220, 255)
            text_color = self.TEXT
        else:
            base = self.SECONDARY
            hover = self.SECONDARY_HOVER
            border = self.BORDER_HOVER if self.hovered else self.BORDER
            text_color = self.TEXT if self.hovered else self.TEXT_DIM

        blend = self._hover_anim
        fill = tuple(int(a + (b - a) * blend) for a, b in zip(base, hover))

        # Pressed buttons visually sink by a few pixels.
        press_offset = max(1, int(rect.height * 0.04)) if self.pressed else 0
        draw_rect = rect.move(0, press_offset)

        radius = max(8, int(draw_rect.height * 0.34))

        # Outer glow.
        if self.is_primary or self._hover_anim > 0.04:
            glow_pad = max(6, int(draw_rect.height * 0.18))
            glow = pygame.Surface(
                (draw_rect.width + glow_pad * 2, draw_rect.height + glow_pad * 2),
                pygame.SRCALPHA,
            )

            glow_alpha = int(42 + 68 * self._hover_anim)
            pygame.draw.rect(
                glow,
                (164, 64, 255, glow_alpha),
                glow.get_rect(),
                border_radius=radius + glow_pad // 2,
            )
            screen.blit(
                glow,
                (draw_rect.x - glow_pad, draw_rect.y - glow_pad),
            )

        # Main glassy body.
        body = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            body,
            (*fill, 242),
            body.get_rect(),
            border_radius=radius,
        )

        # Subtle top highlight.
        highlight_height = max(2, int(draw_rect.height * 0.08))
        pygame.draw.rect(
            body,
            (255, 255, 255, 28),
            (2, 2, max(1, draw_rect.width - 4), highlight_height),
            border_radius=max(2, radius // 2),
        )

        pygame.draw.rect(
            body,
            border,
            body.get_rect(),
            width=max(2, int(draw_rect.height * 0.035)),
            border_radius=radius,
        )

        screen.blit(body, draw_rect.topleft)

        # Small accent marker gives the buttons a more intentional HUD feel.
        accent_x = draw_rect.x + max(10, int(draw_rect.width * 0.06))
        accent_y = draw_rect.centery
        accent_color = self.BORDER_HOVER if self.hovered else border
        pygame.draw.circle(
            screen,
            accent_color,
            (accent_x, accent_y),
            max(2, int(draw_rect.height * 0.055)),
        )

        text = font.render(self.label, True, text_color)
        text_rect = text.get_rect(
            center=(draw_rect.centerx + max(4, int(draw_rect.width * 0.015)),
                    draw_rect.centery)
        )
        screen.blit(text, text_rect)

    def clicked(self, event):
        """Return True only when the left mouse button is released over the button."""
        if event.type != pygame.MOUSEBUTTONUP or event.button != 1:
            return False

        self.pressed = False
        return self.rect().collidepoint(event.pos)


# Backwards-compatible name for any older code using UIButton.
UIButton = Button


class MobileButtons:
    """Simple in-game touch/mouse controls."""

    LEFT_COLOR = (76, 48, 112)
    FIRE_COLOR = (138, 46, 168)
    BORDER = (154, 92, 232)
    BORDER_HOVER = (66, 215, 255)
    TEXT = (255, 255, 255)

    def __init__(self):
        self.left = pygame.Rect(20, 520, 80, 60)
        self.right = pygame.Rect(120, 520, 80, 60)
        self.fire = pygame.Rect(680, 520, 100, 60)
        self.font = pygame.font.SysFont("arial", 22, bold=True)

    def draw(self, screen):
        mouse_down = pygame.mouse.get_pressed()[0]
        mouse_pos = pygame.mouse.get_pos()

        self._draw_button(
            screen, self.left, self.LEFT_COLOR, mouse_down, mouse_pos, "left"
        )
        self._draw_button(
            screen, self.right, self.LEFT_COLOR, mouse_down, mouse_pos, "right"
        )
        self._draw_button(
            screen, self.fire, self.FIRE_COLOR, mouse_down, mouse_pos, "FIRE"
        )

    def _draw_button(self, screen, rect, color, mouse_down, mouse_pos, kind):
        held = mouse_down and rect.collidepoint(mouse_pos)

        fill = (
            tuple(min(255, channel + 42) for channel in color)
            if held
            else color
        )
        border = self.BORDER_HOVER if rect.collidepoint(mouse_pos) else self.BORDER

        # Soft touch-control glow.
        glow = pygame.Surface(
            (rect.width + 14, rect.height + 14),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            glow,
            (*border, 35),
            glow.get_rect(),
            border_radius=12,
        )
        screen.blit(glow, (rect.x - 7, rect.y - 7))

        pygame.draw.rect(screen, fill, rect, border_radius=10)
        pygame.draw.rect(
            screen,
            border,
            rect,
            2,
            border_radius=10,
        )

        cx, cy = rect.center

        if kind == "left":
            points = [
                (cx + 10, cy - 14),
                (cx + 10, cy + 14),
                (cx - 12, cy),
            ]
            pygame.draw.polygon(screen, self.TEXT, points)

        elif kind == "right":
            points = [
                (cx - 10, cy - 14),
                (cx - 10, cy + 14),
                (cx + 12, cy),
            ]
            pygame.draw.polygon(screen, self.TEXT, points)

        else:
            label = self.font.render(kind, True, self.TEXT)
            screen.blit(label, label.get_rect(center=rect.center))

    def handle_mouse(self, player, events):
        fire_pressed = False
        mouse_pressed = pygame.mouse.get_pressed()

        if mouse_pressed[0]:
            mouse_pos = pygame.mouse.get_pos()

            if self.left.collidepoint(mouse_pos):
                player.move_left()
            elif self.right.collidepoint(mouse_pos):
                player.move_right()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.fire.collidepoint(event.pos):
                    fire_pressed = True

        return fire_pressed
