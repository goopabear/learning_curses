# Input Mapping (Windows / windows-curses backend)

Keyboard:
    'Enter'     = 10     # or 459
    'Escape'    = 27
    'Tab'       = 9
    'Backspace' = 8      # or curses.KEY_BACKSPACE = 263, depending on terminal

Numpad (Num Lock ON — sends plain digits/operators):
    '0' = 48
    '1' = 49
    '2' = 50
    '3' = 51
    '4' = 52
    '5' = 53
    '6' = 54
    '7' = 55
    '8' = 56
    '9' = 57
    '.' = 462   # PADSTOP
    '/' = 458   # PADSLASH
    '*' = 463   # PADSTAR
    '-' = 464   # PADMINUS
    '+' = 465   # PADPLUS
    'Enter' = 459   # PADENTER

Arrow Keys:
    'Up'    = 259
    'Down'  = 258
    'Left'  = 260
    'Right' = 261

Navigation:
    'Home'      = 262
    'End'       = 358
    'Page Up'   = 339
    'Page Down' = 338
    'Insert'    = 331
    'Delete'    = 330