import re


FLOAT_REGEX = re.compile(r"""
(
    [-+]?       # + or minus sign
    [0-9]*      
    \.?         # floating point separator
    [0-9]+
)""", re.VERBOSE)


POSITIVE_FLOAT_REGEX = re.compile(r"([0-9]*\.?[0-9]+)", re.VERBOSE)


POSITIVE_FLOAT_LIST_REGEX = re.compile(r"""
(-0\.0)?                        # First float can be -0.0
( 
    ({POSITIVE_FLOAT}+)         # positive float
    \s                          # separated by a space
)* 
({POSITIVE_FLOAT}+)             # final positive float
""".format(POSITIVE_FLOAT=POSITIVE_FLOAT_REGEX.pattern), re.VERBOSE)


TIMESERIE_ENTRY_REGEX = re.compile(r"""
(?P<time>\d+)
(?P<sep>,)
(?P<float>[-+]?[0-9]*\.?[0-9]+)
""", re.VERBOSE)


TIMESERIES_REGEX = re.compile(r"""
(
    \d+,{float}     # digit,float for example: 60,-0.5
    \n
)*                  # multiple 'digit,float' split over newlines
(
    \d+,{float}
){{1}}              # last 'digit,float' has no newline.
""".format(float=FLOAT_REGEX.pattern), re.VERBOSE)
