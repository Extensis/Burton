import chardet

def detect_encoding(file):
    """This function attempts to detect the character encoding of a file."""
    encoding = None

    bom = file.read(4)

    encoding = {
        
        b'\x00\x00\xfe\xff' : "utf_32", #BE
        b'\xff\xfe\x00\x00' : "utf_32", #LE
    }.get(bom, None)

    if encoding is not None:
        return encoding

    bom = bom[:3]
    file.seek(3)
    encoding = {
        b'\xef\xbb\xbf' : "utf_8",
    }.get(bom, None)

    if encoding is not None:
        return encoding

    bom = bom[:2]
    file.seek(2)
    encoding = {
        b'\xfe\xff' : "utf_16", #BE
        b'\xff\xfe' : "utf_16", #LE
    }.get(bom, None)

    if encoding is not None:
        return encoding

    file.seek(0)
    encoding = 'ascii'

    try:
        encoding = chardet.detect(file.read())["encoding"]
    except Exception as e:
        encoding = "iso-8859-1"

    file.seek(0)
    return encoding

def filter_string(string):
    string = string.replace("\\r", "\\\\r").replace("\\n", "\\\\n")
    string = string.replace("\r", "\\\\r").replace("\n", "\\\\n")
    string = string.encode('utf-8').decode('unicode-escape')
    return string

def replace_params(raw_string):
    """This function replaces format placeholders with incrementing numbers
    surrounded with curly quotes. It replaces both printf placeholders
    (e.g. "%d" "%s") and Windows placeholders (e.g. "{0}", "{1}"). The
    replacements are very similar to Windows placeholders, but ordered so that
    the first paramater in the string is always "{0}", the next is "{1}", etc.
    Because of this, it is possible that the replaced string will be identical
    to the original string
    """
    printf_flags         = "-+#1234567890"
    printf_width         = "1234567890*"
    printf_precision_sep = "."
    printf_precision     = printf_width
    printf_length        = "hlL"
    printf_specifiers    = "cdieEfgGosuxXpn%@"
    digits               = "1234657890"

    output_string       = ""
    replaced_strings    = []
    num_replacements    = 0
    current_token       = ""
    in_printf           = False
    in_percent_escape   = False
    in_printf_flags     = False
    in_printf_width     = False
    in_printf_precision = False
    in_printf_length    = False
    in_printf_specifier = False
    in_num_param        = False

    for c in raw_string:
        current_token = current_token + c
        if in_printf:
            if c == "%" and current_token[-1] == "%":
                in_printf           = False
                in_percent_escape   = True
                in_printf_flags     = False
                in_printf_width     = False
                in_printf_precision = False
                in_printf_length    = False
                in_printf_specifier = False
                in_num_param        = False

            if in_printf_flags:
                if c not in printf_flags:
                    in_printf_flags = False
                    in_printf_width = True

            if in_printf_width:
                if c == printf_precision_sep:
                    in_printf_width = False
                    in_printf_precision = True
                elif c not in printf_width:
                    in_printf_width = False
                    in_printf_length = True

            if in_printf_precision:
                if c != printf_precision_sep and c not in printf_precision:
                    in_printf_precision = False
                    in_printf_length = True

            if in_printf_length:
                if c not in printf_length:
                    in_printf_length = False
                    in_printf_specifier = True

            if in_printf_specifier:
                in_printf = False
                if c in printf_specifiers:
                    replaced_strings.append(current_token)
                    output_string += "{" + str(num_replacements) + "}"
                    num_replacements += 1
                    current_token = ""
                else:
                    output_string += current_token[:-1]
                    current_token = c

                in_printf           = False
                in_printf_flags     = False
                in_printf_width     = False
                in_printf_precision = False
                in_printf_length    = False
                in_printf_specifier = False

        elif in_num_param:
            if c == "}":
                in_num_param = False
                replaced_strings.append(current_token)
                output_string += "{" + str(num_replacements) + "}"
                num_replacements += 1
                current_token = ""
            elif c not in digits:
                in_num_param = False
                output_string += current_token
                current_token = ""

        if not in_printf and not in_num_param and not in_percent_escape:
            if c == "%":
                in_printf           = True
                in_printf_flags     = True
                in_printf_width     = False
                in_printf_precision = False
                in_printf_length    = False
                in_printf_specifier = False

                output_string += current_token[:-1]
                current_token = c
            elif c == "{":
                in_num_param = True
            else:
                output_string += current_token
                current_token = ""

        in_percent_escape = False

    output_string += current_token
    return output_string, replaced_strings

def restore_platform_specific_params(string, replaced_strings):
    """This function reverses the replace_params function. Pass the return
    values from replace_params to this function to get the original string back.
    """
    opening_tag = "<burton_param>"
    closing_tag = "</burton_param>"
    string = string.replace("{", opening_tag)
    string = string.replace("}", closing_tag)

    for index in range(0, len(replaced_strings)):
        string = string.replace(
            opening_tag + str(index) + closing_tag,
            replaced_strings[index]
        )

    string = string.replace(opening_tag, "{")
    string = string.replace(closing_tag, "}")

    return string
