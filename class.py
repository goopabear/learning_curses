# For Windows, pip install 'windows-curses'
# For documentation on 'curses', visit: 'https://docs.python.org/3/library/curses.html#curses.init_pair'

import curses
import time

from util.add_terminal import pop_out_terminal


class Content():
    lnum = 0
    lines = []

    def __init__(self, window, text: str = "Sample"):

        window.scrollok(True)
        window.idlok(True)
        curses.curs_set(0)

        self.text = text
        self.window = window
        #self.cursor = curses.curs_set(0) # Terminal cursor; 0 = invisible, 1 = visible, 2 = borders-only
        self.font = curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK) # CSS-like styling; (id, foreground (text), background)

    def message(self):
        self.window.attron(curses.color_pair(1))
        self.window.addstr(self.lnum, 0, self.text)
        end_y, end_x = self.window.getyx()

        line = 0
        while line <= end_y:
            each_line = self.window.instr(line, 0).decode('utf-8').rstrip()
            self.lines.append(repr(each_line))
            line += 1

    def total_lines(self):
        return self.lnum

    def each_line(self):
        return self.lines

        
def menu(window,text):
    content = Content(window, text)

    while True:
        window.clear()
        content.message()
        window.refresh()
        input = window.getch()
        if input in (10, 13, curses.KEY_ENTER):
            return content.each_line()


if __name__ == "__main__":
    @pop_out_terminal
    def main():
        essay = f"Hello there!\nMy name is Charlie\nWhat is your name?"
        output = curses.wrapper(menu, essay)
        if output:
            print(output)

    main()