
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
        self.cap_y, self.cap_x = self.window.getmaxyx()
        # Default font color:
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK) # CSS-like styling; (id, foreground (text), background)
        self.window.attron(curses.color_pair(1))
        
    # ----------------------------------------------------------------------------------------------------
    # Helper functions: 
    def update_curs_position(self) -> int:
        self.curs_y, self.curs_x = self.window.getyx()
    
    def update_window_max(self) -> int:
        self.cap_y, self.cap_x = self.window.getmaxyx()

    # ----------------------------------------------------------------------------------------------------
    # Window Resize Handler:
    def input(self):
        user_input = self.window.getch()
        self.update_window_max()
        if self.cap_y <= 3 or self.cap_x <= 48:
            self.size_warning()
        else:
            return user_input

    def size_warning(self):
        self.window.clear()
        self.window.addstr('Please make window bigger!!!')
        while True:
            self.window.getch()
            self.update_window_max()
            if self.cap_y > 3 or self.cap_x > 48:
                self.window.clear()
                self.window.addstr('Thanks!')
                self.window.getch()
                return


    # ----------------------------------------------------------------------------------------------------
    # Helper functions: 
    def display_size(self):
        while True:
            try:
                self.input()
                self.window.clear()
                self.window.addstr(str(self.cap_y))
                #self.window.addstr('\n')
                self.window.addstr(str(self.cap_x))
            except Exception as e:
                return e

    def resize(self):
        self.window.newwin(10,10,0,0)  # window is now 15 rows x 30 cols




if __name__ == "__main__":

    def main(window):
        window.clear()
        app = Content(window)
        return app.display_size()


        
    print(Terminal(main).run())