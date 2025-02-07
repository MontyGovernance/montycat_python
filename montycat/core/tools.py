from typing import get_origin, get_args, get_type_hints, Union

class Timestamp:
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def serialize(self):
        return self.timestamp
    
    class range:
        def __init__(self, start_timestamp, end_timestamp):
            self.start_timestamp = start_timestamp
            self.end_timestamp = end_timestamp

        def serialize(self):
            return {"range_timestamp": [self.start_timestamp, self.end_timestamp]}
        
    class after:
        def __init__(self, after_timestamp):
            self.after_timestamp = after_timestamp

        def serialize(self):
            return self.__dict__

    class before:
        def __init__(self, before_timestamp):
            self.before_timestamp = before_timestamp

        def serialize(self):
            return self.__dict__


class Pointer:
    def __init__(self, namespace, key):
        self.namespace = namespace.namespace
        self.key = key
        
    def __str__(self):
        """
        Returns the string representation of the `Pointer` object, showing its 
        dictionary representation.
        
        Returns:
            str: String representation of the `Pointer` object.
        """
        return str(self.__dict__)
    
    def serialize(self):
        """
        Serializes the `Pointer` object into a dictionary format for easy 
        storage or transmission.

        Returns:
            dict: A dictionary representation of the `Pointer` object.
        """
        return self.__dict__

class SchemaMetaclass(type):
    def __str__(cls) -> str:
        return cls.__name__
    
    def __repr__(cls) -> str:
        return cls.__name__

class Schema(metaclass=SchemaMetaclass):
    def __init__(self, **kwargs):
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

    def __repr__(self):
        return str(self.__dict__)
    
    def __str__(self):
        return str(self.__dict__)
    
    def get_schema_name(self):
        return self.__class__.__name__
    
    def serialize(self):                    
        return self.__dict__

    def check_missing_fields(self, hints):
        """Ensure all required fields are initialized."""
        for attribute, expected_type in hints.items():
            if getattr(self, attribute) is None:
                raise ValueError(f"Missing required field: '{attribute}'")
    
    def check_extra_fields(self, hints):
        """Ensure no extra fields are present."""
        defined_fields = set(hints.keys())

        for attribute in self.__dict__:
            if attribute not in defined_fields and not attribute.startswith('_'):
                raise ValueError(f"Unexpected field '{attribute}' found in the instance.")
    
    def validate_types(self):
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

            # Handle Union types (e.g., int | None)
            if origin is Union:
                expected_types = get_args(expected_type)
                if not isinstance(actual_value, expected_types) and actual_value is not None:
                    raise TypeError(
                        f"Attribute '{attribute}' should be one of types {expected_types}, "
                        f"but got '{type(actual_value).__name__}'"
                    )
            else:
                # Validate against non-Union type
                if not isinstance(actual_value, expected_type) and actual_value is not None:
                    raise TypeError(
                        f"Attribute '{attribute}' should be of type '{expected_type.__name__}', "
                        f"but got '{type(actual_value).__name__}'"
                    )
                
class Limit:
    """
    A class to represent pagination limits with start and stop indices.

    This class is used to define the range of records to be retrieved or processed,
    typically for pagination in queries. It allows you to specify a starting index 
    and a stopping index, and it can return these as a dictionary.

    Attributes:
        start (int): The starting index for the range (default is 0).
        stop (int): The stopping index for the range (default is 0).
    """
    def __init__(self, start: int = 0, stop: int = 0):
        """
        Initializes the Limit object with optional start and stop values.

        Args:
            start (int): The starting index for the range (default is 0).
            stop (int): The stopping index for the range (default is 0).
        """
        self.start = start
        self.stop = stop

    def return_limit(self):
        """
        Returns the pagination limit as a dictionary with 'start' and 'stop' keys.

        This method is useful for returning the limit values in a structured format 
        that can be used in query construction or other operations requiring pagination limits.

        Returns:
            dict: A dictionary containing the 'start' and 'stop' indices.
        """
        return {"start": self.start, "stop": self.stop}
    
class MetaclassPermission(type):
    def __str__(cls):
        return cls.permission
    
    def __repr__(cls):
        return cls.permission

class Permission:
    class read(metaclass=MetaclassPermission):
        permission = "read"
    class write(metaclass=MetaclassPermission):
        permission = "write"
    class all(metaclass=MetaclassPermission):
        permission = "all"
