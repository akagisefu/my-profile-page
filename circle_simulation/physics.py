import pygame
import math
import random
import config

class Ball:
    def __init__(self, position=None, velocity=None, radius=config.BALL_RADIUS, color=None):
        self.radius = radius
        # Assign a random color if none is provided
        self.color = color if color is not None else random.choice(config.BALL_COLORS)

        if position is None:
            # Start near the center, avoiding the exact center
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0, config.CIRCLE_RADIUS * 0.1)
            self.pos = pygame.Vector2(
                config.CIRCLE_CENTER[0] + dist * math.cos(angle),
                config.CIRCLE_CENTER[1] + dist * math.sin(angle)
            )
        else:
            self.pos = pygame.Vector2(position)

        if velocity is None:
            # Random initial velocity
            angle = random.uniform(0, 2 * math.pi)
            self.vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * config.BALL_SPEED
        else:
            self.vel = pygame.Vector2(velocity)

    def update(self, dt):
        """Updates the ball's position based on its velocity."""
        self.pos += self.vel * dt * 100 # Scale velocity for noticeable movement

    def draw(self, surface):
        """Draws the ball on the given surface."""
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

    def is_off_screen(self, width=config.WIDTH, height=config.HEIGHT):
        """Checks if the ball is completely outside the screen boundaries."""
        return (self.pos.x + self.radius < 0 or
                self.pos.x - self.radius > width or
                self.pos.y + self.radius < 0 or
                self.pos.y - self.radius > height)

