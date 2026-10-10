"""Each line's expressions, following the mascot sheet's loop: the asker hooks, the explainer
explains, the asker says it back.

The same moods pick the characters' faces in the video (render.py) and, with expressive
voices, how each line is acted (tts.py), so what you see matches what you hear.
"""

ASKER_MOODS = ("bored", "curious", "gets", "hyped")
EXPLAINER_MOODS = ("chill", "explain", "think", "laugh")


def line_moods(roles: list[str]) -> list[tuple[str, str]]:
    """(speaker's mood, listener's mood) for each line, from each line's speaker role.

    Asker: bored on the opening hook, curious while asking, "gets it" on the closing recall.
    Explainer: explains (every third line he stops to think), laughs on his last line.
    Listening, the explainer is chill and the asker curious, or hyped at the explainer's last line.
    """
    explainer_lines = [i for i, role in enumerate(roles) if role == "explainer"]
    last = len(roles) - 1
    moods = []
    for i, role in enumerate(roles):
        if role == "asker":
            speaker = "bored" if i == 0 else "gets" if i == last else "curious"
            listener = "chill"
        elif role == "explainer":
            if i == explainer_lines[-1]:
                speaker = "laugh"
            else:
                speaker = "think" if explainer_lines.index(i) % 3 == 2 else "explain"
            listener = "hyped" if speaker == "laugh" else "curious"
        else:
            speaker, listener = "", ""
        moods.append((speaker, listener))
    return moods
