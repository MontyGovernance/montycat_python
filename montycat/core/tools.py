from enum import Enum

class Timestamp:
    """A class for handling timestamp conditions."""
    def __init__(self, timestamp=None, start=None, end=None, after=None, before=None):
        self.timestamp = timestamp
        self.start = start
        self.end = end
        self.after = after
        self.before = before

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
        return [self.keyspace, self.key]

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

class PolicyCapability(str, Enum):
    """Capabilities that can be granted through data-mesh governance policies."""
    PROVISION_KEYSPACE = "provision-keyspace"
    REMOVE_KEYSPACE = "remove-keyspace"
    MANAGE_SNAPSHOTS = "manage-snapshots"
    MANAGE_SEMANTIC = "manage-semantic"
    MANAGE_SCHEMA = "manage-schema"
    MANAGE_ACCESS = "manage-access"

class PolicyKeyspaceType(str, Enum):
    """Keyspace storage types addressable by governance policies."""
    IN_MEMORY = "inmemory"
    PERSISTENT = "persistent"
    DISTRIBUTED = "distributed"

class SemanticModel(str, Enum):
    """Compiled embedding models supported by Montycat semantic search."""
    MINI_LM = "minilm"
    BGE_SMALL = "bge-small"
    BGE_BASE = "bge-base"
    E5_SMALL = "e5-small"

class PolicyFormat(str, Enum):
    """Serialization formats accepted by policy manifest commands."""
    JSON = "json"
    YAML = "yaml"
    YML = "yml"
