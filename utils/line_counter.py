import cv2
from typing import Dict, List, Set, Optional
from .geometry import Point
from .tracking import TrackingState
from .bom_reader import BOMReader
from .event_manager import EventManager

class LineCounter:
    def __init__(self):
        self.counted_ids: Set[int] = set()
        self.center_x = 0.5  # Center of the frame
        self.line_spacing = 20  # 20 pixels between lines
        self.line_y_position = 0.5  # Horizontal line at 50% of height
        self.tracking_state = TrackingState()
        self.counts = {'line1': 0, 'line2': 0}
        self.latest_crossings = {'Line 1': None, 'Line 2': None}
        self.frame_width = 0
        self.frame_height = 0
        self.bom_reader = BOMReader()
        self.event_manager = EventManager.get_instance()
        self.objects_between_lines = {}  # Track objects between the lines
        self.line1_x = 0  # Will be calculated when frame dimensions are set
        self.line2_x = 0  # Will be calculated when frame dimensions are set

    def update_frame_dimensions(self, width: int, height: int) -> None:
        """Update frame dimensions"""
        self.frame_width = width
        self.frame_height = height
        center_x_pixels = int(self.frame_width * self.center_x)
        self.line1_x = (center_x_pixels - self.line_spacing/2) / self.frame_width
        self.line2_x = (center_x_pixels + self.line_spacing/2) / self.frame_width
        self.tracking_state.update_frame_dimensions(width, height)

    def update_counts(self, detections: List[Dict]) -> None:
        """Update part counts based on detected objects between the lines"""
        if not detections or self.frame_width == 0 or self.frame_height == 0:
            return

        line1_x = int(self.frame_width * self.line1_x)
        line2_x = int(self.frame_width * self.line2_x)
        line_y = int(self.frame_height * self.line_y_position)

        for detection in detections:
            track_id = detection['track_id']
            x = detection['center'][0]
            y = detection['center'][1]

            # Check if object is between the lines
            if line1_x <= x <= line2_x:
                if track_id not in self.counted_ids and track_id not in self.objects_between_lines:
                    # New object detected between lines
                    self.objects_between_lines[track_id] = {
                        'detection': detection,
                        'position': Point(x, y),
                        'timestamp': cv2.getTickCount()
                    }
                    self._process_detection(track_id, detection, Point(x, y))
            else:
                # Remove object from tracking if it's outside the lines
                self.objects_between_lines.pop(track_id, None)

    def _process_detection(self, track_id: int, detection: Dict, position: Point) -> None:
        """Process a detection between the lines"""
        if track_id not in self.counted_ids:
            line_y = int(self.frame_height * self.line_y_position)
            line_key = 'Line 1' if position.y < line_y else 'Line 2'
            
            # First, retrieve part information from BOM
            class_name = detection['class_name']
            part_info = self.bom_reader.get_part_info(class_name)
            
            print(f"\nDebug - LineCounter - Creating crossing data for {line_key}:")
            print(f"  Program: {part_info['program']}")
            print(f"  Part Number: {part_info['part_number']}")
            print(f"  Part Description: {part_info['part_description']}")
            
            # Create crossing data with exact property names expected by frontend
            self.latest_crossings[line_key] = {
                'class_name': detection['class_name'],
                'program': part_info['program'],
                'part_number': part_info['part_number'],
                'part_description': part_info['part_description'],
                'target': part_info['target'],
                'track_id': track_id,
                'timestamp': cv2.getTickCount()
            }
            
            # Update counts
            count_key = 'line1' if line_key == 'Line 1' else 'line2'
            self.counts[count_key] += 1
            
            # Log which line is being updated
            print(f"\nUpdating Current Part {line_key} information:")
            print(f"  Program: {part_info['program']}")
            print(f"  Part Number: {part_info['part_number']}")
            print(f"  Part Description: {part_info['part_description']}")
            
            # Force immediate update of production tracker to refresh web display
            self.event_manager.update_production(
                self.counts,
                self.get_latest_crossings()
            )
            
            self.counted_ids.add(track_id)

    def get_counts(self) -> Dict[str, int]:
        """Get current counts for both lines"""
        return self.counts.copy()

    def get_latest_crossings(self) -> Dict[str, Optional[Dict]]:
        """Get information about the latest crossings for each line"""
        return self.latest_crossings.copy()

    def reset_counts(self) -> None:
        """Reset only the counting data without losing part information"""
        self.counted_ids.clear()
        self.counts = {'line1': 0, 'line2': 0}
        print("Debug - LineCounter counts reset")

    def reset(self) -> None:
        """Reset all counting data"""
        self.counted_ids.clear()
        self.tracking_state.reset()
        self.counts = {'line1': 0, 'line2': 0}
        self.latest_crossings = {'Line 1': None, 'Line 2': None}
        print("Debug - LineCounter reset completed")
        # Don't reset BOMReader connection