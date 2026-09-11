
# Let's try to make a module where we define functions that print repeatable block patterns using 'curses.

from util.add_terminal import pop_out_terminal

import curses



class Content():
    def __init__(self, window, text: str):
        window.scrollok(True)

        self.window = window
        self.text = text
        self.cursor = curses.curs_set(0) # Terminal cursor; 0 = invisible, 1 = visible, 2 = borders-only

    def font_color(self):
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK) # CSS-like styling; (id, foreground (text), background)
        self.window.attron(curses.color_pair(1))


    def text_box(self):
        for char in self.text:
            self.window.addch(char) # Draws each character of the message one at a time


    def choices(self):
        print()


class Terminal():
    
    def __init__(self):
        self.text = 'Hi'
        self.terminal = curses.wrapper(menu, text)
        
        
    def menu(window, text):
        content = Content(window, text)
        content.font_color()

        while True:
            window.clear()
            content.text_box()
            window.refresh()

            user_input = window.getch()
            return user_input



if __name__ == "__main__":

    @pop_out_terminal
    def main():
        text = 'Example'
        
        if output:
            print(output)

    main()