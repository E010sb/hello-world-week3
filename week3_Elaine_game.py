"""The Last Guest: an English-language terminal puzzle game.

Run: python week3_Elaine_game.py
Use --no-animation for an instant, motion-free playthrough.
"""

import argparse
from rich.markup import escape
import game_ui as ui

# Each dictionary describes one room. Item numbers are menu choices.
ROOMS = {
    "1": {
        "name": "The Forgotten Dining Room",
        "creature": "The Zombie",
        "color": "green",
        "scene": "Three plates wait beneath a blanket of dust. At the head of the "
        "table, a zombie rocks in a chair, covering its ears. An empty place "
        "beside it is set for one more guest.",
        "riddle": '"I have no hunger, yet something is missing. When I was small, '
        'she wound the night into a little wooden heart. Let it remember for me."',
        "items": {"1": "Rotten Apple", "2": "Carved Wooden Box", "3": "Rusty Knife"},
        "item_descriptions": {
            "1": "A dark apple on a child's plate. It smells of earth and rain.",
            "2": "A small wooden box with a winding key. Two initials mark the lid.",
            "3": "A blunt knife beside an untouched plate. Its handle bears a family crest.",
        },
        "answer": "2",
        "wrong": {
            "1": 'The zombie grips your wrist. "I said I was not hungry."',
            "3": 'The knife scrapes a plate. The zombie shrieks. "Not that sound!"',
        },
        "success": "You turn the little key. The wooden box opens: a music box. "
        "A fragile lullaby fills the room. The zombie whispers, 'Mother,' and "
        "closes its eyes. A seal marked REST slips from its hand.",
        "seal": "REST",
    },
    "2": {
        "name": "The Echoing Library",
        "creature": "The Bat",
        "color": "cyan",
        "scene": "Books lean like crooked teeth. A bat hangs above a desk, "
        "listening to the darkness. Its eyes are covered by an old curse.",
        "riddle": '"My paths are drawn in returning waves. Wake what sleeps '
        'inside the hollow metal, and I will find you in the dark."',
        "items": {"1": "Feather Quill", "2": "Old Map", "3": "Small Brass Bell"},
        "item_descriptions": {
            "1": "A split feather rests in an empty inkwell. Its tip is dry.",
            "2": "A faded plan of the castle. Every doorway has been crossed out.",
            "3": "A hollow brass cup with a handle. A loose metal tongue hangs inside.",
        },
        "answer": "3",
        "wrong": {
            "1": "The quill brushes the desk without a sound. Wings strike your face.",
            "2": 'You unfold the map. The bat hisses. "I cannot read your silence."',
        },
        "success": "You ring the bell. The bat follows its echo and lands on the "
        "desk. Beneath its folded wing lies a seal marked ECHO.",
        "seal": "ECHO",
    },
    "3": {
        "name": "The Moonlit Bedchamber",
        "creature": "The Werewolf",
        "color": "yellow",
        "scene": "Moonlight spills through a bare window. A werewolf trembles "
        "beside the bed, its claws digging into the floorboards.",
        "riddle": '"A pale watcher steals my name each night. Do not strike it. '
        'Do not give it another eye. Let darkness stand between us."',
        "items": {"1": "Heavy Curtain", "2": "Silver Mirror", "3": "Empty Candlestick"},
        "item_descriptions": {
            "1": "A folded length of thick velvet. Brass hooks line its upper edge.",
            "2": "A polished mirror. The moon appears twice when you lift it.",
            "3": "A tall brass stand with a cold, empty socket. There is no candle.",
        },
        "answer": "1",
        "wrong": {
            "2": "The mirror throws moonlight across the walls. The werewolf howls.",
            "3": "The empty candlestick casts no shadow large enough to hide the moon.",
        },
        "success": "You hang the heavy curtain over the window. The howling stops. "
        "A trembling human hand offers you a seal marked SHADE.",
        "seal": "SHADE",
    },
}

# Room IDs define a fixed route, not player navigation choices.
ROOM_ORDER = ["1", "2", "3"]


def new_game(name):
    """Create fresh state for each playthrough; replay never keeps old progress."""
    return {
        "name": name,
        "courage": 3,
        "completed": [],
        "has_key": False,
        "key_inspected": False,
        "ending": None,
    }


