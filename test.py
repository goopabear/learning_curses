import curses

def main(window):
    while True:
        window.clear()
        window.addstr(str(window.getch()))
        window.refresh()
        window.getch()


curses.wrapper(main)