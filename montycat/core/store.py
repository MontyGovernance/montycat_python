from ..store_classes.kv import generic_kv

class Store:
    class InMemory(generic_kv):
        persistent = False
        distributed = False

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        class Distributed(generic_kv):
            persistent = False
            distributed = True

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

    class Persistent(generic_kv):
        persistent = True
        distributed = False

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        class Distributed(generic_kv):
            persistent = True
            distributed = True

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)



