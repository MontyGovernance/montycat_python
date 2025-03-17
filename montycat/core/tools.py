from enum import Enum

class Timestamp:
    """A class for handling timestamp conditions."""
    def __init__(self, timestamp=None, start=None, end=None, after=None, before=None):
        self.timestamp = timestamp  # Single timestamp
        self.start = start          # Range start
        self.end = end              # Range end
        self.after = after          # After condition
        self.before = before        # Before condition

    def serialize(self):
        """Serialize the timestamp based on its type."""
        if self.start is not None and self.end is not None:
            return {"range_timestamp": [self.start, self.end]}
        elif self.after is not None:
            return {"after_timestamp": self.after}
        elif self.before is not None:
            return {"before_timestamp": self.before}
        elif self.timestamp is not None:
            return self.timestamp
        raise ValueError("Invalid timestamp configuration")

class Pointer:
    """A simple class representing a reference pointer."""
    def __init__(self, keyspace, key):
        self.keyspace = keyspace.keyspace if hasattr(keyspace, 'keyspace') else keyspace
        self.key = key

    def serialize(self):
        """Serialize the pointer to a dictionary."""
        return {"keyspace": self.keyspace, "key": self.key}

class Limit:
    """A class for pagination limits."""
    def __init__(self, start: int = 0, stop: int = 0):
        self.start = start
        self.stop = stop

    def serialize(self):
        return {"start": self.start, "stop": self.stop}

class Permission(Enum):
    """Enum for permission levels."""
    READ = "read"
    WRITE = "write"
    ALL = "all"

    def __str__(self):
        return self.value