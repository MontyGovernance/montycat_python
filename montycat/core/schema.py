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
    # """
    # A class that represents a reference to another entity, often used for 
    # creating relationships between data objects in a schema. A `Pointer` holds 
    # a reference to a store namespace and its associated value. This is useful 
    # when dealing with schema-based models where entities point to other entities 
    # or collections.

    # Attributes:
    #     namespace (str): The namespace for the store this pointer refers to.
    #     value (str): The value associated with this pointer.

    # Methods:
    #     __str__: Returns a string representation of the pointer.
    #     serialize: Returns a serialized dictionary representation of the pointer.
    # """
    # def __init__(self, **kwargs):
    #     """
    #     Initializes a `Pointer` object with keyword arguments. Each keyword 
    #     argument is expected to be a tuple containing the store namespace and 
    #     the associated value.

    #     Args:
    #         kwargs (dict): Keyword arguments where keys are attribute names 
    #                        and values are tuples containing a store namespace 
    #                        and a value.

    #     Example:
    #         pointers = Pointer(field1=("namespace1", "value1"), field2=("namespace2", "value2"))
    #     """
    #     # Should enforce word pointers
    #     for key, value in kwargs.items():
    #         # Each pointer is initialized with a store namespace and a value
    #         print(key, value)
    #         setattr(self, key, [value[0].namespace, value[1]])

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
            if expected_type is Pointer and "_pointer" not in attribute:
                raise SyntaxError(
                    f"Type Pointer must have keyword '_pointer' within its name, but got '{attribute}'"
                )
            if expected_type is Timestamp and "_timestamp" not in attribute:
                raise SyntaxError(
                    f'Type Timestamp must have keyword "timestamp" within its name, but got "{attribute}"'
                )

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


# class Schema:
#     def __init__(self, **kwargs):
#         hints = get_type_hints(self.__class__)
#         for key, value in kwargs.items():
#             setattr(self, key, value)
#         for attribute in hints:
#             if not hasattr(self, attribute):
#                 setattr(self, attribute, None)
#         self.validate_types()

#     def __repr__(self):
#         return str(self.__dict__)
    
#     def __str__(self):
#         return str(self.__dict__)
    
#     def serialize(self):
#         for attr_name in dir(self):
#             if "_pointer" in attr_name:
#                 attr_value = getattr(self, attr_name)
#                 if hasattr(attr_value, "serialize"):

#                     setattr(self, attr_name, [attr_value.namespace, str(attr_value.key)])

#         # if hasattr(self, "timestamps"):
#         #     self.timestamps = self.timestamps.serialize()
#         #     for k, v in self.timestamps.items():
#         #         if type(v) != str:
#         #             raise ValueError("Timestamp must be str")

#         return self.__dict__
    
#     def validate_types(self):
#         hints = get_type_hints(self.__class__)
#         for attribute, expected_type in hints.items():
#             actual_value = getattr(self, attribute)
#             if expected_type is Pointer and "_pointer" not in attribute: #!= "pointers":
#                 raise SyntaxError(
#                     f"Type Pointer must have keyword '_pointer' within its name, but got '{attribute}'"
#                 )
#             if expected_type is Timestamp and not "timestamp" in attribute:
#                 raise SyntaxError(
#                     f'Type Timestamp has keyword "timestamps" within its name, but got "{attribute}"'
#                 )
            
#             origin = get_origin(expected_type)

#             if origin is Union:
#                 # Handle Union types (e.g., int | str)
#                 expected_types = get_args(expected_type)
#                 if not isinstance(actual_value, expected_types) and actual_value is not None:
#                     raise TypeError(
#                         f"Attribute '{attribute}' should be one of types {expected_types}, "
#                         f"but got '{type(actual_value).__name__}'"
#                     )

#             elif origin is Pointer:
#                 if not isinstance(actual_value, Pointer) and actual_value is not None:
#                     raise TypeError(
#                         f"Attribute '{attribute}' should be of type '{expected_type.__name__}', "
#                         f"but got '{type(actual_value).__name__}'"
#                     )
                
#             elif origin is Timestamp:
#                 if not isinstance(actual_value, Timestamp) and actual_value is not None:
#                     raise TypeError(
#                         f"Attribute '{attribute}' should be of type '{expected_type.__name__}', "
#                         f"but got '{type(actual_value).__name__}'"                        
#                     )

#             elif origin is None:
#                 if not isinstance(actual_value, expected_type) and actual_value is not None:
#                     raise TypeError(
#                         f"Attribute '{attribute}' should be of type '{expected_type.__name__}', "
#                         f"but got '{type(actual_value).__name__}'"
#                     )
#             else:
#                 if not isinstance(actual_value, origin) and actual_value is not None:
#                     raise TypeError(
#                         f"Attribute '{attribute}' should be of type '{expected_type}', "
#                         f"but got '{type(actual_value).__name__}'"
#                     )
