from ..store_classes.kv import generic_kv, inmemory_kv

class Store:
    """
    The `Store` class represents a data store with different modes of persistence 
    and distribution. It includes subclasses for in-memory and persistent storage 
    options, with further distinctions for distributed versions of each. These 
    variations allow for flexible data storage configurations based on persistence 
    and distribution needs.

    Attributes:
        No direct attributes, but subclasses inherit from `generic_kv`, which 
        handles key-value store functionality.

    Methods:
        InMemory: A subclass for an in-memory data store.
        Persistent: A subclass for a persistent data store, which persists data 
                    across sessions or server restarts.
    """
    class InMemory(generic_kv, inmemory_kv):
        """
        Represents an in-memory data store. This store is volatile and does not 
        persist data after the program ends. It is ideal for temporary storage or 
        caching.

        Attributes:
            persistent (bool): Always False for in-memory stores.
            distributed (bool): Always False for the basic in-memory store.

        Methods:
            __init__: Initializes the in-memory store, inheriting from `generic_kv`.
        """
        # persistent = False
        distributed = False

        def __init__(self, *args, **kwargs):
            """
            Initializes the `InMemory` store, inheriting functionality from 
            `generic_kv` and providing an in-memory key-value store with no persistence 
            or distribution.

            Args:
                *args: Positional arguments to pass to the parent class constructor.
                **kwargs: Keyword arguments to pass to the parent class constructor.
            """
            super().__init__(*args, **kwargs)

        class Distributed(generic_kv, inmemory_kv):
            """
            Represents a distributed in-memory data store. This store does not 
            persist data, but it is distributed across multiple nodes or systems.

            Attributes:
                persistent (bool): Always False for distributed in-memory stores.
                distributed (bool): Always True for distributed stores.

            Methods:
                __init__: Initializes the distributed in-memory store, inheriting 
                          from `generic_kv`.
            """
            # persistent = False
            distributed = True

            def __init__(self, *args, **kwargs):
                """
                Initializes the `Distributed` in-memory store, inheriting functionality 
                from `generic_kv` and enabling distribution across multiple nodes.

                Args:
                    *args: Positional arguments to pass to the parent class constructor.
                    **kwargs: Keyword arguments to pass to the parent class constructor.
                """
                super().__init__(*args, **kwargs)

    class Persistent(generic_kv):
        """
        Represents a persistent data store. This store is designed to persist data 
        across sessions, making it suitable for long-term storage.

        Attributes:
            persistent (bool): Always True for persistent stores.
            distributed (bool): Always False for the basic persistent store.

        Methods:
            __init__: Initializes the persistent store, inheriting from `generic_kv`.
        """
        persistent = True
        distributed = False

        def __init__(self, *args, **kwargs):
            """
            Initializes the `Persistent` store, inheriting functionality from `generic_kv` 
            and providing a persistent key-value store.

            Args:
                *args: Positional arguments to pass to the parent class constructor.
                **kwargs: Keyword arguments to pass to the parent class constructor.
            """
            super().__init__(*args, **kwargs)

        class Distributed(generic_kv):
            """
            Represents a distributed persistent data store. This store persists data 
            across sessions and is distributed across multiple nodes or systems.

            Attributes:
                persistent (bool): Always True for distributed persistent stores.
                distributed (bool): Always True for distributed stores.

            Methods:
                __init__: Initializes the distributed persistent store, inheriting 
                          from `generic_kv`.
            """
            persistent = True
            distributed = True

            def __init__(self, *args, **kwargs):
                """
                Initializes the `Distributed` persistent store, inheriting functionality 
                from `generic_kv` and enabling distribution across multiple nodes while 
                ensuring persistence.

                Args:
                    *args: Positional arguments to pass to the parent class constructor.
                    **kwargs: Keyword arguments to pass to the parent class constructor.
                """
                super().__init__(*args, **kwargs)




