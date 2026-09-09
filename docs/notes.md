

# Curses operates with a set row/column count

## Targeting rows that already have been printed

    # First, print any length of string in one loop.

    # Get the ending row/column
    end_y, end_x = window.getyx()

    # Go back up using end_y
    window.addstr(end_y - 1, 0, str)
