
# Let's try to make a module where we define functions that print repeatable block patterns using 'curses.

from util.add_terminal import pop_out_terminal

import curses


@pop_out_terminal    
def UI(window, text):
    content = Content(window, text)
    content.font_color()

    while True:
        window.clear()
        y = content.text_box()
        window.refresh()

        user_input = window.getch()
        return y

class Terminal():
    def __init__(self):
        self.text = 'Hi'

    def run(self):
        return curses.wrapper(UI, self.text)


class Content():
    def __init__(self, window, text: str):
        window.scrollok(True)

        self.window = window
        self.text = text
        self.cursor = curses.curs_set(0) # Terminal cursor; 0 = invisible, 1 = visible, 2 = borders-only

    def font_color(self):
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK) # CSS-like styling; (id, foreground (text), background)
        self.window.attron(curses.color_pair(1))

    def get_x(self) -> int:
        y, x = self.window.getyx()
        return x
    
    def get_y(self) -> int:
        y, x = self.window.getyx()
        return y

    def text_box(self):
        for char in self.text:
            self.window.addch(char) # Draws each character of the message one at a time
        return self.get_y()

    def choices(self):
        print()





