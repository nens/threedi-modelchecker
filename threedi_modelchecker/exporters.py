def print_errors(errors):
    """Simply prints all errors to stdout

    :param errors: iterator of BaseModelError
    """
    for error in errors:
        print(error)


def export_to_file(errors, file):
    """Write errors to a new file, separated with newlines.

    File cannot be an already existing file.

    :param errors: iterator of BaseModelError
    :param file:
    :return: None
    :raise FileExistsError: if the file already exists
    """
    with open(file, 'x') as f:
        for error in errors:
            f.write(error)


def summary(errors):
    """Produces an summary of the found errors

    :param errors: iterator of BaseModelError
    :return: dict
    """
    pass
