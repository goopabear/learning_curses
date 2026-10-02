"""
add_terminal.py
===============

One import, one decorator. Windows and Linux.

The decorator opens a **fixed-size terminal window**: it is resized to exactly
cols x rows, its resize border / maximize button / scrollbars are removed, and
if something resizes it anyway it is snapped straight back.

Your function gets the real curses window -- plain curses, nothing simulated --
so the cursor, scrolling, attributes and insert/delete all behave exactly as
they always have. The only thing the window size ever does is stay put.

Two modes:

  raw=True   -- (default) your function gets the real curses window and owns
                its own loop. Use this for cursor-based UIs: typing, prompts,
                addch, getch.

  raw=False  -- your function is called once per frame with a drawing canvas.
                Use this for dashboards and redraw-everything UIs.

    from util.add_terminal import curses_app

    @curses_app(cols=100, rows=30)
    def main(window):
        window.addstr(0, 0, "hello")
        window.getch()

    main()

The decorated function may also be handed to curses.wrapper():

    curses.wrapper(main)        # reuses that session, does not re-init curses

On Windows this needs `pip install windows-curses`.
"""

from __future__ import annotations

import functools
import os
import shutil
import subprocess
import sys
import time
import traceback

try:
    import curses
except ImportError:  # pragma: no cover
    raise ImportError(
        "The curses module is unavailable. On Windows, run: "
        "pip install windows-curses"
    ) from None

__all__ = ["curses_app", "Window", "UI", "SizeGuard"]

_CHILD_FLAG = "_CURSES_APP_CHILD"
IS_WINDOWS = sys.platform.startswith("win")


# ---------------------------------------------------------------------------
# win32 console plumbing
# ---------------------------------------------------------------------------
# `mode con:` shells out, prints, and cannot run while curses owns the screen.
# The console API does the same job in-process and mid-session, so it is the
# primary path and `mode con:` is only the fallback.

def _win_console():
    """(ctypes, kernel32, handle to the active screen buffer) or None."""
    try:
        import ctypes
        from ctypes import wintypes
    except Exception:
        return None

    try:
        kernel32 = ctypes.windll.kernel32
        GENERIC_READ, GENERIC_WRITE = 0x80000000, 0x40000000
        FILE_SHARE_READ, FILE_SHARE_WRITE = 1, 2
        OPEN_EXISTING = 3

        kernel32.CreateFileW.restype = wintypes.HANDLE
        handle = kernel32.CreateFileW(
            "CONOUT$", GENERIC_READ | GENERIC_WRITE,
            FILE_SHARE_READ | FILE_SHARE_WRITE, None, OPEN_EXISTING, 0, None)
        if not handle or handle == wintypes.HANDLE(-1).value:
            return None
        return ctypes, kernel32, handle
    except Exception:
        return None


def _win_structs(ctypes):
    from ctypes import wintypes

    class COORD(ctypes.Structure):
        _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]

    class SMALL_RECT(ctypes.Structure):
        _fields_ = [("Left", wintypes.SHORT), ("Top", wintypes.SHORT),
                    ("Right", wintypes.SHORT), ("Bottom", wintypes.SHORT)]

    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        _fields_ = [("dwSize", COORD), ("dwCursorPosition", COORD),
                    ("wAttributes", wintypes.WORD), ("srWindow", SMALL_RECT),
                    ("dwMaximumWindowSize", COORD)]

    return COORD, SMALL_RECT, CONSOLE_SCREEN_BUFFER_INFO


def _win_window_size():
    """Current console window size as (cols, rows), or None."""
    console = _win_console()
    if console is None:
        return None
    ctypes, kernel32, handle = console
    try:
        _, _, INFO = _win_structs(ctypes)
        info = INFO()
        if not kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(info)):
            return None
        width = info.srWindow.Right - info.srWindow.Left + 1
        height = info.srWindow.Bottom - info.srWindow.Top + 1
        return (width, height) if width > 0 and height > 0 else None
    except Exception:
        return None
    finally:
        kernel32.CloseHandle(handle)