def status(state):
    if not state["has_key"]:
        key = "Not found"
    elif state["key_inspected"]:
        key = "Silver key"
    else:
        key = "Unexamined key"
    text = (
        f"Guest: {escape(state['name'])}    Courage: {state['courage']}/3\n"
        f"Seals: {len(state['completed'])}/3    Key: {key}"
    )
    ui.panel(text, "YOUR STATUS", "magenta")


def rules():
    ui.panel(
        "Help all three guardians to collect their seals and receive a key.\n"
        "Follow the fixed route: Dining Room > Library > Bedchamber.\n"
        "Solve each room to move automatically to the next. You cannot go back.\n"
        "Read the riddle and object descriptions, then choose an object to use.\n"
        "Each wrong object costs 1 courage. At 0 courage, the game ends.\n"
        "Wrong objects keep you in the current room. Invalid input costs nothing.\n"
        "Objects stay in their rooms. Each room awards one seal.\n"
        "After the third room, you may inspect the key before going upstairs.\n"
        + ui.control_hint(),
        "HOW TO PLAY", "magenta",
    )


def visit_room(state, number, animate):
    room = ROOMS[number]
    ui.transition("A door creaks open...", animate)
    ui.heading(f"FIRST FLOOR / ROOM {number} OF 3")
    ui.portrait(room)
    ui.panel(room["scene"], room["name"], room["color"])

    while state["courage"] > 0:
        status(state)
        ui.panel(room["riddle"], room["creature"], room["color"])
        ui.objects(room)
        labels = room["items"].copy()
        labels["0"] = "Leave the game"
        choice = ui.choose("Which object will you use?", ["1", "2", "3", "0"], labels)
        if choice == "0":
            if ui.confirm("Quit this playthrough? Progress will not be saved"):
                state["ending"] = "quit"
                return
            continue
        if choice == room["answer"]:
            if number not in state["completed"]:
                state["completed"].append(number)
            ui.panel(room["success"], "GUARDIAN AT PEACE", "green")
            ui.text(f"Seal acquired: {room['seal']} ({len(state['completed'])}/3)", "bold green")
            return
        else:
            state["courage"] -= 1
            ui.text(room["wrong"][choice], "red")
            ui.text(f"WRONG OBJECT - Courage: {state['courage']}/3", "bold red")
    state["ending"] = "courage"


def award_key(state, animate):
    if len(state["completed"]) == 3 and not state["has_key"]:
        ui.transition("The three seals begin to tremble...", animate)
        state["has_key"] = True
        ui.panel(
            "REST. ECHO. SHADE.\n\nThe three seals dissolve into a single cold key. "
            "In the candlelight, its surface glows faintly gold.\n\n"
            "There is writing beneath the dust. You may want to inspect it.",
            "THE KEY APPEARS", "yellow",
        )
        ui.panel(
            "A final passage brings you back to the iron gate.\n"
            "As the key approaches, a hidden inscription appears:\n\n"
            '"The keeper asks only once. Speak what is true, not what the candle shows."\n\n'
            "Below it, another hand has scratched a warning:\n"
            '"Answer falsely, and the house may claim you. Answer truly, and he must let you pass."',
            "AT THE FOOT OF THE STAIRS", "magenta",
        )


def inspect_key(state):
    if not state["has_key"]:
        ui.text("You have no key yet. Help the three guardians first.", "yellow")
        return
    state["key_inspected"] = True
    ui.panel(
        "You turn away from the candle and rub away the dust.\n"
        "The metal is silver. The golden glow was only reflected candlelight.\n\n"
        'A single word is engraved on the bow: SILVER.\n'
        'Below it: "Know what you carry. The house listens."',
        "KEY INSPECTED / SILVER", "bright_white",
    )


