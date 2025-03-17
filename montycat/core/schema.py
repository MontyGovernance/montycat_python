
from typing import get_origin, get_args, get_type_hints, Union
from .tools import Pointer, Timestamp

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

    def serialize(self):                    
        return self.__dict__

    def check_missing_fields(self, hints):
        """
        Verify that all required fields defined in type hints are present.

        Args:
            hints: Dictionary of type hints for the schema

        Raises:
            ValueError: If any required field is missing
        """
        for attribute, _ in hints.items(): #expected_type
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
                self.pointers[attribute] = [actual_value.keyspace, actual_value.key]
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