def _win_set_size(cols: int, rows: int) -> bool:
    """Set window *and* buffer to cols x rows, so there are no scrollbars."""
    console = _win_console()
    if console is None:
        return False
    ctypes, kernel32, handle = console
    try:
        COORD, SMALL_RECT, _ = _win_structs(ctypes)
        kernel32.GetLargestConsoleWindowSize.restype = COORD
        largest = kernel32.GetLargestConsoleWindowSize(handle)
        if largest.X > 0:
            cols = min(cols, largest.X)
        if largest.Y > 0:
            rows = min(rows, largest.Y)
        if cols < 1 or rows < 1:
            return False

        # The window shrinks out of the way first, then the buffer is set to
        # the exact target, then the window is grown onto it. The other order
        # fails whenever the buffer and the window cross sizes.
        tiny = SMALL_RECT(0, 0, 0, 0)
        kernel32.SetConsoleWindowInfo(handle, True, ctypes.byref(tiny))
        ok = bool(kernel32.SetConsoleScreenBufferSize(handle,
                                                      COORD(cols, rows)))
        rect = SMALL_RECT(0, 0, cols - 1, rows - 1)
        ok = bool(kernel32.SetConsoleWindowInfo(handle, True,
                                                ctypes.byref(rect))) and ok
        # A buffer larger than the window would put the scrollbars back.
        kernel32.SetConsoleScreenBufferSize(handle, COORD(cols, rows))
        return ok
    except Exception:
        return False
    finally:
        kernel32.CloseHandle(handle)


# ---------------------------------------------------------------------------
# terminal sizing
# ---------------------------------------------------------------------------

def _terminal_size():
    """Current terminal size as (cols, rows)."""
    if IS_WINDOWS:
        size = _win_window_size()
        if size:
            return size
    try:
        size = shutil.get_terminal_size()
        return size.columns, size.lines
    except Exception:
        return 80, 24


def _set_terminal_size(cols: int, rows: int, quiet: bool = False) -> bool:
    """Resize the terminal. `quiet` forbids anything that writes to stdout."""
    if IS_WINDOWS:
        if _win_set_size(cols, rows):
            return True
        if quiet:
            return False
        return os.system(f"mode con: cols={cols} lines={rows}") == 0
    try:
        # xterm window-manipulation sequence: CSI 8 ; rows ; cols t
        sys.stdout.write(f"\x1b[8;{rows};{cols}t")
        sys.stdout.flush()
        return True
    except Exception:
        return False


def _sync_curses_size() -> None:
    """Tell curses the terminal changed size, so refresh clips correctly."""
    cols, rows = _terminal_size()
    try:
        curses.resize_term(rows, cols)
    except Exception:
        pass
    try:
        curses.update_lines_cols()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# taking resizing away from the user
# ---------------------------------------------------------------------------

def _lock_windows():
    """
    Strip resizing from the console window. Returns an undo callable, or None.

    Removes the sizing border, the maximize box and the scrollbars, and also
    deletes Size and Maximize from the system (title-bar) menu, which is the
    other way a console window can be resized by hand.
    """
    try:
        import ctypes
    except Exception:
        return None

    GWL_STYLE = -16
    WS_SIZEBOX, WS_MAXIMIZEBOX = 0x00040000, 0x00010000
    WS_VSCROLL, WS_HSCROLL = 0x00200000, 0x00100000
    SC_SIZE, SC_MAXIMIZE = 0xF000, 0xF030
    MF_BYCOMMAND = 0x0
    SWP_NOSIZE, SWP_NOMOVE, SWP_NOZORDER, SWP_FRAMECHANGED = 1, 2, 4, 0x20
    reposition = SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED

    try:
        user32 = ctypes.windll.user32
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if not hwnd:
            return None

        style = user32.GetWindowLongW(hwnd, GWL_STYLE)
        new_style = (style & ~WS_SIZEBOX & ~WS_MAXIMIZEBOX
                     & ~WS_VSCROLL & ~WS_HSCROLL)
        if new_style != style:
            user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)
            user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, reposition)

        menu = user32.GetSystemMenu(hwnd, False)
        if menu:
            user32.DeleteMenu(menu, SC_SIZE, MF_BYCOMMAND)
            user32.DeleteMenu(menu, SC_MAXIMIZE, MF_BYCOMMAND)
            user32.DrawMenuBar(hwnd)

        def undo():
            try:
                user32.SetWindowLongW(hwnd, GWL_STYLE, style)
                user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, reposition)
                user32.GetSystemMenu(hwnd, True)   # rebuild the default menu
                user32.DrawMenuBar(hwnd)
            except Exception:
                pass

        return undo
    except Exception:
        return None


