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

        while end_y >= 0:
            each_line = self.window.instr(end_y, 0).decode('utf-8').rstrip()
            self.lines.append(each_line)
            end_y -= 1

        self.lines.reverse

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
        essay = """Gojo Satoru's greatest advantage over Goku lies in a technique that removes the fight before it even starts: Infinity. This isn't simple super-speed or a shield; it is a conceptual barrier that mathematically prevents anything from ever truly reaching him, constantly halving the distance an object travels toward him so contact never occurs. Goku's strength comes from raw physical force and ki, both of which rely on closing distance and connecting. Against a fighter whose base ability makes 'connecting' a logical impossibility, Goku's punches, kicks, and even most ki blasts would stall out just before impact, no matter how fast or strong they are.

Even if Goku found a workaround, such as using Instant Transmission to skip the need to physically close distance, Gojo has a second layer that solves that problem entirely: Domain Expansion. Unlimited Void traps anyone caught inside it in an inescapable space flooded with infinite sensory information, effectively paralyzing them through overwhelming information overload rather than damage. Unless the opponent has a domain or ability of their own to counter it, a guaranteed hit is guaranteed, and Goku, for all his power, has no equivalent technique built to escape a domain's certain-hit property.

Finally, Gojo's Six Eyes give him near-perfect control over his cursed energy, letting him use techniques at a fraction of the cost most sorcerers would pay, while Hollow Purple combines his Blue and Red techniques into an attack with small-scale universe-erasing potential. Goku's power scaling is immense, but it is still fundamentally physical and elemental, forms of offense that Infinity is specifically built to neutralize. Put simply, Goku fights by hitting harder and faster than his opponent, but Gojo's kit is designed around the premise that he never has to be hit at all, which is precisely the matchup Goku is least equipped to solve."""

        output = curses.wrapper(menu, essay)
        if output:
            print(output)

    main()