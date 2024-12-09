from typing import get_origin, get_args, get_type_hints, Union

class Timestamp:
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def serialize(self):
        return self.timestamp


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
    
class Schema:
    def __init__(self, **kwargs):
        hints = get_type_hints(self.__class__)
        for key, value in kwargs.items():
            setattr(self, key, value)
        for attribute in hints:
            if not hasattr(self, attribute):
                setattr(self, attribute, None)
        
        # Ensure all fields are provided and validate types
        self.check_missing_fields(hints)
        self.validate_types()

    def __repr__(self):
        return str(self.__dict__)
    
    def __str__(self):
        return str(self.__dict__)
    
    def serialize(self):
        for attr_name in dir(self):
            if "_pointer" in attr_name:
                attr_value = getattr(self, attr_name)
                if hasattr(attr_value, "serialize"):
                    setattr(self, attr_name, [attr_value.namespace, str(attr_value.key)])
            if "_timestamp" in attr_name:
                attr_value = getattr(self, attr_name)
                if hasattr(attr_value, "serialize"):
                    setattr(self, attr_name, attr_value.serialize())
                    
        return self.__dict__

    def check_missing_fields(self, hints):
        """Ensure all required fields are initialized."""
        for attribute, expected_type in hints.items():
            if getattr(self, attribute) is None:
                raise ValueError(f"Missing required field: '{attribute}'")
    
    def validate_types(self):
        hints = get_type_hints(self.__class__)
        for attribute, expected_type in hints.items():
            actual_value = getattr(self, attribute)
            origin = get_origin(expected_type)
            
            # Enforce naming rules for specific types
            if expected_type is Pointer:

                # put attribute into a new dict "pointers"
                if 'pointers' not in self.__dict__:
                    self.pointers = {}
                self.pointers[attribute] = [actual_value.namespace, actual_value.key]
                #remove the attribute
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
