import re


def column_number_to_name(n):
    """Number to column name, e.g., 1 = A, 26 = Z, 27 = AA, 703 = AAA."""
    name = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        name = chr(r + ord("A")) + name
    return name


def column_name_to_number(name):
    """Excel-style column name to number, e.g., A = 1, Z = 26, AA = 27, AAA = 703."""
    n = 0
    for c in name.upper():
        n = n * 26 + 1 + ord(c) - ord("A")
    return n


def address_to_coordinates(address):
    if match := re.match(r"([a-z]+)(\d+)", address.lower()):
        column_name = match.group(1)
        row = int(match.group(2))
        return row, column_name_to_number(column_name)


def generate_blank_values(num_rows, num_columns):
    return [["" for col in range(num_columns)] for row in range(num_rows)]
