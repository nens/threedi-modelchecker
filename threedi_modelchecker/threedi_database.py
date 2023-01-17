# backwards compatibility:
from threedi_schema import ThreediDatabase  # NOQA

import warnings


warnings.warn(
    "threedi_model_checker.threedi_database is pending deprecation. Please use the new "
    "threedi_schema instead.",
    UserWarning,
)
