from flask import session, abort
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('nivel_conta') != 1:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function