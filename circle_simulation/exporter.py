import pygame
import cv2
import numpy as np
import os
from datetime import datetime
import config

# Check if OpenCV is available
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("Warning: OpenCV not found. Video export disabled.")
    print("Install OpenCV using: pip install opencv-python")

class VideoExporter:
    def __init__(self, width=config.WIDTH, height=config.HEIGHT, fps=config.VIDEO_FPS,
                 filename_prefix=config.VIDEO_FILENAME_PREFIX, output_dir=config.VIDEO_DIR):

        if not OPENCV_AVAILABLE or not config.RECORD_VIDEO:
            self.video_writer = None
            self.enabled = False
            print("Video export is disabled (OpenCV not found or RECORD_VIDEO=False).")
            return

        self.enabled = True
        self.width = width
        self.height = height
        self.fps = fps

        # Create video directory if it doesn't exist
        # Ensure the path is relative to the script's directory if needed
        # Assuming exporter.py is in the same dir as main.py
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_path = os.path.join(script_dir, output_dir)
        os.makedirs(self.output_path, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = os.path.join(self.output_path, f"{filename_prefix}_{timestamp}.mp4")

        # Define the codec and create VideoWriter object
        # Using 'mp4v' for .mp4 files
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        try:
            self.video_writer = cv2.VideoWriter(self.filename, fourcc, self.fps, (self.width, self.height))
            if not self.video_writer.isOpened():
                raise IOError(f"Could not open video writer for '{self.filename}'")
            print(f"Video recording enabled. Saving to: {self.filename}")
        except Exception as e:
            print(f"Error initializing VideoWriter: {e}")
            self.video_writer = None
            self.enabled = False

    def capture_frame(self, surface):
        """Captures a frame from the Pygame surface and writes it to the video."""
        if not self.enabled or self.video_writer is None:
            return

        try:
            # Get pixel data from Pygame surface
            frame_data = pygame.surfarray.array3d(surface)
            # Pygame uses (width, height, channels), OpenCV uses (height, width, channels)
            # Pygame uses RGB, OpenCV uses BGR
            frame_data = frame_data.swapaxes(0, 1) # Transpose width and height
            frame_data = cv2.cvtColor(frame_data, cv2.COLOR_RGB2BGR) # Convert RGB to BGR

            self.video_writer.write(frame_data)
        except Exception as e:
            print(f"Error capturing frame: {e}")
            # Optionally disable further recording on error
            # self.enabled = False
            # self.finalize()

    def finalize(self):
        """Releases the video writer object."""
        if self.enabled and self.video_writer is not None:
            print(f"Finalizing video export: {self.filename}")
            self.video_writer.release()
            self.video_writer = None # Ensure it's not used again
            print("Video export finished.")
        self.enabled = False # Mark as finalized
