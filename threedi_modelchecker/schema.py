# backwards compatibility:
from threedi_schema import ModelSchema  # NOQA

import warnings


warnings.warn(
    "threedi_model_checker.schema is pending deprecation. Please use the new "
    "threedi_schema instead.",
    UserWarning,
)
