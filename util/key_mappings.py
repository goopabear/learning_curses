

# --- Special / named keys ---------------------------------------------

SPECIAL_CHARACTERS = {
    32: "Spacebar",
    10: "Enter",
    27: "Escape",
    9: "Tab",
    8: "Backspace",
    263: "Backspace (curses)",

    # Numpad (windows-curses / PDCurses specific)
    459: "Numpad Enter",
    458: "Numpad /",
    463: "Numpad *",
    464: "Numpad -",
    465: "Numpad +",
    462: "Numpad .",

    # Arrow keys
    259: "Up",
    258: "Down",
    260: "Left",
    261: "Right",

    # Navigation
    262: "Home",
    358: "End",
    339: "Page Up",
    338: "Page Down",
    331: "Insert",
    330: "Delete",

    # Window Resize
    546: "Resize"
}

# --- Letter keys ---------------------------------------------------------

ALPHABET = {
    97: "a", 98: "b", 99: "c", 100: "d", 101: "e", 102: "f", 103: "g",
    104: "h", 105: "i", 106: "j", 107: "k", 108: "l", 109: "m", 110: "n",
    111: "o", 112: "p", 113: "q", 114: "r", 115: "s", 116: "t", 117: "u",
    118: "v", 119: "w", 120: "x", 121: "y", 122: "z",

    65: "A", 66: "B", 67: "C", 68: "D", 69: "E", 70: "F", 71: "G",
    72: "H", 73: "I", 74: "J", 75: "K", 76: "L", 77: "M", 78: "N",
    79: "O", 80: "P", 81: "Q", 82: "R", 83: "S", 84: "T", 85: "U",
    86: "V", 87: "W", 88: "X", 89: "Y", 90: "Z",
}
