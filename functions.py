from flask import redirect, session, g
from functools import wraps
import re, sqlite3
from hashlib import md5
from time import localtime
from werkzeug.utils import secure_filename
import locale
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF8')

# Database constant
DB = "cook.db"

def get_db():
    """Get database connection"""
    db =  getattr(g, "_database", None)
    if db is None: 
        db = g._database = sqlite3.connect(DB)
    return db

def run_db(query, args=()):
    """Database queries"""
    try:
        cur = get_db().execute(query, args)
    except:
        return None

    if "SELECT" in query and "DELETE" not in query and "INSERT" not in query and "UPDATE" not in query:
        fields = list(map(lambda x: x[0], cur.description))
        fetch = cur.fetchall()
        cur.close()

        if len(fetch) == 0:
            return None

        rv = []
        count = 0
        for i in range(0, len(fetch)):
            rv.append({})
            for item in fetch[i]:
                rv[i][fields[count]] = item
                count += 1
                if count == len(fields):
                    count = 0

        return rv

    else:
        get_db().commit()
        cur.close()
        return


def login_required(f):
    """Decorate routes to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    """Allowed file types"""
    if re.search(".jpg|.jpeg|.bmp|.png$", filename):
        return True
    else:
        return False


def validate_fields(request):
    """Validate form fields with regex"""
    fields = {
        "email": r"^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$",
        "password": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,16}$",
        "name": r"^[\w'\-,.:;!?0-9&#@$+=()_][^¡÷¿/\\%ˆ*{}|~<>[\]]{0,1000}$",
        "phone": r"^[0-9]{11,13}$",
        "zipcode": r"^[0-9]{8}$",
        "price": r"^\d*[.,]?\d*[.,]?\d*[.,]?\d*\d$",
    }

    rv = {}
    for name in request:
        temp_name = name.split("_")[0]
        try:
            pattern = re.compile(fields[temp_name])
            if re.fullmatch(pattern, request[name]):
               rv[name] = "valid"
            else:
                rv[name] = "invalid"
        except:
            rv[name] = "invalid"

    return rv

def validate_file(file):
    """Validate and set file name"""
    if file.filename == "":
        return "valid"
    elif file and allowed_file(file.filename):
        extension = "." + file.filename.split(".")[1]
        file.filename = md5(str(localtime()).encode('utf-8')).hexdigest() + extension
        filename = secure_filename(file.filename)
        return [file, filename]
    else:
        return "invalid"


def br_currency(value):
    """Convert float to local currency format"""
    return locale.currency(value)




