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
