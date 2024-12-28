from datetime import datetime
from typing import Dict, Optional
from .bom_reader import BOMReader
from .excel_logger import ExcelLogger

class ProductionTracker:
    def __init__(self):
        """Initialize production tracker"""
        self.line_data = {
            'Line 1': {
                'part': {
                    'program': '',
                    'part_number': '',
                    'part_description': '',
                    'track_id': '',
                    'target': '0',
                    'class_name': ''
                },
                'production': {
                    'quantity': 0,
                    'delta': 0
                },
                'scrap': {
                    'total': 0,
                    'rate': 0.0
                }
            },
            'Line 2': {
                'part': {
                    'program': '',
                    'part_number': '',
                    'part_description': '',
                    'track_id': '',
                    'target': '0',
                    'class_name': ''
                },
                'production': {
                    'quantity': 0,
                    'delta': 0
                },
                'scrap': {
                    'total': 0,
                    'rate': 0.0
                }
            }
        }
        
        # Separate tracking for production and scrap totals
        self.total_quantity = 0
        self.total_scrap = 0
        
        # Track IDs that have been counted
        self.counted_track_ids = set()
        
        # Time between parts tracking
        self.last_crossing_time = {'Line 1': None, 'Line 2': None}
        self.tbp = {'Line 1': 0, 'Line 2': 0}  # Time between parts (seconds)
        self.total_tbp = {'Line 1': 0, 'Line 2': 0}  # Total time between parts

    def update_production(self, counts: Dict[str, int], latest_crossings: Dict[str, Optional[Dict]]) -> None:
        """Update production data based on line crossings"""
        print("\nDebug - Updating production with:")
        print(f"Latest crossings: {latest_crossings}")
        
        current_time = datetime.now()
        current_hour_start = current_time.replace(minute=0, second=0, microsecond=0)
        elapsed_hour_fraction = (current_time - current_hour_start).total_seconds() / 3600.0
        
        for line_key in ['Line 1', 'Line 2']:
            # Debug - Print current state before update
            print(f"\nDebug - {line_key} BEFORE production update:")
            print(f"Production: {self.line_data[line_key]['production']}")
            print(f"Scrap: {self.line_data[line_key]['scrap']}")
            
            crossing_data = latest_crossings[line_key]
            if crossing_data:
                track_id = crossing_data['track_id']
                
                # Calculate time between parts only for new track IDs
                if track_id not in self.counted_track_ids:
                    if self.last_crossing_time[line_key]:
                        self.tbp[line_key] = int((current_time - self.last_crossing_time[line_key]).total_seconds())
                        self.total_tbp[line_key] += self.tbp[line_key]
                    self.last_crossing_time[line_key] = current_time

                # Update only part information
                target = int(crossing_data.get('target', 0))
                
                # Save current scrap data
                current_scrap_total = self.line_data[line_key]['scrap']['total']
                
                self.line_data[line_key]['part'].update({
                    'program': crossing_data['program'],
                    'part_number': crossing_data['part_number'],
                    'part_description': crossing_data['part_description'],
                    'track_id': track_id,
                    'target': target,
                    'class_name': crossing_data.get('class_name', '')
                })

                # Calculate theoretical target for current hour
                theoretical_target = int(target * elapsed_hour_fraction)
                
                # Only update quantities if this track_id hasn't been counted before
                if track_id not in self.counted_track_ids:
                    self.line_data[line_key]['production']['quantity'] += 1
                    current_quantity = self.line_data[line_key]['production']['quantity']
                    self.line_data[line_key]['production']['delta'] = current_quantity - theoretical_target
                    self.total_quantity += 1
                    self.counted_track_ids.add(track_id)
                
                # Debug - Print state after update
                print(f"\nDebug - {line_key} AFTER production update:")
                print(f"Production: {self.line_data[line_key]['production']}")
                print(f"Scrap: {self.line_data[line_key]['scrap']}")

    def update_scrap(self, line_key: str, quantity: int = 1) -> None:
        """Update scrap data for a line"""
        # Debug - Print current state before update
        print(f"\nDebug - {line_key} BEFORE scrap update:")
        print(f"Production: {self.line_data[line_key]['production']}")
        print(f"Scrap: {self.line_data[line_key]['scrap']}")
        
        # Update scrap total
        self.line_data[line_key]['scrap']['total'] += quantity
        self.total_scrap += quantity
        
        # Debug - Print state after update
        print(f"\nDebug - {line_key} AFTER scrap update:")
        print(f"Production: {self.line_data[line_key]['production']}")
        print(f"Scrap: {self.line_data[line_key]['scrap']}")

    def get_all_data(self) -> Dict:
        """Get all production data for display"""
        # Debug print current part data
        print("\nDebug - Current part data:")
        print(f"Line 1 part: {self.line_data['Line 1']['part']}")
        print(f"Line 2 part: {self.line_data['Line 2']['part']}")

        # Debug print production data
        print("\nDebug - Production data:")
        print(f"Line 1 production: {self.line_data['Line 1']['production']}")
        print(f"Line 2 production: {self.line_data['Line 2']['production']}")

        # Calculate total scrap
        total_scrap = (self.line_data['Line 1']['scrap']['total'] + 
                      self.line_data['Line 2']['scrap']['total'])

        # Create data structure exactly matching what frontend expects
        data = {
            'line1_part': {
                'program': self.line_data['Line 1']['part']['program'],
                'part_number': self.line_data['Line 1']['part']['part_number'],
                'part_description': self.line_data['Line 1']['part']['part_description'],
                'track_id': self.line_data['Line 1']['part'].get('track_id', ''),
                'target': self.line_data['Line 1']['part'].get('target', '0'),
                'class_name': self.line_data['Line 1']['part'].get('class_name', '')
            },
            'line2_part': {
                'program': self.line_data['Line 2']['part']['program'],
                'part_number': self.line_data['Line 2']['part']['part_number'],
                'part_description': self.line_data['Line 2']['part']['part_description'],
                'track_id': self.line_data['Line 2']['part'].get('track_id', ''),
                'target': self.line_data['Line 2']['part'].get('target', '0'),
                'class_name': self.line_data['Line 2']['part'].get('class_name', '')
            },
            'line1_production': {
                'quantity': self.line_data['Line 1']['production']['quantity'],
                'delta': self.line_data['Line 1']['production']['delta']
            },
            'line1_scrap': {
                'total': self.line_data['Line 1']['scrap']['total']
            },
            'line2_production': {
                'quantity': self.line_data['Line 2']['production']['quantity'],
                'delta': self.line_data['Line 2']['production']['delta']
            },
            'line2_scrap': {
                'total': self.line_data['Line 2']['scrap']['total']
            },
            'total_quantity': self.total_quantity,
            'total_delta': (self.line_data['Line 1']['production']['delta'] + 
                          self.line_data['Line 2']['production']['delta']),
            'total_scrap': total_scrap,
            'tbp_line1': self.tbp['Line 1'],
            'tbp_line2': self.tbp['Line 2'],
            'total_tbp_line1': self.total_tbp['Line 1'],
            'total_tbp_line2': self.total_tbp['Line 2']
        }

        return data