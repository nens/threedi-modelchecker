# Backwards compatibility
from threedi_schema import constants  # NOQA
from threedi_schema import custom_types  # NOQA
from threedi_schema import models  # NOQA

import warnings


warnings.warn(
    "threedi_model_checker.threedi_model is pending deprecation. Please use the new "
    "threedi_schema instead.",
    UserWarning,
)
