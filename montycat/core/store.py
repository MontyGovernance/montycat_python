from ..store_classes.kv import generic_kv
from ..store_classes.inmemory import inmemory_kv
from ..store_classes.persistent import  persistent_kv

class Keyspace:
    """
    The `Keyspace` class represents a data keyspace with different modes of persistence 
    and distribution. It includes subclasses for in-memory and persistent storage 
    options, with further distinctions for distributed versions of each. These 
    variations allow for flexible data storage configurations based on persistence 
    and distribution needs.

    Attributes:
        No direct attributes, but subclasses inherit from `generic_kv`, which 
        handles key-value keyspace functionality.

    Methods:
        InMemory: A subclass for an in-memory data keyspace.
        Persistent: A subclass for a persistent data keyspace, which persists data 
                    across sessions or server restarts.
    """
    class InMemory(generic_kv, inmemory_kv):
        """
        Represents an in-memory data keyspace. This keyspace is volatile and does not 
        persist data after the program ends. It is ideal for temporary storage or 
        caching.

        Attributes:
            persistent (bool): Always False for in-memory keyspaces.
            distributed (bool): Always False for the basic in-memory keyspace.

        Methods:
            __init__: Initializes the in-memory keyspace, inheriting from `generic_kv`.
        """
        # persistent = False
        distributed = False

        def __init__(self, *args, **kwargs):
            """
            Initializes the `InMemory` keyspace, inheriting functionality from 
            `generic_kv` and providing an in-memory key-value keyspace with no persistence 
            or distribution.

            Args:
                *args: Positional arguments to pass to the parent class constructor.
                **kwargs: Keyword arguments to pass to the parent class constructor.
            """
            super().__init__(*args, **kwargs)

        class Distributed(generic_kv, inmemory_kv):
            """
            Represents a distributed in-memory data keyspace. This keyspace does not 
            persist data, but it is distributed across multiple nodes or systems.

            Attributes:
                persistent (bool): Always False for distributed in-memory keyspaces.
                distributed (bool): Always True for distributed keyspaces.

            Methods:
                __init__: Initializes the distributed in-memory keyspace, inheriting 
                          from `generic_kv`.
            """
            distributed = True

            def __init__(self, *args, **kwargs):
                """
                Initializes the `Distributed` in-memory keyspace, inheriting functionality 
                from `generic_kv` and enabling distribution across multiple nodes.

                Args:
                    *args: Positional arguments to pass to the parent class constructor.
                    **kwargs: Keyword arguments to pass to the parent class constructor.
                """
                super().__init__(*args, **kwargs)

    class Persistent(generic_kv, persistent_kv):
        """
        Represents a persistent data keyspace. This keyspace is designed to persist data 
        across sessions, making it suitable for long-term storage.

        Attributes:
            persistent (bool): Always True for persistent keyspaces.
            distributed (bool): Always False for the basic persistent keyspace.
            cache (Union[int, None]): Optional cache size for the keyspace. Should be setup in MB. If parameter was not set default value (10 MB) will be used.
            compression (bool): Indicates whether data compression is enabled. Default is False.

        Methods:
            __init__: Initializes the persistent keyspace, inheriting from `generic_kv`.
        """
        distributed = False

        def __init__(self, *args, **kwargs):
            """
            Initializes the `Persistent` keyspace, inheriting functionality from `generic_kv` 
            and providing a persistent key-value keyspace.

            Args:
                *args: Positional arguments to pass to the parent class constructor.
                **kwargs: Keyword arguments to pass to the parent class constructor.
            """
            super().__init__(*args, **kwargs)

        class Distributed(generic_kv, persistent_kv):
            """
            Represents a distributed persistent data keyspace. This keyspace persists data 
            across sessions and is distributed across multiple nodes or systems.

            Attributes:
                persistent (bool): Always True for distributed persistent keyspaces.
                distributed (bool): Always True for distributed keyspaces.

            Methods:
                __init__: Initializes the distributed persistent keyspace, inheriting 
                          from `generic_kv`.
            """
            persistent = True
            distributed = True

            def __init__(self, *args, **kwargs):
                """
                Initializes the `Distributed` persistent keyspace, inheriting functionality 
                from `generic_kv` and enabling distribution across multiple nodes while 
                ensuring persistence.

                Args:
                    *args: Positional arguments to pass to the parent class constructor.
                    **kwargs: Keyword arguments to pass to the parent class constructor.
                """
                super().__init__(*args, **kwargs)




