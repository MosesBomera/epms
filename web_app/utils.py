from functools import wraps
from flask import redirect, session, url_for

def logged_in(f):
    """
    Checks if the current user is logged.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapped

def read_sensor_logs(
    log_path
):
    """
    Reads a sensor log file at te log_path. 

    Parameters
    ----------
    log_path
        The path/to the sensor log file.
    
    Returns
    -------
    value
        A float value of the sensor reading.
    """
    # Read file.
    with open(log_path, 'r') as reader:
        text = reader.readlines()
    return round(float(text[0].split()[-1]), 2)