def _lock_x11():
    """Pin the window manager's min/max size hints. Returns an undo callable."""
    try:
        from Xlib import display, Xutil
    except Exception:
        return None
    try:
        d = display.Display()
        root = d.screen().root
        win = d.get_input_focus().focus
        if not win or isinstance(win, int):
            return None
        for _ in range(32):  # walk up to the window the WM manages
            tree = win.query_tree()
            if tree.parent is None or tree.parent.id == root.id:
                break
            win = tree.parent
        geom = win.get_geometry()
        hints = win.get_wm_normal_hints()
        if hints is None:
            return None
        old_flags = hints.flags
        hints.flags |= Xutil.PMinSize | Xutil.PMaxSize
        hints.min_width = hints.max_width = geom.width
        hints.min_height = hints.max_height = geom.height
        win.set_wm_normal_hints(hints)
        d.sync()

        def undo():
            try:
                hints.flags = old_flags
                win.set_wm_normal_hints(hints)
                d.sync()
            except Exception:
                pass

        return undo
    except Exception:
        return None


def _lock_terminal_size():
    return _lock_windows() if IS_WINDOWS else _lock_x11()


class SizeGuard:
    """
    Keeps the terminal at exactly cols x rows for the life of the app.

    apply()     resize now, and take away the resize affordances
    reassert()  called whenever curses reports a resize: if the terminal is no
                longer the right size, snap it back
    release()   undo the lock, and restore the original size if asked to

    reassert() is a no-op once the size already matches, so the resize event
    our own snap-back generates cannot start a loop.
    """

    def __init__(self, cols: int, rows: int, lock: bool = True,
                 restore: bool = False):
        self.cols = cols
        self.rows = rows
        self.lock = lock
        self.restore = restore
        self.original = _terminal_size() if restore else None
        self._undo = None

    def matches(self) -> bool:
        cols, rows = _terminal_size()
        return cols == self.cols and rows == self.rows

    def apply(self, quiet: bool = False, sync: bool = False) -> None:
        if not self.matches():
            _set_terminal_size(self.cols, self.rows, quiet=quiet)
        if self.lock and self._undo is None:
            self._undo = _lock_terminal_size()
        if sync:
            _sync_curses_size()

    def reassert(self) -> bool:
        """True if the terminal had drifted and was snapped back."""
        if self.matches():
            _sync_curses_size()
            return False
        _set_terminal_size(self.cols, self.rows, quiet=True)
        _sync_curses_size()
        return True

    def release(self) -> None:
        if self._undo is not None:
            self._undo()
            self._undo = None
        if self.restore and self.original:
            _set_terminal_size(*self.original)


# ---------------------------------------------------------------------------
# launching the popup
# ---------------------------------------------------------------------------

# (executable, flag that introduces the command to run)
_LINUX_EMULATORS = [
    ("x-terminal-emulator", "-e"),
    ("konsole", "-e"),
    ("xfce4-terminal", "-x"),
    ("mate-terminal", "-x"),
    ("xterm", "-e"),
    ("alacritty", "-e"),
    ("kitty", "--"),
    ("gnome-terminal", "--"),
]


def _conhost_path():
    root = os.environ.get("SystemRoot") or r"C:\Windows"
    path = os.path.join(root, "System32", "conhost.exe")
    return path if os.path.exists(path) else None


def _relaunch(legacy_console: bool = True) -> None:
    script = os.path.abspath(sys.argv[0])
    command = [sys.executable, script] + sys.argv[1:]

    env = os.environ.copy()
    env[_CHILD_FLAG] = "1"
    cwd = os.path.dirname(script) or None

    if IS_WINDOWS:
        # No cmd.exe and no `start`. CREATE_NEW_CONSOLE gives the child its own
        # console window, and subprocess builds the command line for
        # CreateProcess directly, so paths with spaces need no shell quoting.
        #
        # (`cmd /k` only preserves quotes when the line has exactly two quote
        # characters; with a quoted interpreter *and* a quoted script it strips
        # the outer pair and mangles both paths. Avoiding cmd avoids the rule.)
        #
        # conhost.exe is asked for first: on Windows 11 a new console is handed
        # to Windows Terminal, a tabbed app whose window we cannot pin, while
        # conhost gives the classic console window that SizeGuard can lock.
        conhost = _conhost_path() if legacy_console else None
        if conhost:
            try:
                child = subprocess.Popen(
                    [conhost] + command,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    env=env, cwd=cwd)
                time.sleep(0.3)
                if child.poll() in (None, 0):
                    return
            except Exception:
                pass

        subprocess.Popen(
            command,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            env=env, cwd=cwd)
        return

    for name, exec_flag in _LINUX_EMULATORS:
        path = shutil.which(name)
        if not path:
            continue
        try:
            subprocess.Popen([path, exec_flag] + command, env=env, cwd=cwd)
            return
        except Exception:
            continue

    raise RuntimeError(
        "No supported terminal emulator found. Tried: "
        + ", ".join(name for name, _ in _LINUX_EMULATORS)
    )


