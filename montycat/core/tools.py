from typing import get_origin, get_args, get_type_hints, Union

class Timestamp:
    """
    A class for handling timestamp-related operations and their various formats.
    
    This class provides functionality for working with timestamps in different contexts,
    including single timestamps, timestamp ranges, and before/after timestamp conditions.
    """
    def __init__(self, timestamp):
        """
        Initialize a Timestamp object.

        Args:
            timestamp: The timestamp value to be stored
        """
        self.timestamp = timestamp

    def serialize(self):
        """
        Serialize the timestamp value.

        Returns:
            The raw timestamp value
        """
        return self.timestamp
    
    class range:
        """
        Nested class for handling timestamp ranges with start and end values.
        """
        def __init__(self, start_timestamp, end_timestamp):
            """
            Initialize a timestamp range.

            Args:
                start_timestamp: The beginning of the timestamp range
                end_timestamp: The end of the timestamp range
            """
            self.start_timestamp = start_timestamp
            self.end_timestamp = end_timestamp

        def serialize(self):
            """
            Serialize the timestamp range.

            Returns:
                dict: A dictionary containing the range timestamps as a list
            """
            return {"range_timestamp": [self.start_timestamp, self.end_timestamp]}
        
    class after:
        """
        Nested class for handling timestamps after a specific point.
        """
        def __init__(self, after_timestamp):
            """
            Initialize an after timestamp condition.

            Args:
                after_timestamp: The timestamp to compare against
            """
            self.after_timestamp = after_timestamp

        def serialize(self):
            """
            Serialize the after timestamp condition.

            Returns:
                dict: The object's dictionary representation
            """
            return self.__dict__

    class before:
        """
        Nested class for handling timestamps before a specific point.
        """
        def __init__(self, before_timestamp):
            """
            Initialize a before timestamp condition.

            Args:
                before_timestamp: The timestamp to compare against
            """
            self.before_timestamp = before_timestamp

        def serialize(self):
            """
            Serialize the before timestamp condition.

            Returns:
                dict: The object's dictionary representation
            """
            return self.__dict__


class Pointer:
    """
    A class representing a reference pointer with namespace and key components.
    
    This class is used to create references to other objects or resources within
    the system using a namespace and key combination.
    """
    def __init__(self, namespace, key):
        """
        Initialize a Pointer object.

        Args:
            namespace: The namespace object containing the namespace value
            key: The key value for the pointer
        """
        self.namespace = namespace.namespace
        self.key = key
        
    def __str__(self):
        """
        Get the string representation of the Pointer object.
        
        Returns:
            str: String representation of the Pointer's dictionary form
        """
        return str(self.__dict__)
    
    def serialize(self):
        """
        Serialize the Pointer object into a dictionary format.

        Returns:
            dict: Dictionary containing the namespace and key
        """
        return self.__dict__

class SchemaMetaclass(type):
    """
    Metaclass for Schema classes that provides custom string representation.
    
    This metaclass modifies how Schema classes are represented as strings,
    returning just the class name instead of the default representation.
    """
    def __str__(cls) -> str:
        """Return the class name as string representation."""
        return cls.__name__
    
    def __repr__(cls) -> str:
        """Return the class name as official representation."""
        return cls.__name__

