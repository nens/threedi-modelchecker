import re


TIMESERIE_ENTRY_REGEX = re.compile(
    r"""
(\d+)                                # int
\s*,\s*                              # comma-separated (allow whitespace)
[+-]?([\d]+([.][\d]*)?|[.][\d]+)     # float (.5, 5.2, -14.)
""",
    re.VERBOSE,
)

TIMESERIES_REGEX = re.compile(
    r"""\s*
(
    {timeserie_entry}       # digit,float; for example: 60,-0.5
    \s+                     # separated by one or more whitespace characters
)*
(
    {timeserie_entry}       # last entry does not have a newline.
){{1}}\s*                   # allow whitespace after
""".format(
        timeserie_entry=TIMESERIE_ENTRY_REGEX.pattern
    ),
    re.VERBOSE,
)
