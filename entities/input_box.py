# ==============================================================================
# Pygame InputBox Component (Sci-Fi Theme)
# ------------------------------------------------------------------------------
# Handles user text input with features including:
#  - Active focus and error state styling (glows, borders)
#  - Automatic password character masking
#  - Text clipping and right-alignment when text exceeds field width
#  - Blinking cursor animation and custom scaling
# ==============================================================================

import pygame
class InputBox:
    """Responsive sci-fi input field with focus, validation, and password masking."""

    BACKGROUND = (20, 12, 38)
    BACKGROUND_FOCUS = (32, 18, 58)

    BORDER = (145, 86, 225)
    BORDER_FOCUS = (60, 215, 255)
    BORDER_ERROR = (255, 88, 112)

    TEXT = (255, 255, 255)
    LABEL = (202, 184, 232)
    PLACEHOLDER = (128, 110, 166)

    def __init__(
        self,
        label="",
        placeholder="",
        is_password=False,
        max_length=24,
    ):
        self.rect = pygame.Rect(0, 0, 0, 0)

        self.label = label
        self.placeholder = placeholder
        self.is_password = is_password
        self.max_length = max_length

        self.text = ""
        self.active = False
        self.error = False

    def clear(self):
        """Clear the field and return it to its inactive state."""
        self.text = ""
        self.active = False
        self.error = False

    def handle_event(self, event):
        """Handle mouse focus and keyboard input."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)

        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                self.error = False

            elif event.key in (
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
                pygame.K_TAB,
                pygame.K_ESCAPE,
            ):
                # Navigation/submission is handled by GameManager.
                pass

            elif (
                event.unicode
                and event.unicode.isprintable()
                and len(self.text) < self.max_length
            ):
                self.text += event.unicode
                self.error = False

    def draw(self, screen, scale):
        """Draw the complete input field at its current responsive rectangle."""
        rect = self.rect

        if rect.width <= 0 or rect.height <= 0:
            return

        scale = max(0.1, scale)

        # Label above the field.
        label_color = self.BORDER_FOCUS if self.active else self.LABEL
        label_font = pygame.font.SysFont(
            "arial",
            max(10, int(14 * scale)),
            bold=True,
        )
        label_surface = label_font.render(self.label.upper(), True, label_color)

        screen.blit(
            label_surface,
            (
                rect.x + int(3 * scale),
                rect.y - label_surface.get_height() - int(4 * scale),
            ),
        )

        # Select border color by state.
        if self.error:
            border = self.BORDER_ERROR
        elif self.active:
            border = self.BORDER_FOCUS
        else:
            border = self.BORDER

        radius = max(8, int(rect.height * 0.28))

        # Outer glow when focused/error.
        if self.active or self.error:
            glow_color = (
                self.BORDER_ERROR if self.error else self.BORDER_FOCUS
            )
            glow = pygame.Surface(
                (rect.width + 12, rect.height + 12),
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                glow,
                (*glow_color, 32),
                glow.get_rect(),
                border_radius=radius + 3,
            )
            screen.blit(glow, (rect.x - 6, rect.y - 6))

        # Main field.
        field = pygame.Surface(rect.size, pygame.SRCALPHA)
        background = self.BACKGROUND_FOCUS if self.active else self.BACKGROUND

        pygame.draw.rect(
            field,
            (*background, 245),
            field.get_rect(),
            border_radius=radius,
        )

        # Subtle top highlight.
        pygame.draw.rect(
            field,
            (255, 255, 255, 18),
            (2, 2, max(1, rect.width - 4), max(2, int(rect.height * 0.08))),
            border_radius=max(2, radius // 2),
        )

        pygame.draw.rect(
            field,
            border,
            field.get_rect(),
            width=max(2, int((3 if self.active else 2) * scale)),
            border_radius=radius,
        )

        screen.blit(field, rect.topleft)

        # Text area is clipped so long text cannot escape the field.
        padding = int(15 * scale)
        area = pygame.Rect(
            rect.x + padding,
            rect.y,
            max(1, rect.width - padding * 2),
            rect.height,
        )

        font = pygame.font.SysFont(
            "arial",
            max(12, int(18 * scale)),
        )

        old_clip = screen.get_clip()
        screen.set_clip(area)

        if self.text:
            if self.is_password:
                radius = max(3, int(4 * scale))
                spacing = max(12, int(14 * scale))
                total_width = len(self.text) * spacing

                start_x = (
                    area.x
                    if total_width <= area.width
                    else area.right - total_width
                )

                for index in range(len(self.text)):
                    center_x = start_x + index * spacing + radius
                    pygame.draw.circle(
                        screen,
                        self.TEXT,
                        (center_x, rect.centery),
                        radius,
                    )

                text_right = start_x + total_width

            else:
                text_surface = font.render(self.text, True, self.TEXT)

                x = (
                    area.x
                    if text_surface.get_width() <= area.width
                    else area.right - text_surface.get_width()
                )

                screen.blit(
                    text_surface,
                    (
                        x,
                        rect.centery - text_surface.get_height() // 2,
                    ),
                )
                text_right = x + text_surface.get_width()

        else:
            text_right = area.x

            if self.placeholder:
                placeholder_surface = font.render(
                    self.placeholder,
                    True,
                    self.PLACEHOLDER,
                )
                screen.blit(
                    placeholder_surface,
                    (
                        area.x,
                        rect.centery - placeholder_surface.get_height() // 2,
                    ),
                )

        # Animated cursor.
        if self.active and (pygame.time.get_ticks() // 500) % 2 == 0:
            cursor_x = min(text_right + 2, area.right - 1)
            cursor_top = rect.y + int(rect.height * 0.25)
            cursor_bottom = rect.bottom - int(rect.height * 0.25)

            pygame.draw.line(
                screen,
                self.BORDER_FOCUS,
                (cursor_x, cursor_top),
                (cursor_x, cursor_bottom),
                max(1, int(2 * scale)),
            )

        screen.set_clip(old_clip)
