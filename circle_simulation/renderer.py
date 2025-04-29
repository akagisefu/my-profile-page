import pygame
import math
import config

# Initialize font for text rendering
pygame.font.init()
try:
    FONT = pygame.font.SysFont("Arial", 24)
except:
    FONT = pygame.font.Font(None, 30) # Fallback font

# draw_circle_wall function is removed as it's now part of the CircleWall class in physics.py

def draw_ball(surface, ball):
    """Draws a single ball."""
    pygame.draw.circle(surface, ball.color, (int(ball.pos.x), int(ball.pos.y)), ball.radius)

def draw_ball_count(surface, count):
    """Draws the current ball count on the screen."""
    text_surface = FONT.render(f"Balls: {count}", True, config.WHITE)
    surface.blit(text_surface, (10, 10)) # Position at top-left
