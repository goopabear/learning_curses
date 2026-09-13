
# Let's try to make a module where we define functions that print repeatable block patterns using 'curses.

from util.add_terminal import pop_out_terminal
from util.key_mappings import ALPHABET, SPECIAL_CHARACTERS
from time import sleep
import curses


def load_window(inner_func):
    @pop_out_terminal    
    def UI(window):
        window.clear()
        try:
            output = inner_func(window)
        except NameError as e:
            window.addstr(0, 0, str(e))
            window.refresh()
            window.getch()
            return None
        return output
    return UI


class Terminal():
    def __init__(self, inner_func):
        self.inner_func = inner_func

    def run(self):
        return curses.wrapper(load_window(self.inner_func))


class Content():
    def __init__(self, window):
        window.scrollok(True)
        window.idlok(True)

        self.window = window
        self.cursor = curses.curs_set(0) # Terminal cursor; 0 = invisible, 1 = visible, 2 = borders-only

        self.ycoord = 0
        self.xcoord = 0

        # Default font color:
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK) # CSS-like styling; (id, foreground (text), background)
        self.window.attron(curses.color_pair(1))

    def get_x(self) -> int:
        y, x = self.window.getyx()
        return x
    
    def get_y(self) -> int:
        y, x = self.window.getyx()
        return y

    def max_x(self) -> int:
        y, x = self.window.getmaxyx()
        return x

    def max_y(self) -> int:
        y, x = self.window.getmaxyx()
        return y
    
    def text_box(self, text, rate: float = 0.001):
        for char in str(text):
            self.window.addch(char) # Draws each character of the message one at a time
            self.window.refresh()
            sleep(rate)      
            
        self.ycoord, self.xcoord = self.window.getyx()
        return

    def input_box(self):
        curses.curs_set(1)
        input = self.window.getch()
        if input in ALPHABET:
            input = ALPHABET[input]
            self.window.addch(input)

            self.ycoord, self.xcoord = self.window.getyx()

        elif input in SPECIAL_CHARACTERS:
            if input in (8, 330):
                if self.xcoord > 0:
                    self.window.move(self.ycoord, self.xcoord - 1)
                    self.window.delch()
                    self.xcoord -= 1
                elif self.xcoord <= 0 and self.ycoord > 0:
                    self.window.addch(self.ycoord-1, self.max_x()-1, ' ')
                    self.window.move(self.ycoord-1, self.max_x()-1)
                    self.window.delch()
                    self.ycoord, self.xcoord = self.window.getyx()

        else:
            self.input_box()
        curses.curs_set(0)


    def choices(self):
        print()


if __name__ == "__main__":

    def main(window):
        window.clear()
        app = Content(window)
        while True:
            app.input_box()


        
    Terminal(main).run()

