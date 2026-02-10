import re


def parse_name(name_string):
    """
    Parse name string and return (first_name, last_name).
    Handles both 'First Last' and 'Last, First' formats.
    """
    name_string = name_string.strip()

    # Check if format is "Last, First"
    if ',' in name_string:
        parts = name_string.split(',', 1)
        if len(parts) == 2:
            last_name = parts[0].strip()
            first_name = parts[1].strip()
            return first_name, last_name

    # Default to "First Last" format
    parts = name_string.split()
    if len(parts) >= 2:
        first_name = parts[0]
        last_name = ' '.join(parts[1:])  # Handle multi-word last names
        return first_name, last_name
    elif len(parts) == 1:
        return parts[0], ''

    return '', ''