class Schema(metaclass=SchemaMetaclass):
    """
    Base class for creating schema definitions with type validation and serialization.
    
    This class provides the foundation for creating strongly-typed schema objects
    with automatic validation of fields and types. It supports features such as:
    - Automatic type checking based on type hints
    - Required field validation
    - Extra field detection
    - Special handling for Pointer and Timestamp types
    - Serialization capabilities
    """
    def __init__(self, **kwargs):
        """
        Initialize a Schema instance with the provided field values.

        Args:
            **kwargs: Keyword arguments representing the schema fields and their values

        Raises:
            ValueError: If required fields are missing or unexpected fields are present
            TypeError: If field values don't match their type hints
        """
        hints = get_type_hints(self.__class__)
        for key, value in kwargs.items():
            setattr(self, key, value)
        for attribute in hints:
            if not hasattr(self, attribute):
                setattr(self, attribute, None)
        self.check_missing_fields(hints)
        self.check_extra_fields(hints)
        self.validate_types()
        self.schema = self.__class__.__name__

    def check_missing_fields(self, hints):
        """
        Verify that all required fields defined in type hints are present.

        Args:
            hints: Dictionary of type hints for the schema

        Raises:
            ValueError: If any required field is missing
        """
        for attribute, expected_type in hints.items():
            if getattr(self, attribute) is None:
                raise ValueError(f"Missing required field: '{attribute}'")
    
    def check_extra_fields(self, hints):
        """
        Verify that no unexpected fields are present in the instance.

        Args:
            hints: Dictionary of type hints for the schema

        Raises:
            ValueError: If any unexpected field is found
        """
        defined_fields = set(hints.keys())
        for attribute in self.__dict__:
            if attribute not in defined_fields and not attribute.startswith('_'):
                raise ValueError(f"Unexpected field '{attribute}' found in the instance.")
    
    def validate_types(self):
        """
        Validate the types of all fields against their type hints.
        
        This method performs type checking and special handling for Pointer and
        Timestamp types, as well as handling Union types. It reorganizes Pointer
        and Timestamp fields into dedicated collections.

        Raises:
            TypeError: If any field's value doesn't match its type hint
        """
        hints = get_type_hints(self.__class__)
        for attribute, expected_type in hints.items():
            actual_value = getattr(self, attribute)
            origin = get_origin(expected_type)
            
            if expected_type is Pointer:
                if 'pointers' not in self.__dict__:
                    self.pointers = {}
                self.pointers[attribute] = [actual_value.namespace, actual_value.key]
                delattr(self, attribute)

            if expected_type is Timestamp:
                if 'timestamps' not in self.__dict__:
                    self.timestamps = {}
                self.timestamps[attribute] = actual_value.timestamp
                delattr(self, attribute)

            if origin is Union:
                expected_types = get_args(expected_type)
                if not isinstance(actual_value, expected_types) and actual_value is not None:
                    raise TypeError(
                        f"Attribute '{attribute}' should be one of types {expected_types}, "
                        f"but got '{type(actual_value).__name__}'"
                    )
            else:
                if not isinstance(actual_value, expected_type) and actual_value is not None:
                    raise TypeError(
                        f"Attribute '{attribute}' should be of type '{expected_type.__name__}', "
                        f"but got '{type(actual_value).__name__}'"
                    )

class Limit:
    """
    A class for handling pagination limits with start and stop indices.

    This class provides a clean interface for defining pagination ranges and
    serializing them for use in queries or other operations requiring pagination.
    """
    def __init__(self, start: int = 0, stop: int = 0):
        """
        Initialize a Limit object with start and stop indices.

        Args:
            start (int): The starting index (default: 0)
            stop (int): The stopping index (default: 0)
        """
        self.start = start
        self.stop = stop

    def return_limit(self):
        """
        Get the limit range as a dictionary.

        Returns:
            dict: A dictionary with 'start' and 'stop' keys containing the indices
        """
        return {"start": self.start, "stop": self.stop}
    
class MetaclassPermission(type):
    """
    Metaclass for Permission classes that provides custom string representation.
    
    This metaclass modifies how Permission classes are represented as strings,
    returning their permission value instead of the default representation.
    """
    def __str__(cls):
        """Return the permission value as string representation."""
        return cls.permission
    
    def __repr__(cls):
        """Return the permission value as official representation."""
        return cls.permission

class Permission:
    """
    A class providing permission level definitions through nested classes.
    
    This class defines three permission levels (read, write, and all) using
    nested classes with metaclass-based string representation.
    """
    class read(metaclass=MetaclassPermission):
        """Read permission level."""
        permission = "read"
    class write(metaclass=MetaclassPermission):
        """Write permission level."""
        permission = "write"
    class all(metaclass=MetaclassPermission):
        """All permissions level."""
        permission = "all"