class CircleWall:
    def __init__(self, center=config.CIRCLE_CENTER, radius=config.CIRCLE_RADIUS,
                 thickness=config.CIRCLE_THICKNESS, gap_angle_degrees=config.GAP_ANGLE_DEGREES):
        self.center = pygame.Vector2(center)
        self.radius = radius
        self.thickness = thickness
        self.gap_angle_rad = math.radians(gap_angle_degrees) # Store gap size in radians
        self.half_gap_rad = self.gap_angle_rad / 2
        # Collision primarily happens at self.radius

    def _get_gap_boundaries(self, current_rotation_rad):
        """Calculates the start and end angles of the gap in radians [0, 2*pi),
           using Pygame's angle convention (0=right, positive=counter-clockwise)."""
        # Normalize rotation to [0, 2*pi)
        norm_rotation_rad = (current_rotation_rad + 2 * math.pi) % (2 * math.pi)
        # Gap starts half-gap before rotation and ends half-gap after
        start_gap_rad = (norm_rotation_rad - self.half_gap_rad + 2 * math.pi) % (2 * math.pi)
        end_gap_rad = (norm_rotation_rad + self.half_gap_rad + 2 * math.pi) % (2 * math.pi)
        return start_gap_rad, end_gap_rad

    def is_inside_gap(self, angle_rad, current_rotation_rad):
        """Checks if a given angle (radians, Pygame convention) falls within the gap."""
        start_gap_rad, end_gap_rad = self._get_gap_boundaries(current_rotation_rad)
        # Normalize the angle to [0, 2*pi)
        norm_angle_rad = (angle_rad + 2 * math.pi) % (2 * math.pi)

        # Check if the angle is within the gap range, handling wrap-around
        if start_gap_rad < end_gap_rad: # Gap does not wrap around 0 radians
            return start_gap_rad < norm_angle_rad < end_gap_rad
        else: # Gap wraps around 0 radians (e.g., starts at 6.0, ends at 0.5)
            return norm_angle_rad > start_gap_rad or norm_angle_rad < end_gap_rad

    def collide_ball(self, ball, current_rotation_rad): # Parameter is radians
        """Handles collision between the wall and a ball.
        Corrects position and reflects velocity if collision occurs with solid wall.
        Returns:
            True: If the ball collided with the solid part of the wall.
            False: If no collision occurred or the ball is in the gap area.
        """
        vec_to_ball = ball.pos - self.center
        dist_from_center = vec_to_ball.length()
        collision_radius = self.radius # Collision boundary

        # Avoid division by zero or issues very close to center
        if dist_from_center < 1e-6:
            return False

        # Check if the ball's *outer edge* is at or beyond the collision radius
        if dist_from_center + ball.radius >= collision_radius:
            # Calculate the angle using atan2(-y, x) for Pygame convention
            ball_angle_rad = math.atan2(-vec_to_ball.y, vec_to_ball.x)

            # Check if the ball's angle is within the gap (using Pygame angle convention)
            if self.is_inside_gap(ball_angle_rad, current_rotation_rad):
                # Ball is aligned with the gap, no collision with the solid wall
                # Escape check (ball center > radius) is handled by is_off_screen in main.py
                return False
            else:
                # Ball angle is NOT in the gap -> Collision with the solid wall

                # Calculate penetration depth
                penetration = (dist_from_center + ball.radius) - collision_radius

                # Correct position only if penetrating
                if penetration > 0:
                    # Move ball back along the normal vector (away from center)
                    # so its edge is exactly at the collision_radius
                    normal = vec_to_ball.normalize()
                    ball.pos -= normal * penetration

                    # Reflect velocity radially only if moving towards the wall
                    # Normal points outward from center. Ball moving towards wall has vel.dot(normal) > 0.
                    if ball.vel.dot(normal) > 0:
                        ball.vel = ball.vel.reflect(normal)
                        # Optional: Apply restitution (slightly reduce speed after bounce)
                        # ball.vel *= 0.98
                    return True # Collision occurred and was handled

        # No collision detected with the solid wall part
        return False

    def draw(self, surface, current_rotation_rad): # Changed parameter to radians
        """Draws the rotating circle wall with a gap, consistent with collision logic."""
        center_x, center_y = int(self.center.x), int(self.center.y)
        radius = int(self.radius)
        # Use a thickness consistent with config, ensure it's an int
        thickness = max(1, int(config.CIRCLE_THICKNESS)) # Ensure thickness is at least 1

        # Calculate gap boundaries in radians using the same helper function as collision detection
        gap_start_angle_rad, gap_end_angle_rad = self._get_gap_boundaries(current_rotation_rad)

        # Define the bounding rectangle for the arc drawing
        # Make radius slightly larger for drawing to encompass the collision radius visually
        draw_radius = radius
        rect = pygame.Rect(center_x - draw_radius, center_y - draw_radius, 2 * draw_radius, 2 * draw_radius)

        # Draw the solid part of the wall using pygame.draw.arc
        # Pygame angles: 0 is right (positive x-axis), increases counter-clockwise.
        # We need to draw the arc segment *excluding* the gap.
        # Draw from the end of the gap angle to the start of the gap angle (counter-clockwise).
        draw_start_rad = gap_end_angle_rad
        draw_end_rad = gap_start_angle_rad

        # Ensure thickness is valid for pygame.draw.arc (must be <= radius)
        draw_thickness = min(thickness, draw_radius)
        if draw_thickness <= 0: draw_thickness = 1 # Minimum thickness of 1

        try:
            # Handle the case where the solid arc crosses the 0 angle
            if draw_start_rad > draw_end_rad:
                 # Draw in two parts
                 pygame.draw.arc(surface, config.WHITE, rect, draw_start_rad, 2 * math.pi, draw_thickness)
                 pygame.draw.arc(surface, config.WHITE, rect, 0, draw_end_rad, draw_thickness)
            elif abs(draw_start_rad - draw_end_rad) > 1e-6: # Normal case, ensure angles are different
                 pygame.draw.arc(surface, config.WHITE, rect, draw_start_rad, draw_end_rad, draw_thickness)
            # If draw_start is very close to draw_end (gap is ~360 deg), draw nothing.
        except ValueError as e:
            print(f"Error drawing arc: {e}, rect={rect}, start={draw_start_rad}, end={draw_end_rad}, thickness={draw_thickness}")
