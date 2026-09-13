

# Curses operates with a set row/column count

Finding current lines and returning them:

end_y, end_x = window.getyx()
last_line = window.instr(end_y, 0).decode('utf-8').rstrip()

# Keys

Keyboard:
    'Enter' = 10

Numpad:
    'Enter' = 459
    '0' = 48

Arrow Keys:
    'Up' = 259
    'Down' = 258
    'Left' = 260
    'Right' = 261