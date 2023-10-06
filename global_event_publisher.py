class EventPublisher:
    def __init__(self):
        self.listeners = {}
        
    def emit(self, event_name, data):
        for listener in self.listeners.get(event_name, []):
            listener(data)

    def on(self, event_name, listener):
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(listener)

event_publisher = EventPublisher()