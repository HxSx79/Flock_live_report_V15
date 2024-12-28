from typing import Dict, Optional
from .geometry import Point

class TrackingState:
    def __init__(self):
        self._positions: Dict[int, Point] = {}
        self.frame_width = 0
        self.frame_height = 0
    
    def update_frame_dimensions(self, width: int, height: int) -> None:
        """Update frame dimensions"""
        self.frame_width = width
        self.frame_height = height
    
    def has_previous_position(self, track_id: int) -> bool:
        """Check if we have a previous position for this track ID"""
        return track_id in self._positions
    
    def get_previous_position(self, track_id: int) -> Optional[Point]:
        """Get the previous position for a track ID"""
        return self._positions.get(track_id)
    
    def update_position(self, track_id: int, position: Point) -> None:
        """Update the position for a track ID"""
        self._positions[track_id] = position
    
    def reset(self) -> None:
        """Clear all tracking data"""
        self._positions.clear()