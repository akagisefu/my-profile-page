import pygame
import sys
import math
import random
import os
from datetime import datetime

# Import configuration and components
import config
import physics
import renderer
import exporter

class Simulation:
    def __init__(self):
        pygame.init()
        # Initialize screen, clock, etc. based on config
        self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        pygame.display.set_caption("Circle Wall Simulation")
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_angle = 0 # Initial angle of the gap (in degrees for rotation speed)

        # Initialize simulation objects
        self.balls = []
        self.circle_wall = physics.CircleWall()

        # Initialize video exporter if enabled
        self.video_exporter = None
        if config.RECORD_VIDEO:
            # Check if exporter is available and usable before initializing
            if hasattr(exporter, 'OPENCV_AVAILABLE') and exporter.OPENCV_AVAILABLE:
                self.video_exporter = exporter.VideoExporter()
            else:
                print("Video recording requested but exporter is not available/functional.")

        self.setup_initial_state()

    def setup_initial_state(self):
        """Sets up the initial balls."""
        print(f"Setting up initial state with {config.INITIAL_BALLS} ball(s).")
        for _ in range(config.INITIAL_BALLS):
            self.add_ball()

    def add_ball(self, position=None, velocity=None):
        """Adds a new ball to the simulation."""
        if len(self.balls) < config.MAX_BALLS:
            new_ball = physics.Ball(position=position, velocity=velocity)
            self.balls.append(new_ball)

    def run(self):
        """Main simulation loop."""
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0 # Delta time in seconds

            self.handle_events()
            self.update(dt)
            self.render()

            # Export frame if recording
            if self.video_exporter and self.video_exporter.enabled:
                self.video_exporter.capture_frame(self.screen)

            # Check for exit condition (e.g., max balls reached or exceeded)
            # Use >= just in case multiple balls escape simultaneously pushing count over limit
            if len(self.balls) >= config.MAX_BALLS:
                print(f"Reached or exceeded maximum balls ({len(self.balls)}/{config.MAX_BALLS}). Ending simulation.")
                self.running = False

        self.cleanup()

    def handle_events(self):
        """Handles user input and events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def update(self, dt):
        """Updates the state of the simulation."""
        # Update circle wall rotation (using degrees for easy speed control)
        self.current_angle += config.ROTATION_SPEED_DEGREES_PER_SEC * dt
        self.current_angle %= 360 # Keep angle between 0 and 360

        # Update balls and handle collisions/escapes
        balls_to_remove = []
        new_balls_needed = 0
        # Convert current angle to normalized radians for physics calculations
        current_rotation_rad = (math.radians(self.current_angle) + 2 * math.pi) % (2 * math.pi)

        # Use a copy of the list for iteration as we modify the original list
        for ball in self.balls[:]:
            ball.update(dt)
            # Pass current rotation in radians to collide_ball
            self.circle_wall.collide_ball(ball, current_rotation_rad)

            # Check if the ball went off-screen AFTER collision handling
            if ball.is_off_screen():
                 if ball not in balls_to_remove: # Avoid adding the same ball twice
                    balls_to_remove.append(ball)
                    new_balls_needed += 2 # Increment needed balls for each removed ball

        # Remove off-screen balls
        for ball in balls_to_remove:
            if ball in self.balls: # Check if it wasn't already removed (e.g., by reaching max limit)
                self.balls.remove(ball)

        # Add new balls for each one that went off-screen, respecting the limit
        for _ in range(new_balls_needed):
            # Check limit inside the loop as balls are added
            if len(self.balls) < config.MAX_BALLS:
                self.add_ball()
            else:
                break # Stop adding if limit is reached

        # Placeholder: Handle ball-ball collisions (Simple pairwise check for now)
        # This is computationally expensive (O(n^2)) and needs optimization for large N
        # For now, let's skip complex collision resolution between balls
        # for i in range(len(self.balls)):
        #     for j in range(i + 1, len(self.balls)):
        #         ball_a = self.balls[i]
        #         ball_b = self.balls[j]
        #         # physics.handle_ball_collision(ball_a, ball_b) # Needs implementation

    def render(self):
        """Renders the current state to the screen."""
        self.screen.fill(config.BLACK)

        # Render circle wall using the method from the physics object
        # Pass the current rotation angle in radians
        current_rotation_rad = (math.radians(self.current_angle) + 2 * math.pi) % (2 * math.pi)
        self.circle_wall.draw(self.screen, current_rotation_rad)

        # Render balls
        for ball in self.balls:
            renderer.draw_ball(self.screen, ball)

        # Render ball count
        renderer.draw_ball_count(self.screen, len(self.balls))

        pygame.display.flip()

    def cleanup(self):
        """Cleans up resources before exiting."""
        print("Cleaning up...")
        # Finalize video export if enabled
        if self.video_exporter and self.video_exporter.enabled:
            self.video_exporter.finalize()
        pygame.quit()
        print("Simulation finished.")

if __name__ == "__main__":
    simulation = Simulation()
    simulation.run()
    sys.exit()
