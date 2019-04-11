from sqlalchemy.types import TypeDecorator, Integer


class IntegerEnum(TypeDecorator):
    """Column type for storing python enums.

    The IntegerEnum will make use of the backend INTEGER datatype to store
    the data. Data is converted back to a enum_type python object if possible.
    If not, the raw INTEGER is returned.
    """

    impl = Integer

    def __init__(self, enum_type):
        """

        :param enum_type: instance of enum.Enum
        """
        super(IntegerEnum, self).__init__()
        self.enum_type = enum_type

    def process_bind_param(self, value, dialect):
        if isinstance(value, self.enum_type):
            return value.value
        else:
            return value

    def process_result_value(self, value, dialect):
        if isinstance(value, self.enum_type):
            return self.enum_type(value)
        else:
            return value
