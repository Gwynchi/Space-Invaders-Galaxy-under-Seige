import pygame
import random

class ProfilePage:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        
        # Load the profile box text asset
        try:
            self.profile_box_img = pygame.image.load("assets/image/text/PROFILE_BOX.png").convert_alpha()
        except Exception as e:
            print(f"Error loading PROFILE_BOX.png: {e}")
            self.profile_box_img = None

        # Background moving stars setup
        self.stars = [{"x": random.randint(0, 800), "y": random.randint(0, 600), "speed": random.uniform(0.5, 2)} for _ in range(60)]
        self.shooting_stars = []
        self.shooting_star_timer = 0

        # Nickname input state
        self.nickname = ""
        self.input_active = False
        
        # Font setup for rendering text
        self.font = pygame.font.Font(None, 32)
        
        # Input box rect for nickname typing
        self.nickname_box_rect = pygame.Rect(300, 320, 200, 40)
        
        # Back button rect (temporary navigation)
        self.back_button_rect = pygame.Rect(50, 50, 100, 40)

        # Try to load existing profile info if user is logged in
        self.load_current_profile()

    def load_current_profile(self):
        """Fetches the current user profile data if available."""
        try:
            current_user = getattr(self.game_manager, "current_user", None)
            if current_user and hasattr(self.game_manager, "db"):
                db = self.game_manager.db
                profile_data = db.get_user_profile(current_user.get("username"))
                if profile_data and profile_data.get("nickname"):
                    self.nickname = profile_data["nickname"]
        except Exception as e:
            print(f"Error loading profile into page: {e}")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check if clicking the nickname text box
                if self.nickname_box_rect.collidepoint(event.pos):
                    self.input_active = True
                else:
                    self.input_active = False

                # ==========================================================
                # TEMPORARY NAVIGATION: Redirecting back to the register page
                # ==========================================================
                if self.back_button_rect.collidepoint(event.pos):
                    self.game_manager.change_scene("register_page")

            elif event.type == pygame.KEYDOWN and self.input_active:
                if event.key == pygame.K_BACKSPACE:
                    self.nickname = self.nickname[:-1]
                elif event.key == pygame.K_RETURN:
                    # Save profile on enter key
                    self.save_profile()
                    self.input_active = False
                else:
                    # Limit nickname length to 20 chars
                    if len(self.nickname) < 20:
                        self.nickname += event.unicode

    def save_profile(self):
        """Saves the nickname and profile icon changes to the database."""
        try:
            current_user = getattr(self.game_manager, "current_user", None)
            if current_user and hasattr(self.game_manager, "db"):
                username = current_user.get("username")
                # Default icon if none selected yet
                icon = current_user.get("profile_icon", "default_icon") 
                success, msg = self.game_manager.db.update_user_profile(username, icon, self.nickname)
                print(msg)
        except Exception as e:
            print(f"Error saving profile: {e}")

    def update(self):
        # Update star positions for background movement
        for star in self.stars:
            star["y"] += star["speed"]
            if star["y"] > 600:
                star["y"] = 0
                star["x"] = random.randint(0, 800)

        # Handle shooting stars spawn & updates
        self.shooting_star_timer += 1
        if self.shooting_star_timer > 150:
            self.shooting_stars.append({
                "x": random.randint(300, 800), 
                "y": 0, 
                "speed_x": -5, 
                "speed_y": 3
            })
            self.shooting_star_timer = 0

        for s in self.shooting_stars[:]:
            s["x"] += s["speed_x"]
            s["y"] += s["speed_y"]
            if s["x"] < 0 or s["y"] > 600:
                self.shooting_stars.remove(s)

    def draw(self, screen):
        # Fill background color
        screen.fill((15, 15, 35))

        # Draw moving stars
        for star in self.stars:
            pygame.draw.circle(screen, (180, 180, 220), (int(star["x"]), int(star["y"])), 1)

        # Draw shooting stars
        for s in self.shooting_stars:
            pygame.draw.line(screen, (255, 255, 255), (s["x"], s["y"]), (s["x"] - s["speed_x"] * 2, s["y"] - s["speed_y"] * 2), 2)

        # Draw the custom PROFILE_BOX asset image at the top/center
        if self.profile_box_img:
            screen.blit(self.profile_box_img, (220, 80)) # Adjust X, Y coords to fit your UI layout

        # Draw Nickname Input Box & Text
        border_color = (0, 255, 100) if self.input_active else (100, 100, 150)
        pygame.draw.rect(screen, (30, 30, 50), self.nickname_box_rect)
        pygame.draw.rect(screen, border_color, self.nickname_box_rect, 2)
        
        nick_surf = self.font.render(self.nickname, True, (255, 255, 255))
        screen.blit(nick_surf, (self.nickname_box_rect.x + 10, self.nickname_box_rect.y + 8))

        # Draw Temporary Back Button
        pygame.draw.rect(screen, (200, 50, 50), self.back_button_rect)
        back_surf = self.font.render("Back", True, (255, 255, 255))
        screen.blit(back_surf, (self.back_button_rect.x + 20, self.back_button_rect.y + 8))