# ---------------------------------------------------------------------------
# raw mode: the real curses window, at a fixed size
# ---------------------------------------------------------------------------

class Window:
    """
    The real curses window (stdscr), with the terminal pinned to cols x rows.

    Every method is the genuine curses one -- addch, addstr, move, delch,
    getyx, getmaxyx, scrollok, idlok, attron, insertln and the rest are
    forwarded straight through -- so the cursor lands exactly where curses
    says it should. Nothing is drawn off-screen and copied back, because the
    window cannot change size in the first place.

    Only three things differ from bare stdscr:

      getch()   refreshes first, so the hardware cursor sits on the window's
                cursor before the read, and swallows KEY_RESIZE: the terminal
                is snapped back to its fixed size and repainted, and your
                input code never sees the event
      getkey()  returns "" instead of raising when a read times out
      addch(), addstr() and insch() do not raise at the bottom-right cell

    getmaxyx() is the true window size, which SizeGuard holds at rows x cols.
    """

    def __init__(self, stdscr, cols: int, rows: int, guard=None):
        # Set first: __getattr__ forwards to it and must never recurse.
        self._win = stdscr
        self._guard = guard
        self.cols = cols
        self.rows = rows

    # Anything not defined here goes to the real window.
    def __getattr__(self, name):
        return getattr(self._win, name)

    # -- size -------------------------------------------------------------

    def term_size(self):
        """Actual terminal size. Same as getmaxyx(), kept for symmetry."""
        return self._win.getmaxyx()

    # -- input ------------------------------------------------------------

    def getch(self, *args):
        """Ordinary curses getch; KEY_RESIZE is handled internally."""
        if len(args) == 2:          # getch(y, x) moves there first, so do the
            try:                    # move before the refresh below, not after
                self._win.move(*args)
            except curses.error:
                pass

        while True:
            # Sync the hardware cursor with the window's own cursor, so a
            # visible cursor sits where the last write left it.
            try:
                self._win.refresh()
            except curses.error:
                pass

            try:
                ch = self._win.getch()
            except curses.error:
                return -1

            if ch != curses.KEY_RESIZE:
                return ch

            if self._guard is not None:
                self._guard.reassert()
            else:
                curses.update_lines_cols()
            try:
                # The console blanks itself on a resize; repaint from the
                # curses buffer rather than erasing what the app drew.
                self._win.redrawwin()
                self._win.refresh()
            except curses.error:
                pass

    def getkey(self, *args):
        ch = self.getch(*args)
        return chr(ch) if 0 <= ch < 0x110000 else ""

    # -- forgiving writes -------------------------------------------------
    # A write that fills the bottom-right cell raises curses.error even though
    # the character lands. Swallowing that keeps a stray character from killing
    # the app mid-draw; the cursor is left exactly where curses left it.

    def addch(self, *args, **kwargs):
        try:
            return self._win.addch(*args, **kwargs)
        except curses.error:
            return None

    def addstr(self, *args, **kwargs):
        try:
            return self._win.addstr(*args, **kwargs)
        except curses.error:
            return None

    def insch(self, *args, **kwargs):
        try:
            return self._win.insch(*args, **kwargs)
        except curses.error:
            return None


# ---------------------------------------------------------------------------
# frame mode: an immediate-mode drawing canvas
# ---------------------------------------------------------------------------

