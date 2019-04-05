class BaseModelError(object):
    """Dataclass to store error information of a model

    Base class to group all model errors"""

    def __init__(self, instance, column, **kwargs):
        self.instance = instance
        self.column = column
        self.id = getattr(self.instance, 'id')

    def __str__(self):
        return "Unexpected value '%s' in column '%s' for id %s" % (
            getattr(self.instance, self.column.name),
            self.column,
            self.id
        )


class MissingForeignKeyError(BaseModelError):

    def __init__(self, ref_column, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ref_column = ref_column

    def __str__(self):
        return "Missing foreign key in column %s for id %s, expected " \
               "reference to %s" % (
                   self.column,
                   self.id,
                   self.ref_column
               )


class NullColumnError(BaseModelError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return "Unexpected null value in column '%s' for id %s" % (
            self.column,
            self.id)


class InvalidTypeError(BaseModelError):
    def __init__(self, expected_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expected_type = expected_type

    def __str__(self):
        return "Invalid type in column '%s' for id %s, expected type '%s'" % (
                   self.column,
                   self.id,
                   self.expected_type,
               )


class NotUniqueError(BaseModelError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def yield_model_errors(klass, instances, column, **kwargs):
    """Helper function to instantiate ModelError with data

    :param klass:
    :param instances:
    :param column:
    :param kwargs:
    :return:
    """
    for instance in instances:
        yield klass(instance=instance, column=column, **kwargs)
