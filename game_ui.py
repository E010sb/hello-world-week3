"""Display and input helpers; game rules stay in game.py.

Rich is the default. setup(use_charm=True) enables optional Gum decoration.
All helpers are ordinary functions, with no custom classes or function swapping.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text


ROOT = Path(__file__).resolve().parent
LOCAL_GUM = ROOT / ".tools" / "gum_2.0.2_Darwin_arm64" / "gum"
GOLD = "#C1A574"
INK = "#101116"
PAPER = "#E8E2D4"
MUTED = "#A49DAA"
COLORS = {
    "magenta": GOLD, "green": "#99B49A", "cyan": "#91B6C8",
    "yellow": GOLD, "red": "#D17883", "bright_white": PAPER,
}
PORTRAIT_FILES = {
    "The Zombie": "zombie-face-v2.json",
    "The Bat": "bat-face-v2.json",
    "The Werewolf": "werewolf-face-v2.json",
    "The Vampire Butler": "vampire-face-v1.json",
}
CASTLE = r"""
            /\
           /  \
    /\    | ++ |    /\
   /  \___|    |___/  \
  | [] |  |    |  | [] |
  |    |[]| /\ |[]|    |
  |____|__|/  \|__|____|
"""

# These are display settings, not player progress. setup() resets them.
charm = False
preview = False
width = 80
gum_path = ""
gum_env = {}
recorded = []
portraits = {}
keys = {}
console = Console(highlight=False)


def setup(use_charm=False, save_preview=False):
    global charm, preview, width, gum_path, gum_env, console
    charm = use_charm
    preview = save_preview
    recorded.clear()
    portraits.clear()
    keys.clear()
    console = Console(highlight=False)
    if not charm:
        return
    gum_path = shutil.which("gum")
    if LOCAL_GUM.exists():
        gum_path = str(LOCAL_GUM)
    if not gum_path:
        raise RuntimeError("Charm Gum was not found. See README.md or run python game.py.")
    width = shutil.get_terminal_size((80, 24)).columns - 4
    width = max(24, min(80, width))
    gum_env = os.environ.copy()
    gum_env.pop("NO_COLOR", None)
    gum_env["CLICOLOR_FORCE"] = "1"
    gum_env["COLORTERM"] = "truecolor"
    if not gum_env.get("TERM"):
        gum_env["TERM"] = "xterm-256color"
    console = Console(highlight=False, force_terminal=True,
                      color_system="truecolor", width=width + 2)
    for creature, filename in PORTRAIT_FILES.items():
        portraits[creature] = json.loads((ROOT / "assets" / filename).read_text())
    keys.update(json.loads((ROOT / "assets" / "keys.json").read_text()))


def gum(arguments, interactive=False):
    """Run one Gum component; Escape cancels instead of choosing an answer."""
    input_stream = subprocess.DEVNULL
    error_stream = subprocess.PIPE
    if interactive:
        input_stream = None
        error_stream = None
    result = subprocess.run(
        [gum_path] + arguments, stdin=input_stream, stderr=error_stream,
        stdout=subprocess.PIPE, text=True, env=gum_env,
    )
    if result.returncode != 0:
        if interactive and result.returncode in (1, 130, -2):
            raise KeyboardInterrupt
        raise RuntimeError("Charm could not draw the interface: " + str(result.stderr))
    return result.stdout.rstrip("\n")


def emit(value):
    if preview:
        recorded.append(value + "\n")
    else:
        print(value, flush=True)


def text(message, style="", markup=True):
    if preview:
        with console.capture() as captured:
            console.print(message, style=style, markup=markup)
        emit(captured.get())
    else:
        console.print(message, style=style, markup=markup)


def card(body, title="", color=GOLD, align="left", border="rounded", monochrome=False):
    if title:
        body = title + "\n\n" + body
    output = gum([
        "style", "--trim=false", "--foreground", PAPER, "--background", INK,
        "--border", border, "--border-foreground", color,
        "--padding", "1 2", "--margin", "0 1", "--width", str(width),
        "--align", align, "--", body,
    ])
    if monochrome:
        # Artwork uses the terminal's default text, with no color codes at all.
        output = Text.from_ansi(output).plain
    emit(output)


def panel(body, title="", color="magenta"):
    if charm:
        body = Text.from_markup(body).plain
        card(body, title, COLORS.get(color, GOLD))
    else:
        console.print(Panel(body, title=title, border_style=color))


def heading(title):
    if charm:
        emit(gum(["style", "--foreground", GOLD, "--bold", "--padding", "1 2",
                  "--width", str(width), "--", title]))
    else:
        console.rule(title, style="magenta")


def cover():
    if not charm:
        panel("[bold magenta]THE LAST GUEST[/]\nA Haunted Castle Adventure\n\n"
              "Three restless guardians. One locked staircase. One final question.")
        return
    art = CASTLE
    if width < 44:
        art = "      /\\\n  ___/  \\___\n |  THE KEEP  |\n |____/\\____|"
    lines = []
    for line in art.strip("\n").splitlines():
        lines.append(line.strip())
    card("\n".join(lines) + "\n\nT H E   L A S T   G U E S T\n\n"
         "A HAUNTED CASTLE ADVENTURE\n"
         "Three restless guardians. One final question.\n\n"
         "MIDNIGHT  /  CHARM EDITION", align="center", border="double", monochrome=True)


def control_hint():
    if charm:
        return "Use Up/Down to choose and Enter to confirm. Esc or Ctrl+C exits."
    return "Type a menu number and press Enter. Ctrl+C exits at any time."


def choose(prompt, choices, labels=None):
    if not charm:
        return Prompt.ask(prompt, choices=choices, console=console)
    options = []
    for choice in choices:
        if labels is None:
            options.append(choice)
        else:
            options.append(labels[choice])
    selected = gum([
        "choose", "--header", prompt, "--height", str(len(options)),
        "--cursor", "› ", "--padding", "1 3", "--header.foreground", GOLD,
        "--cursor.foreground", INK, "--cursor.background", GOLD,
        "--item.foreground", PAPER, "--selected.foreground", INK,
        "--selected.background", GOLD, "--",
    ] + options, interactive=True)
    if selected not in options:
        raise KeyboardInterrupt
    text("  You chose: " + selected, MUTED, markup=False)
    return choices[options.index(selected)]


def name():
    if charm:
        answer = gum([
            "input", "--header", "The guest book is open. What is your name?",
            "--placeholder", "Traveler", "--prompt", "  Name › ",
            "--char-limit", "32", "--width", str(max(16, width - 8)),
            "--padding", "1 2", "--header.foreground", GOLD,
            "--prompt.foreground", GOLD, "--cursor.foreground", GOLD,
        ], interactive=True)
    else:
        answer = Prompt.ask("What is your name?", default="Traveler", console=console)
    clean_name = ""
    for character in answer.strip():
        if character.isprintable():
            clean_name += character
    if clean_name == "":
        clean_name = "Traveler"
    return clean_name


def confirm(prompt, default=False):
    if not charm:
        return Confirm.ask(prompt, default=default, console=console)
    options = ["no", "yes"]
    if default:
        options = ["yes", "no"]
    answer = choose(prompt, options, {"yes": "Yes", "no": "No"})
    return answer == "yes"


def transition(message, animate):
    if not animate:
        text(message, "dim")
    elif charm:
        gum(["spin", "--spinner", "pulse", "--title", message,
             "--spinner.foreground", GOLD, "--title.foreground", PAPER,
             "--padding", "1 3", "--", sys.executable, "-c",
             "import time; time.sleep(0.7)"], interactive=True)
    elif console.is_terminal:
        with console.status(message, spinner="dots", spinner_style="magenta"):
            time.sleep(0.8)
    else:
        text(message, "dim")


def objects(room):
    details = []
    for number, item in room["items"].items():
        description = room["item_descriptions"][number]
        if charm:
            details.append(item + "\n" + description)
        else:
            text(f"  [bold]{number}. {item}[/]")
            text("     " + description, "dim")
    if charm:
        card("\n\n".join(details), "OBJECTS IN THE ROOM", COLORS[room["color"]])
    else:
        text("  0. Quit the game")


def art_width(lines):
    longest = 0
    for line in lines:
        longest = max(longest, len(line))
    return longest


def plain_art(lines, available):
    """Center the original letters and digits without adding any colors."""
    left = " " * max(0, (available - art_width(lines)) // 2)
    rows = []
    for line in lines:
        rows.append(left + line)
    return rows


def portrait(room):
    if not charm:
        return
    art = portraits[room["creature"]]
    available = width - 6
    lines = art["full"]
    if art_width(lines) > available:
        lines = art["compact"]
    rows = plain_art(lines, available)
    card("\n".join(rows), room["creature"].upper(), monochrome=True)


def key_choices():
    if not charm:
        return
    available = width - 6
    columns = art_width(keys["full"])
    gap = " " * 6
    rows = []
    if available >= columns * 2 + len(gap):
        lines = []
        for line in keys["full"]:
            lines.append(line.ljust(columns))
        picture = plain_art(lines, columns)
        left = " " * ((available - columns * 2 - len(gap)) // 2)
        for index in range(len(lines)):
            rows.append(left + picture[index] + gap + picture[index])
        rows.append("")
        rows.append(left + "GOLD".center(columns) + gap + "SILVER".center(columns))
    else:
        for metal in ["gold", "silver"]:
            art = keys[metal]
            rows.extend(plain_art(keys["compact"], available))
            rows.append(art["label"].center(available))
            rows.append("")
    card("\n".join(rows), "GOLD OR SILVER?", monochrome=True)
