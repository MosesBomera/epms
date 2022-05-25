from flask import redirect, session
from functools import wraps

def logged_in(f):
    """Checks if the current user is logged."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapped

def read_sensor_logs(
    log_path: "The path to the log file"
):
    # Read file.
    with open(log_path, 'r') as reader:
        text = reader.readlines()
    return float(text[0].split()[-1])