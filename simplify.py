
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

        self.window = window
        curses.curs_set(0) # Terminal cursor; 0 = invisible, 1 = visible, 2 = borders-only
        self.curs_y = 0
        self.curs_x = 0
        self.cap_y = 0
        self.cap_x = 0
        # Default font color:
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK) # CSS-like styling; (id, foreground (text), background)
        self.window.attron(curses.color_pair(1))
        
    # ----------------------------------------------------------------------------------------------------
    # Helper functions: 
    def get_y(self) -> int:
        self.curs_y, self.curs_x = self.window.getyx()
        return self.curs_y
    def get_x(self) -> int:
        self.curs_y, self.curs_x = self.window.getyx()
        return self.curs_x
    
    def max_y(self) -> int:
        self.cap_y, self.cap_x = self.window.getmaxyx()
        return self.cap_y
    def max_x(self) -> int:
        self.cap_y, self.cap_x = self.window.getmaxyx()
        return self.cap_x
    
    def get_char(self, y: int, x: int) -> str:
        raw = self.window.inch(y, x)
        return chr(raw & curses.A_CHARTEXT)
    
    # ----------------------------------------------------------------------------------------------------
    # Needs to be improved. Lazy error handling.

    def textbox(self, text, rate: float = 0.001):

        return 

    # ----------------------------------------------------------------------------------------------------
    def inputbox(self):
        curses.curs_set(1)
        input = self.window.getch()
        if input in ALPHABET:
            # 'Letter' logic
            input = ALPHABET[input]
            self.window.addch(input)
            self.curs_y, self.curs_x = self.window.getyx()
            
        elif input in SPECIAL_CHARACTERS:
            # 'Space' logic
            if input == 32:
                self.window.addch(' ')
                self.curs_y, self.curs_x = self.window.getyx()

            # 'Newline' logic
            if input in (10, 459):
                self.window.addstr('\n')
                self.curs_y, self.curs_x = self.window.getyx()

            # 'Delete' logic
            if input in (8, 330):
                if self.curs_x > 0: #
                    self.window.move(self.curs_y, self.curs_x - 1)
                    self.window.delch()
                    self.curs_x -= 1
                elif self.curs_x <= 0 and self.curs_y > 0:
                    self.curs_y -= 1
                    self.curs_x = self.max_x() - 1
                    while True:
                        if self.get_char(self.curs_y, self.curs_x) == ' ':
                            self.curs_x -= 1
                        else:
                            try:
                                self.window.move(self.curs_y, self.curs_x+1)
                                self.curs_y, self.curs_x = self.window.getyx()
                                break
                            except:
                                self.window.addch(self.curs_y, self.curs_x, ' ')
                                self.window.move(self.curs_y, self.curs_x)
                                self.curs_y, self.curs_x = self.window.getyx()
                                break
        curses.curs_set(0)
    # ----------------------------------------------------------------------------------------------------
    def inner_choices(self, options: list = ['First', 'Second', 'Third']):
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN) # Highligher color

        while True:
            for option in options:
                    self.window.attron(curses.color_pair(2)) # Turns on highlighter
                    self.window.addstr(option) # Draws option; i = index, 0 = left-margin, option = display-text
                    self.window.addstr('\n')
                    self.window.attron(curses.color_pair(1)) # Turns off highlighter

            self.window.refresh()
            key = self.window.getch()

            if key == curses.KEY_UP:
                current = max(1, current - 1)
            elif key == curses.KEY_DOWN:
                current = min(2, current + 1)
            elif key in (curses.KEY_ENTER, ord("\n")):
                current -= 1  # Adjust for 0-based indexing
                return options[current]

    def choices(self, options: list = ['First', 'Second', 'Third']):
        return self.auto_wrap(self.inner_choices, options)

    # ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    def main(window):
        window.clear()
        app = Content(window)
        while True:
            app.inputbox()


        
    print(Terminal(main).run())

