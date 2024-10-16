class Limit:
    def __init__(self, start: int = 0, stop: int = 0):
        self.start = start
        self.stop = stop

    def return_limit(self):
        return {"start": self.start, "stop": self.stop}