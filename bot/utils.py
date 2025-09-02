import re

def escape_markdown_v2(text: str) -> str:
    """
    Escapes characters for Telegram's MarkdownV2 parse mode.

    Args:
        text: The input string.

    Returns:
        The escaped string.
    """
    # In MarkdownV2, characters _, *, [, ], (, ), ~, `, >, #, +, -, =, |, {, }, ., ! must be escaped.
    escape_chars = r"[_*\[\]()~`>#+\-=|{}.!]"
    return re.sub(escape_chars, r"\\\g<0>", text)
