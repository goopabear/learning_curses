# For Windows, pip install 'windows-curses'
# For documentation on 'curses', visit: 'https://docs.python.org/3/library/curses.html#curses.init_pair'

import curses
from add_terminal import run_in_terminal
import time

def menu(window):
    # Terminal cursor; 0 = invisible, 1 = visible, 2 = borders-only
    curses.curs_set(1)
    # CSS-like styling; (id, foreground (text), background)
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)

    # Allow the window to scroll instead of erroring when text runs past the
    # bottom row. idlok enables the terminal's hardware scroll where available.
    window.scrollok(True)
    window.idlok(True)

    text = "With this Sacred Treasure, I summon Divine General, Mahoraga!"

    while True:
        window.clear()
        window.attron(curses.color_pair(1))

        for char in text:
            window.addch(char) # Draws each character of the message one at a time
            window.refresh() # Refreshes the window to show the new character
            time.sleep(0.0001) # Adds a small delay between each character for a "typing" effect

        # Move to a fresh line for the prompt. addstr with an explicit y past
        # the last row would still raise, even with scrollok, so write a newline
        # and let the scroll happen, then addstr at the current position.
        window.addstr("\n")
        window.addstr("Understand?")
        window.getch()

if __name__ == "__main__":

    @run_in_terminal
    def main():
        curses.wrapper(menu)

    main()