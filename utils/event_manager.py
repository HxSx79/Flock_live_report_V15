from datetime import datetime

class EventManager:
    _instance = None
    
    def __init__(self):
        self.production_tracker = None
        self.socket = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = EventManager()
        return cls._instance
    
    def set_production_tracker(self, tracker):
        self.production_tracker = tracker
    
    def set_socket(self, socket):
        self.socket = socket
    
    def update_production(self, counts, crossings):
        if self.production_tracker:
            self.production_tracker.update_production(counts, crossings)
            if self.socket:
                data = self.production_tracker.get_all_data()
                data['current_time'] = datetime.now().strftime("%H:%M:%S")
                self.socket.emit('production_update', data)