def upstairs(state, animate):
    if not state["has_key"]:
        remaining = 3 - len(state["completed"])
        ui.text(f"The iron gate is locked. You still need {remaining} seal(s).", "yellow")
        return
    ui.text("The key unlocks the iron gate. You climb the staircase.", "magenta")
    ui.transition("The stairs groan beneath your feet...", animate)
    ui.heading("SECOND FLOOR / THE BUTLER")
    ui.portrait({"creature": "The Vampire Butler", "color": "red"})
    ui.panel(
        "At the top of the stairs, a pale butler stands perfectly still.\n"
        "Behind him, an open balcony leads to an outside stairway.\n"
        "A guest book lies open at his elbow. Every line is filled except the last.\n\n"
        f'"Good evening, {escape(state["name"])}."\n\n'
        "His eyes move from your face to the key. For the first time, his smile fades.",
        "THE VAMPIRE BUTLER", "red",
    )
    ui.transition("For a moment, even the rain falls silent.", animate)
    ui.panel(
        '"One last question."\n\n'
        '"Is the key you found gold, or silver?"',
        "THE KEEPER'S QUESTION", "red",
    )
    ui.key_choices()
    if not ui.charm:
        ui.text("1. Gold\n2. Silver")
    answer = ui.choose("Your answer", ["1", "2"], {"1": "Gold", "2": "Silver"})
    if answer == "1":
        state["ending"] = "gold"
    else:
        state["ending"] = "silver"


def show_ending(state):
    if state["ending"] == "silver":
        text = ('The empty line in the guest book stays blank. The butler tries '
                'to reach for you, but his hand stops at the edge of the light.\n\n'
                '"You are lucky."\n\nBound by your truthful answer, he steps aside. '
                'You cross the balcony and '
                'descend the outside stairs into the rain.\n'
                'Behind you, the castle windows go dark.\n\nYOU ESCAPED.')
        title, color = "ENDING / THE SILVER DAWN", "green"
    elif state["ending"] == "gold":
        text = ('Ink crawls across the final line of the guest book, spelling your name. '
                'Your false answer has made you a guest. The house will not let you leave.\n\n'
                'The butler smiles. His teeth are far too sharp.\n\n'
                '"At last. I have been waiting for you."\n\n'
                'Before you can lift the key, he sinks his fangs into your neck.\n'
                'The candle goes out.\n\nGAME OVER.')
        title, color = "ENDING / THE EXPECTED GUEST", "red"
    elif state["ending"] == "courage":
        text = ("Your courage is gone. The corridor stretches into darkness.\n"
                "Your knees give way. Somewhere upstairs, a dinner bell rings.\n\nGAME OVER.")
        title, color = "ENDING / LOST TO THE HOUSE", "red"
    else:
        ui.text("You close this chapter. Your progress has not been saved.", "dim")
        return
    ui.panel(text, title, color)


def play(animate=True):
    ui.cover()
    name = ui.name()
    state = new_game(name)
    ui.panel(
        "You enter an old castle to escape a violent storm.\n"
        "The entrance door slams shut. It has no handle on this side.\n\n"
        "An iron gate blocks the staircase. Only the dining room door is open.\n"
        "Beyond it, a narrow passage leads deeper into the first floor.\n"
        'Carved into the gate: "Give peace to the three who keep watch, '
        'and the way above shall open."',
        "MIDNIGHT", "magenta",
    )
    rules()

    # Only solving the current room opens the next room in the fixed sequence.
    for number in ROOM_ORDER:
        visit_room(state, number, animate)
        if state["ending"] is not None:
            break
        if number != ROOM_ORDER[-1]:
            ui.transition("A hidden door opens. The passage draws you into the next room...", animate)

    if state["ending"] is None:
        award_key(state, animate)
        status(state)
        if ui.confirm("Inspect the key before going upstairs?", default=True):
            inspect_key(state)
        upstairs(state, animate)

    show_ending(state)
    return state


def main():
    parser = argparse.ArgumentParser(description="The Last Guest - a terminal puzzle game")
    parser.add_argument("--no-animation", action="store_true", help="Skip all transition delays")
    args = parser.parse_args()
    ui.setup()
    run(animate=not args.no_animation)


def run(animate=True):
    """Play again with a fresh state, or exit safely when input is cancelled."""
    try:
        while True:
            state = play(animate)
            if state["ending"] == "quit":
                break
            if not ui.confirm("Play again?"):
                break
    except (KeyboardInterrupt, EOFError):
        ui.text("\nThe story pauses here. No progress was saved.", "dim")


if __name__ == "__main__":
    main()
