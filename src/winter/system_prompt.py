# date gives us today's date: a value OUR code supplies, never text from outside.
from datetime import date

# files() finds a data file that ships inside a Python package, wherever the program
# is started from (a plain relative path would break when the working folder changes).
from importlib.resources import files

# Template fills "$blank" markers using only the values we hand it (see _render below).
from string import Template

# The prompt file inside the winter/prompts folder.
_SYSTEM_PROMPT_FILE = "system.txt"


def _render(template_text: str, today: date) -> str:
    """Fill the blanks in a prompt template with the values we supply.

    substitute() is strict on purpose: a blank we did not supply raises KeyError, and a
    stray "$" raises ValueError. Both mean the FILE is wrong, and we want to know at once,
    not send the model a half-filled prompt.
    """
    # The ONLY blank today is $date. Add new keyword values here when the file needs more.
    return Template(template_text).substitute(date=today.isoformat())


def load_system_prompt(today: date | None = None) -> str:
    """Read the system prompt file and fill in its blanks.

    Trust rule (ADR 0012): the only parameter is a date. There is deliberately no way to
    pass free text in, so conversation text, web pages and model output can never reach
    the template. Conversation text always travels as separate messages.
    """
    # Read the file that ships inside the winter package (UTF-8 so any character is safe).
    text = files("winter").joinpath("prompts", _SYSTEM_PROMPT_FILE).read_text(encoding="utf-8")
    # Use the real date unless a test supplies a fixed one.
    when = today if today is not None else date.today()
    # Fill the blanks and drop leading or trailing blank lines.
    return _render(text, when).strip()
