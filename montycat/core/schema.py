from typing import get_origin, get_args, get_type_hints, Union
from timestamp import Timestamp

class Pointer:
    """
    A class that represents a reference to another entity, often used for 
    creating relationships between data objects in a schema. A `Pointer` holds 
    a reference to a store namespace and its associated value. This is useful 
    when dealing with schema-based models where entities point to other entities 
    or collections.

    Attributes:
        namespace (str): The namespace for the store this pointer refers to.
        value (str): The value associated with this pointer.

    Methods:
        __str__: Returns a string representation of the pointer.
        serialize: Returns a serialized dictionary representation of the pointer.
    """
    def __init__(self, **kwargs):
        """
        Initializes a `Pointer` object with keyword arguments. Each keyword 
        argument is expected to be a tuple containing the store namespace and 
        the associated value.

        Args:
            kwargs (dict): Keyword arguments where keys are attribute names 
                           and values are tuples containing a store namespace 
                           and a value.

        Example:
            pointers = Pointer(field1=("namespace1", "value1"), field2=("namespace2", "value2"))
        """
        # Should enforce word pointers
        for key, value in kwargs.items():
            # Each pointer is initialized with a store namespace and a value
            setattr(self, key, [value[0].namespace, value[1]])

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
    """
    A base class for defining data schemas, where the schema class will 
    automatically validate types based on type hints, handle default values, 
    and ensure the integrity of data passed into the schema. It is commonly used 
    for data validation and structuring in complex data models.

    Attributes:
        dynamic attributes based on keyword arguments: The schema can accept 
        any number of fields as keyword arguments. These fields will be validated 
        based on their type hints.

    Methods:
        __repr__: Provides a string representation of the schema, showing all 
                  its attributes.
        __str__: Provides a human-readable string representation of the schema.
        serialize: Serializes the schema object, including pointers, into a 
                  dictionary format.
        validate_types: Ensures that the attributes of the schema adhere to 
                        their expected types based on type hints.
    """
    def __init__(self, **kwargs):
        """
        Initializes a `Schema` object with keyword arguments. The attributes 
        of the schema are dynamically set based on the provided `kwargs`. It also 
        validates that the schema’s attributes conform to the expected types 
        defined by type hints.

        Args:
            kwargs (dict): Keyword arguments where keys are attribute names 
                           and values are the attribute values.

        Example:
            schema = Schema(field1="value1", field2=2)
        """
        # Fetch type hints for the schema class
        hints = get_type_hints(self.__class__)

        for key, value in kwargs.items():
            # Dynamically set the attribute value
            setattr(self, key, value)

        # Set default values for attributes not provided in kwargs
        for attribute in hints:
            if not hasattr(self, attribute):
                setattr(self, attribute, None)

        # Validate the types of the attributes
        self.validate_types()

    def __repr__(self):
        """
        Returns a string representation of the `Schema` object, including all 
        attributes and their values.

        Returns:
            str: String representation of the `Schema` object.
        """
        return str(self.__dict__)
    
    def __str__(self):
        """
        Returns a human-readable string representation of the `Schema` object, 
        displaying the attributes and their corresponding values.

        Returns:
            str: Human-readable string representation of the `Schema`.
        """
        return str(self.__dict__)
    
    def serialize(self):
        """
        Serializes the `Schema` object, including any `Pointer` attributes, 
        into a dictionary format. If the schema contains any pointers, those 
        pointers will be serialized accordingly, converting them to dictionaries 
        and ensuring that values are correctly formatted.

        Returns:
            dict: A dictionary representation of the schema, ready for storage 
                  or transmission.
        """
        if hasattr(self, "pointers"):
            # Serialize any pointers and format their values
            self.pointers = self.pointers.serialize()
            for k, v in self.pointers.items():
                if v[1].isdigit():
                    self.pointers[k] = [v[0].namespace, str(v[1])]

        # if hasattr(self, "timestamps"):
        #     self.timestamps = self.timestamps.serialize()
        #     for k, v in self.timestamps.items():
        #         if type(v) != str:
        #             raise ValueError("Timestamp must be str")

        return self.__dict__
    
    def validate_types(self):
        """
        Validates the types of the attributes of the schema, ensuring that 
        the types match the expected types based on the type hints. If an 
        attribute does not conform to the expected type, a `TypeError` is raised.

        This method checks for `Union` types, `Pointer` types, and other basic 
        types, allowing for flexible schema definitions.

        Raises:
            TypeError: If any attribute does not match its expected type.
        """
        # Fetch type hints for the schema class
        hints = get_type_hints(self.__class__)

        for attribute, expected_type in hints.items():
            actual_value = getattr(self, attribute)

            print(actual_value, expected_type, attribute)

            if expected_type is Pointer and attribute != "pointers":
                raise SyntaxError(
                    f'Type Pointer has to relate to "pointers", but got "{attribute}"'
                )
            
            if expected_type is Timestamp and not "timestamp" in attribute:
                raise SyntaxError(
                    f'Type Timestamp has keyword "timestamps" within its name, but got "{attribute}"'
                )
            
            # Get the origin of the expected type (i.e., the base class for unions)
            origin = get_origin(expected_type)

            if origin is Union:
                # Handle Union types (e.g., int | str)
                expected_types = get_args(expected_type)
                if not isinstance(actual_value, expected_types) and actual_value is not None:
                    raise TypeError(
                        f"Attribute '{attribute}' should be one of types {expected_types}, "
                        f"but got '{type(actual_value).__name__}'"
                    )

            elif origin is Pointer:
                # Handle Pointer types

                if not isinstance(actual_value, Pointer) and actual_value is not None:
                    raise TypeError(
                        f"Attribute '{attribute}' should be of type '{expected_type.__name__}', "
                        f"but got '{type(actual_value).__name__}'"
                    )
                
            elif origin is Timestamp:
                # Handle Timestamp
                if not isinstance(actual_value, Timestamp) and actual_value is not None:
                    raise TypeError(
                        f"Attribute '{attribute}' should be of type '{expected_type.__name__}', "
                        f"but got '{type(actual_value).__name__}'"                        
                    )

            elif origin is None:
                # Handle normal types (e.g., int, str)
                if not isinstance(actual_value, expected_type) and actual_value is not None:
                    raise TypeError(
                        f"Attribute '{attribute}' should be of type '{expected_type.__name__}', "
                        f"but got '{type(actual_value).__name__}'"
                    )
            else:
                # Handle any other types
                if not isinstance(actual_value, origin) and actual_value is not None:
                    raise TypeError(
                        f"Attribute '{attribute}' should be of type '{expected_type}', "
                        f"but got '{type(actual_value).__name__}'"
                    )
