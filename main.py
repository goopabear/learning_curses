# For Windows, pip install 'windows-curses'
# For documentation on 'curses', visit: 'https://docs.python.org/3/library/curses.html#curses.init_pair'

import curses

from add_terminal import run_in_terminal
import time

# Define a menu function with an arbitrary argument, 'window'.
def menu(window):
    # Terminal cursor; 0 = invisible, 1 = visible, 2 = borders-only
    curses.curs_set(0) 
    # CSS-like styling; (id, foreground (text), background)
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    options = ["A", "B"]
    current = 1

    message = "Pick an option (Up/Down to navigate, Enter to select):"

    while True:
        window.clear() # Clears terminal
        window.attron(curses.color_pair(1)) # Turns on color pair 1 (green text on black background)

        for char in message:
            window.addch(char) # Draws each character of the message one at a time
            window.refresh() # Refreshes the window to show the new character
            time.sleep(0.01) # Adds a small delay between each character for a "typing" effect

        for i, option in enumerate(options):
            i += 1 # Start drawing options from line 1 
            if i == current:
                window.attron(curses.color_pair(2)) # Turns on highlighter
                window.addstr(i, 0, option) # Draws option; i = index, 0 = left-margin, option = display-text
                window.attron(curses.color_pair(1)) # Turns off highlighter
            else:
                window.addstr(i, 0, option) # Draws option; no highlight.
        window.refresh()

        key = window.getch()

        if key == curses.KEY_UP:
            current = max(1, current - 1)
        elif key == curses.KEY_DOWN:
            current = min(2, current + 1)
        elif key in (curses.KEY_ENTER, ord("\n")):
            current -= 1  # Adjust for 0-based indexing
            return options[current]


def main():
    choice = curses.wrapper(menu)
    print(f"You picked: {choice}")

if __name__ == "__main__":
    main()
