
import os
import sys
import subprocess
import functools

# This decorator runs the decorated function in a new terminal window.
# Same as terminal.run_in_terminal, but re-launches with the *current*
# interpreter (sys.executable) instead of a bare "python" from PATH, so the
# new window uses the same virtualenv (and therefore the same installed
# packages, e.g. windows-curses).

def pop_out_terminal(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # If we're already the process running inside the new terminal,
        # just call the real function and stop here.
        if "--terminal" in sys.argv:
            return func(*args, **kwargs)

        # Otherwise, we're the original process.
        # Find the absolute path to the script that was originally run.
        script = os.path.abspath(sys.argv[0])
        python = sys.executable  # this venv's python, not whatever PATH finds
        print(f"Re-launching {script} in a new terminal window using {python}...")

        # Open a new terminal window and re-run this script inside it,
        # passing --terminal so that next time the "if" above catches it.
        if sys.platform.startswith("win"):
            # Windows: open a new Command Prompt window
            subprocess.Popen(
                f'start "run-in-terminal" cmd /k ""{python}" "{script}" --terminal"',
                shell=True,
            )
        elif sys.platform == "darwin":
            # macOS: open a new Terminal.app window
            subprocess.Popen(["osascript", "-e",
                               f'tell app "Terminal" to do script "\'{python}\' \'{script}\' --terminal"'])
        else:
            # Linux: open a new terminal emulator window
            subprocess.Popen(["x-terminal-emulator", "-e", f"'{python}' '{script}' --terminal"])

    return wrapper
