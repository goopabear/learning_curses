

# Curses operates with a set row/column count

Finding current lines and returning them:

end_y, end_x = window.getyx()
last_line = window.instr(end_y, 0).decode('utf-8').rstrip()


    