class MigrationMissingError(Exception):
    """Raised when 3Di model is missing migrations."""

    pass


class MigrationTooHighError(Exception):
    """Raised when 3Di model has applied more migrations than expected."""

    pass
