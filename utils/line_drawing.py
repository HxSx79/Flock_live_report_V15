import cv2
from typing import Tuple

class LineDrawer:
    def draw_lines(self, frame: cv2.Mat, line1_x: float, line2_x: float, line_y_position: float) -> cv2.Mat:
        """Draw counting lines and labels on the frame"""
        height, width = frame.shape[:2]
        
        # Define blue color and line style
        blue_color = (255, 0, 0)  # BGR format
        line_thickness = 2
        dot_length = 10  # Length of each dot
        
        # Draw first vertical dotted line (blue)
        line1_x_pos = int(width * line1_x)
        for y in range(0, height, dot_length * 2):
            start_y = y
            end_y = min(y + dot_length, height)
            cv2.line(frame, (line1_x_pos, start_y), (line1_x_pos, end_y), blue_color, line_thickness)
        
        # Draw second vertical dotted line (blue)
        line2_x_pos = int(width * line2_x)
        for y in range(0, height, dot_length * 2):
            start_y = y
            end_y = min(y + dot_length, height)
            cv2.line(frame, (line2_x_pos, start_y), (line2_x_pos, end_y), blue_color, line_thickness)
        
        # Draw horizontal dotted line (blue)
        line_y = int(height * line_y_position)
        for x in range(0, width, dot_length * 2):
            start_x = x
            end_x = min(x + dot_length, width)
            cv2.line(frame, (start_x, line_y), (end_x, line_y), blue_color, line_thickness)
        
        # Add zone labels
        self._add_zone_labels(frame, height)
        
        return frame    
    def _add_zone_labels(self, frame: cv2.Mat, height: int) -> None:
        """Add zone labels to the frame"""
        cv2.putText(frame, "Line 1", (10, int(height * 0.25)), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Line 2", (10, int(height * 0.75)), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
