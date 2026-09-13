
# Let's try to make a module where we define functions that print repeatable block patterns using 'curses.

from util.add_terminal import pop_out_terminal
from basic_structure import Content, Terminal
import curses


def main():
    app = Terminal()
    print(app.run())


main()