class UI:
    """A fixed-size canvas plus this frame's input. See curses_app(raw=False)."""

    BOLD = curses.A_BOLD
    REVERSE = curses.A_REVERSE
    UNDERLINE = curses.A_UNDERLINE
    DIM = curses.A_DIM

    def __init__(self, stdscr, cols: int, rows: int):
        self.cols = cols
        self.rows = rows
        self.stdscr = stdscr
        self.state: dict = {}
        self.key: int = -1
        self.term_cols = 0
        self.term_rows = 0
        self._running = True

    def quit(self) -> None:
        self._running = False

    def addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        if y < 0 or y >= self.rows or x >= self.cols:
            return
        text = str(text)
        if x < 0:
            text = text[-x:]
            x = 0
        text = text[: self.cols - x]
        if not text:
            return
        try:
            self.stdscr.addstr(y, x, text, attr)
        except curses.error:
            # The bottom-right cell raises even though the write lands.
            pass

    def center(self, y: int, text: str, attr: int = 0) -> None:
        self.addstr(y, max(0, (self.cols - len(str(text))) // 2), text, attr)

    def hline(self, y: int, x: int, width: int, ch: str = "-",
              attr: int = 0) -> None:
        self.addstr(y, x, ch * width, attr)

    def box(self, top: int, left: int, height: int, width: int,
            attr: int = 0) -> None:
        if height < 2 or width < 2:
            return
        right, bottom = left + width - 1, top + height - 1
        self.addstr(top, left, "+" + "-" * (width - 2) + "+", attr)
        self.addstr(bottom, left, "+" + "-" * (width - 2) + "+", attr)
        for y in range(top + 1, bottom):
            self.addstr(y, left, "|", attr)
            self.addstr(y, right, "|", attr)

    def _erase(self) -> None:
        self.stdscr.erase()

    def _blit(self) -> None:
        try:
            self.stdscr.refresh()
        except curses.error:
            pass


# ---------------------------------------------------------------------------
# loops
# ---------------------------------------------------------------------------

def _prepare(stdscr, guard) -> None:
    # The cursor is left alone here: raw mode hands you plain curses, so
    # whether the cursor shows is your call, exactly as it is under
    # curses.wrapper. Frame mode hides it, since it repaints every tick.
    try:
        stdscr.keypad(True)     # so getch returns KEY_UP, KEY_BACKSPACE, ...
    except curses.error:
        pass
    if guard is not None:
        # curses may have started before the resize landed; settle it now.
        guard.apply(quiet=True, sync=True)


def _too_small(stdscr, rows, cols, need_cols, need_rows) -> None:
    stdscr.erase()
    for i, line in enumerate(("Window too small",
                              f"need {need_cols}x{need_rows}, "
                              f"have {cols}x{rows}")):
        if i >= rows:
            break
        try:
            stdscr.addstr(i, 0, line[: max(0, cols - 1)])
        except curses.error:
            pass
    stdscr.refresh()


def _raw_loop(stdscr, fn, cols, rows, guard, args, kwargs):
    _prepare(stdscr, guard)
    stdscr.timeout(-1)          # blocking input; your loop controls the pace
    window = Window(stdscr, cols, rows, guard)
    return fn(window, *args, **kwargs)


def _frame_loop(stdscr, fn, cols, rows, min_cols, min_rows, tick_ms, guard,
                args, kwargs):
    _prepare(stdscr, guard)
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.timeout(tick_ms)
    ui = UI(stdscr, cols, rows)

    while ui._running:
        ui.term_rows, ui.term_cols = stdscr.getmaxyx()
        if ui.term_rows < min_rows or ui.term_cols < min_cols:
            _too_small(stdscr, ui.term_rows, ui.term_cols, min_cols, min_rows)
        else:
            ui._erase()
            if fn(ui, *args, **kwargs) is False:
                break
            ui._blit()

        ch = stdscr.getch()
        if ch == curses.KEY_RESIZE:
            if guard is not None:
                guard.reassert()
            else:
                curses.update_lines_cols()
            ui.key = -1
            continue
        ui.key = ch


# ---------------------------------------------------------------------------
# decorator
# ---------------------------------------------------------------------------

def _is_curses_window(obj) -> bool:
    """True for a real curses window, e.g. the stdscr curses.wrapper passes."""
    win_type = getattr(curses, "window", None)
    if win_type is not None:
        return isinstance(obj, win_type)
    return (not isinstance(obj, (Window, UI))
            and all(hasattr(obj, name)
                    for name in ("getmaxyx", "refresh", "getch", "addstr")))


def _end_curses() -> None:
    """Drop out of curses before printing or relaunching, if we are in it."""
    try:
        if not curses.isendwin():
            curses.endwin()
    except Exception:
        pass


def curses_app(func=None, *, cols: int = 80, rows: int = 24, raw: bool = True,
               min_cols: int = 40, min_rows: int = 10, tick_ms: int = 100,
               popup: bool = True, keep_open: bool = True,
               lock: bool = True, legacy_console: bool = True,
               settle: float = 0.3):
    """
    Run the decorated function in a new, fixed-size, non-resizable terminal.

    raw=True   (default) fn(window) gets a real curses window and runs its own
               loop -- getch, addch, move, scrollok, everything.
    raw=False  fn(ui) is called once per frame; return False to exit.

    cols, rows      the window size. It is set exactly, then pinned there.
    lock            remove the resize border, maximize box, scrollbars and the
                    system-menu Size/Maximize entries; a resize that slips
                    through anyway is snapped back on the next key read
    legacy_console  Windows: open the popup through conhost.exe, whose window
                    can actually be pinned, rather than Windows Terminal
    min_cols/rows   frame mode only: below this, show a "too small" notice
    tick_ms         frame mode only: idle frame interval in milliseconds
    popup           False runs in the current terminal, which is easier to
                    debug; that terminal's size and style are restored on exit
    keep_open       wait for Enter before closing, so tracebacks stay readable
    settle          seconds to let the resize land before locking the window

    Works bare or with arguments:

        @curses_app
        @curses_app(cols=100, rows=30)

    The result can be called directly, or handed to curses.wrapper() -- given a
    live stdscr it reuses that session instead of starting a second one, so
    wrapping it twice is harmless.
    """
    if func is not None:
        return curses_app(cols=cols, rows=rows, raw=raw, min_cols=min_cols,
                          min_rows=min_rows, tick_ms=tick_ms, popup=popup,
                          keep_open=keep_open, lock=lock,
                          legacy_console=legacy_console, settle=settle)(func)

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # curses.wrapper(decorated) hands us a live stdscr as the first
            # argument. Take it and reuse that session -- starting a second
            # curses session on top of a running one is what breaks.
            stdscr = None
            if args and _is_curses_window(args[0]):
                stdscr, args = args[0], args[1:]
            live = stdscr is not None

            in_popup = os.environ.get(_CHILD_FLAG) == "1"

            if popup and not in_popup:
                _end_curses()
                print(f"Opening {cols}x{rows} terminal window...")
                _relaunch(legacy_console)
                return None

            guard = SizeGuard(cols, rows, lock=lock, restore=not in_popup)
            guard.apply(quiet=live, sync=live)
            if lock:
                time.sleep(settle)      # let the resize land before locking
                guard.apply(quiet=live, sync=live)

            if raw:
                loop = _raw_loop
                loop_args = (cols, rows, guard, args, kwargs)
            else:
                loop = _frame_loop
                loop_args = (cols, rows, min_cols, min_rows, tick_ms, guard,
                             args, kwargs)

            result = None
            try:
                if live:
                    result = loop(stdscr, fn, *loop_args)
                else:
                    result = curses.wrapper(loop, fn, *loop_args)
            except KeyboardInterrupt:
                pass
            except Exception:
                # curses.wrapper has already restored the terminal, so the
                # traceback prints legibly.
                _end_curses()
                traceback.print_exc()
            finally:
                guard.release()

            if in_popup and keep_open:
                try:
                    input("\nPress Enter to close this window...")
                except (EOFError, KeyboardInterrupt):
                    pass
            return result

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    @curses_app(cols=100, rows=30)
    def main(window):
        window.addstr(1, 2, "fixed 100 x 30 window", curses.A_BOLD)
        window.addstr(3, 2, "the border cannot be dragged, the maximize "
                            "button is gone,")
        window.addstr(4, 2, "and any resize that gets through is snapped back")
        window.addstr(6, 2, "type below; Enter or Esc quits")
        window.move(8, 2)
        curses.curs_set(1)

        while True:
            ch = window.getch()
            if ch in (ord("\n"), 27):
                break
            if 32 <= ch < 127:
                window.addch(ch)

    main()
