import re


FLOAT = re.compile(r"([-+]?[0-9]*\.?[0-9]+)", re.VERBOSE)
POSITIVE_FLOAT = re.compile(r"([0-9]*\.?[0-9]+)", re.VERBOSE)

POSITIVE_FLOAT_LIST = re.compile(r"""
[-0\.0]?                        # First float can be -0.0
( 
    ({POSITIVE_FLOAT}+)         # positive floats 
    \s                          # separated by a space
)* 
({POSITIVE_FLOAT}+)             # final positive float
""".format(POSITIVE_FLOAT=POSITIVE_FLOAT.pattern), re.VERBOSE)

SINGLE_TIMESERIES_ENTRY = re.compile("""
(?P<time>\d+)
(?P<sep>,)
(?P<float>[-+]?[0-9]*\.?[0-9]+)
""", re.VERBOSE)

TIMESERIES = re.compile(r"""
(
    \d+,{float}     # digit,float for example: 60,-0.5
    \n
)*                  # multiple 'digit,float' split over newlines
(
    \d+,{float}
)+                  # last 'digit,float' has no newline.
""".format(float=FLOAT.pattern), re.VERBOSE)
