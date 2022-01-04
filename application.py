from flask import Flask, json, redirect, render_template, session, request, g
from flask_session import Session
from tempfile import mkdtemp
from functions import run_db, login_required, validate_fields, validate_file, br_currency
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
import pycep_correios
import os
import locale
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF8')

USER_FILES = "static/users/"

# Configure application
app = Flask(__name__)

app.config["USER_FILES"] = USER_FILES
app.config["MAX_CONTENT_LENGTH"] = 2 * 1000 * 1000

# Database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
Session(app)


@app.route("/")
def index():
    """Main page"""

    # Search form with get method
    if request.args:
        if request.args["state_search"] == '':
            return render_template("index.html", rv="state_search"), 400
        if request.args["city_search"] == '':
            return render_template("index.html", rv="city_search"), 400

        # Get searched professionals from database
        get_professionals = run_db("SELECT professionals.id, email, name, phone, picture, professionals.description, cats.description AS category FROM professionals JOIN users ON professionals.user_id = users.id JOIN cats ON professionals.cat_id = cats.id WHERE city = ? AND state = ? AND name LIKE ? ORDER BY users.id", [request.args["city_search"], request.args["state_search"], f"%{request.args['name_search']}%"])

        if get_professionals:
            return render_template("index.html", results=get_professionals)
        else:
           return render_template("index.html", results="not found")


    return render_template("index.html")


@app.route("/profissionais/<id>/<name>")
def show_profile(id, name):
    """Individual profile page"""

    # Get profile info from database
    get_profile = run_db("SELECT professionals.id, email, name, phone, picture, professionals.description AS description, cats.description AS category FROM professionals JOIN users ON professionals.user_id = users.id JOIN cats ON professionals.cat_id = cats.id WHERE professionals.id = ?", [id])[0]

    # Get profile dishes from database
    get_dishes = run_db("SELECT professionals.id, dish, type, image, dishes.description, ingredients, price FROM dishes JOIN professionals ON dishes.user_id = professionals.user_id JOIN types ON dishes.type_id = types.id WHERE professionals.id = ?", [id])

    # Get profile menus from database
    get_menus = run_db("SELECT menus.id, menu, menus.description AS menu_description, entry, entry_dish_id, main, main_dish_id, dessert, dessert_dish_id, price FROM (SELECT menu_id, dish AS entry FROM dishes_m JOIN dishes ON dishes_m.dish_id = dishes.id WHERE type_id = 1) t1 JOIN (SELECT menu_id, dish AS main FROM dishes_m JOIN dishes ON dishes_m.dish_id = dishes.id WHERE type_id = 2) t2 ON t1.menu_id = t2.menu_id JOIN (SELECT menu_id, dish AS dessert FROM dishes_m JOIN dishes ON dishes_m.dish_id = dishes.id WHERE type_id = 3) t3 ON t2.menu_id = t3.menu_id JOIN menus ON t3.menu_id = menus.id JOIN professionals ON menus.user_id = professionals.user_id WHERE professionals.id = ?", [id])

    return render_template("professional_profile.html", professional_profile=get_profile, professional_dishes=get_dishes, professional_menus=get_menus, br_currency=br_currency)


@app.route("/cadastro", methods=["GET", "POST"])
def register():
    """Register user"""

    # Route accessed via form submitting
    if request.method == "POST":

        # Validate form
        rv = validate_fields(request.form)
        if run_db("SELECT email FROM users WHERE email = ?", [request.form["email_login"]]):
            rv["email_login"] = "invalid"

        if request.form["password_login"] == request.form["confirmation"]:
            rv["confirmation"] = "valid"

        for item in rv:
            if rv[item] == "invalid":
                 return render_template("register.html", rv=item), 400
        
        # Generate password hash
        hash = generate_password_hash(request.form["password_login"], method='pbkdf2:sha256', salt_length=16)
        
        # Insert user into database
        run_db("INSERT INTO users (email, hash) VALUES (?, ?)", [request.form["email_login"], hash])
       
        return login()
            
    # Route accessed via link or url
    else:
        if session:
            session.clear()
        return render_template("register.html", rv=None)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Route accessed via form submitting
    if request.method == "POST":
        
        # Check login info
        get_login = run_db("SELECT * FROM users WHERE email = ?", [request.form["email_login"]])
        if get_login == None:
            return render_template("login.html", rv="invalid"), 400
        else:
            check_password = check_password_hash(get_login[0]["hash"], request.form["password_login"])
            if check_password == False:
                return render_template("login.html", rv="invalid"), 400

        # Start session variables
        session["user_id"] = get_login[0]["id"]
        session["email"] = get_login[0]["email"]
        session["cats"] = run_db("SELECT * FROM cats")
        user_profile = run_db("SELECT * FROM professionals WHERE user_id = ?", [session["user_id"]])
        if user_profile:
            session["profile_created"] = True
            session["user_profile"] = user_profile[0]
        else:
            session["profile_created"] = False
            session["user_profile"] = None

        return redirect("/")

    # Route accessed via link or url
    else:
        if session:
            session.clear()
        return render_template("login.html", rv=None)

@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")

@app.route("/perfil", methods=["GET", "POST"])
@login_required
def profile():
    """Create user profile"""

    # Route accessed via form submitting
    if request.method == "POST":

        # Validate form
        rv = validate_fields(request.form)
        if len(request.form["description_profile"]) <= 1000:
            rv["description_profile"] = "valid"

        category = run_db("SELECT id FROM cats WHERE id = ?", [request.form["category_profile"]])
        if category:
            rv["category_profile"] = "valid"

        check_file = validate_file(request.files["file_profile"])
        if check_file == "valid" or check_file == "invalid":
            rv["file_profile"] = check_file
        
        try:
            get_location = pycep_correios.get_address_from_cep(request.form["zipcode_profile"])
        except:
            rv["zipcode_profile"] = "invalid"

        for item in rv:
            if rv[item] == "invalid":
                return render_template("profile.html", rv=item, cats=session["cats"]), 400

        if check_file == "valid":
            filepath = ""
        else:
            filepath = app.config["USER_FILES"] + "profile_pic/"  + check_file[1]
            check_file[0].save(os.path.join(filepath))
        
        # Get location from zipcode

        # Insert profile into database
        run_db("INSERT INTO professionals (user_id, cat_id, name, phone, zipcode, state, city, description, picture) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [session["user_id"], category[0]["id"], request.form["name_profile"].upper(), request.form["phone_profile"], request.form["zipcode_profile"], get_location["uf"], get_location["cidade"], request.form["description_profile"], filepath])

        session["profile_created"] = True
        session["user_profile"] = run_db("SELECT * FROM professionals WHERE user_id = ?", [session["user_id"]])[0]
        
        # Redirect user to the next page
        return redirect("/pratos")

    # Route accessed via link or url   
    else:
        if session["profile_created"]:
            return render_template("403.html"), 403
        else:
            return render_template("profile.html", rv=None, cats=session["cats"])

@app.route("/atualizar-dados", methods=["GET","POST"])
@login_required
def update_user_data():
    """Update or delete user data"""

    # Route accessed via form submitting
    if request.method == "POST":

        # Validate args
        if request.args:
            try:
                request_id = int(list(request.args.values())[0])
                item_name = list(request.args.keys())[0]
                if (item_name != "deletar_usuario" and item_name != "deletar_perfil") or request_id != 1:
                    return render_template("user_data.html", rv="request_error", cats=session["cats"], user_profile=session["user_profile"]), 400
            except:
                return render_template("user_data.html", rv="request_error", cats=session["cats"], user_profile=session["user_profile"]), 400

            # Delete user account or profile
            get_password_hash = run_db("SELECT hash FROM users WHERE id = ?", [session["user_id"]])[0]["hash"]
            check_password = check_password_hash(get_password_hash, request.form["password_delete"])

            if check_password:
                if session["profile_created"]:
                    run_db("DELETE FROM professionals WHERE user_id = ?", [session["user_id"]])
                    run_db("DELETE FROM dishes_m WHERE dish_id IN (SELECT id FROM dishes WHERE user_id = ?)", [session["user_id"]])
                    run_db("DELETE FROM dishes WHERE user_id = ?", [session["user_id"]])
                    run_db("DELETE FROM menus WHERE user_id = ?", [session["user_id"]])
                if item_name == "deletar_usuario":
                    run_db("DELETE FROM users WHERE id = ?", [session["user_id"]])
                    session.clear()
                    return redirect("/login")
                elif item_name == "deletar_perfil":
                    session["profile_created"] = False
                    session["user_profile"] = None
                    return render_template("user_data.html", rv=None, cats=session["cats"], user_profile=session["user_profile"])
            else:

                if item_name == "deletar_usuario":
                    rv = "password_delete_user"
                elif item_name == "deletar_perfil":
                    rv = "password_delete_profile"

                return render_template("user_data.html", rv=rv, cats=session["cats"], user_profile=session["user_profile"]), 400

        else:
            # Validate form
            rv = validate_fields(request.form)
            if request.form.get("password"):
                if request.form["confirmation"] == request.form["password"]:
                    rv["confirmation"] = "valid"

                for item in rv:
                    if rv[item] == "invalid":
                        return render_template("user_data.html", rv=item, cats=session["cats"], user_profile=session["user_profile"])
                
                # Generate password hash
                hash = generate_password_hash(request.form["password"], method='pbkdf2:sha256', salt_length=16)

                # Update password hash in database
                run_db("UPDATE users SET hash = ? WHERE id = ?", [hash, session["user_id"]])

                return redirect("/atualizar-dados")

            else:
                # Validate form
                if len(request.form["description_update"]) <= 1000:
                    rv["description_update"] = "valid"

                category = run_db("SELECT id FROM cats WHERE id = ?", [request.form["category_update"]])
                if category:
                    rv["category_update"] = "valid"

                check_file = validate_file(request.files["file_update"])
                if check_file == "valid" or check_file == "invalid":
                    rv["file_update"] = check_file

                try:
                    get_location = pycep_correios.get_address_from_cep(request.form["zipcode_update"])
                except:
                    rv["zipcode_update"] = "invalid"
            
                for item in rv:
                    if rv[item] == "invalid":
                        return render_template("user_data.html", rv=item, cats=session["cats"], user_profile=session["user_profile"]), 400

                if check_file == "valid":
                    filepath = ""
                else:
                    filepath = app.config["USER_FILES"] + "profile_pic/"  + check_file[1]
                    check_file[0].save(os.path.join(filepath))

                # Get profile picture
                get_file = run_db("SELECT picture FROM professionals WHERE user_id = ?", [session["user_id"]])[0]["picture"]
                if filepath != "":
                    if get_file:
                        if os.path.exists(get_file):
                            os.remove(get_file)
                else:
                    filepath = get_file

                # Update user profile
                run_db("UPDATE professionals SET cat_id = ?, name = ?, phone = ?, zipcode = ?, state = ?, city = ?, description = ?, picture = ? WHERE user_id = ?", [request.form["category_update"], request.form["name_update"], request.form["phone_update"], request.form["zipcode_update"], get_location["uf"], get_location["cidade"], request.form["description_update"], filepath, session["user_id"]])
                
                session["user_profile"] = run_db("SELECT * FROM professionals WHERE user_id = ?", [session["user_id"]])[0]
                return redirect("/atualizar-dados")

    # Route accessed via link or url
    else:
        return render_template("user_data.html", rv=None, cats=session["cats"], user_profile=session["user_profile"])


@app.route("/pratos", methods=["GET", "POST"])
@login_required
def dishes():
    """Dishes and menus forms"""

    # Get profile dishes from database and store in session
    session["dishes"] = run_db("SELECT dishes.id, dish, image, type, type_id, dishes.description, ingredients, dishes.price FROM dishes JOIN types ON dishes.type_id = types.id WHERE dishes.user_id = ?", [session["user_id"]])

    # Get profile menus from database and store in session
    session["menus"] = run_db("SELECT menus.id, menu, description, entry, entry_dish_id, main, main_dish_id, dessert, dessert_dish_id, price FROM (SELECT menu_id, dish AS entry FROM dishes_m JOIN dishes ON dishes_m.dish_id = dishes.id WHERE type_id = 1) t1 JOIN (SELECT menu_id, dish AS main FROM dishes_m JOIN dishes ON dishes_m.dish_id = dishes.id WHERE type_id = 2) t2 ON t1.menu_id = t2.menu_id JOIN (SELECT menu_id, dish AS dessert FROM dishes_m JOIN dishes ON dishes_m.dish_id = dishes.id WHERE type_id = 3) t3 ON t2.menu_id = t3.menu_id JOIN menus ON t3.menu_id = menus.id WHERE menus.user_id = ?", [session["user_id"]])

    # Get types of dishes from database and store in session
    session["types"] = run_db("SELECT * FROM types")

    # Get dishes that belongs to menus from database and store in session
    session["menus_list"] = run_db("SELECT dish_id, menu_id, menu FROM dishes_m JOIN menus ON dishes_m.menu_id = menus.id")

    # Route accessed via form submitting
    if request.method == "POST":

        # Validate args
        try:
            request_id = int(list(request.args.values())[0])
            item_name = list(request.args.keys())[0].split("_")[-1]
        except:
            return render_template("dishes.html", menus_list=session["menus_list"], dishes=session["dishes"], menus=session["menus"], types=session["types"], rv="request_error", br_currency=br_currency, form_err={}), 400
        
        # Update, insert and delete dishes
        if item_name == "prato":
            if request.args.get("deletar_prato"):
                for row in session["menus_list"]:
                    if row["dish_id"] == request_id:
                        return render_template("dishes.html", menus_list=session["menus_list"], dishes=session["dishes"], menus=session["menus"], types=session["types"], rv="menu_exists", br_currency=br_currency, form_err=request.args), 400

                for row in session["dishes"]:
                    if request_id == row["id"]:
                        get_file = row["image"]

                if os.path.exists(get_file):
                    os.remove(get_file)

                # Delete dishes
                run_db("DELETE FROM dishes WHERE id = ? AND user_id = ?", [request.args["deletar_prato"], session["user_id"]])
                return redirect("/pratos")
            else:
                # Validate form
                rv = validate_fields(request.form)
                if len(request.form["description_dish"]) <= 250:
                    rv["description_dish"] = "valid"
                
                dish_type = run_db("SELECT id FROM types WHERE id = ?", request.form["type_dish"])
                if dish_type:
                    rv["type_dish"] = "valid"

                ingredients = request.form["name_ingredients_dish"].lower()
                if ingredients and len(ingredients.split("_")) > 12:
                    rv["name_ingredients_dish"] = "invalid"

                # Convert price to float
                try:
                    price = locale.atof(request.form["price_dish"])
                    if price == 0:
                        rv["price_dish"] = "invalid"
                except:
                    rv["price_dish"] = "invalid"

                check_file = validate_file(request.files["file_dish"])
                if check_file == "valid" or check_file == "invalid":
                    rv["file_dish"] = check_file
                
                for item in rv:
                    if rv[item] == "invalid":
                        return render_template("dishes.html", menus_list=session["menus_list"], dishes=session["dishes"], menus=session["menus"], types=session["types"], rv=item, br_currency=br_currency, form_err=request.args), 400
                    
                if check_file == "valid":
                    filepath = ""
                else:
                    filepath = app.config["USER_FILES"] + "dishes_img/"  + check_file[1]
                    check_file[0].save(os.path.join(filepath))

                if request.args.get("adicionar_prato"):
                    # Insert dish into database
                    run_db("INSERT INTO dishes (user_id, type_id, dish, image, description, ingredients, price) VALUES (?, ?, ?, ?, ?, ?, ?)", [session["user_id"], request.form["type_dish"], request.form["name_dish"], filepath, request.form["description_dish"], ingredients, price])
                elif request.args.get("atualizar_prato"):

                    for row in session["dishes"]:
                        if request_id == row["id"]:
                            get_file = row["image"]
                            menu_exists = run_db("SELECT menu_id FROM dishes_m WHERE dish_id = ? LIMIT 1", [request_id])
                            if dish_type[0]["id"] != row["type_id"] and menu_exists:
                                return render_template("dishes.html", menus_list=session["menus_list"], dishes=session["dishes"], menus=session["menus"], types=session["types"], rv="type_menu_exists", br_currency=br_currency, form_err=request.args), 400

                    if filepath != "":
                        if os.path.exists(get_file):
                            os.remove(get_file)
                    else:
                        filepath = get_file

                    # Update dish data
                    run_db("UPDATE dishes SET type_id = ?, dish = ?, image = ?, description = ?, ingredients = ?, price = ? WHERE id = ? AND user_id = ?", [request.form["type_dish"], request.form["name_dish"], filepath, request.form["description_dish"], request.form["name_ingredients_dish"], price, request.args["atualizar_prato"], session["user_id"]])

                return redirect("/pratos") 

        # Update, insert and delete menus   
        elif item_name == "menu":
            if request.args.get("deletar_menu"):

                dishes_list = list(run_db("SELECT entry_dish_id, main_dish_id, dessert_dish_id FROM menus WHERE id = ? AND user_id = ?", [request.args["deletar_menu"], session["user_id"]])[0].values())

                dishes_list.append(request.args["deletar_menu"])
                
                # Delete menu
                run_db("DELETE FROM dishes_m WHERE dish_id IN (?, ?, ?) AND menu_id = ?", dishes_list)
                run_db("DELETE FROM menus WHERE id = ? AND user_id = ?", [request.args["deletar_menu"], session["user_id"]])

                return redirect("/pratos")
            else:
                
                # Validate form
                rv = validate_fields(request.form)
                if len(request.form["description_menu"]) <= 250:
                    rv["description_menu"] = "valid"

                # Validate dishes
                check_entry = run_db("SELECT id FROM dishes WHERE id = ? AND type_id = ? AND user_id = ?", [request.form["entry_menu"], 1, session["user_id"]])
                check_main = run_db("SELECT id FROM dishes WHERE id = ? AND type_id = ? AND user_id = ?", [request.form["main_menu"], 2, session["user_id"]])
                check_dessert = run_db("SELECT id FROM dishes WHERE id = ? AND type_id = ? AND user_id = ?", [request.form["dessert_menu"], 3, session["user_id"]])

                if check_entry:
                    rv["entry_menu"] = "valid"
                if check_main:
                    rv["main_menu"] = "valid"
                if check_dessert:
                    rv["dessert_menu"] = "valid"

                # Convert price to float
                try:
                    price = locale.atof(request.form["price_menu"])
                    if price == 0:
                        rv["price_menu"] = "invalid"
                except:
                    rv["price_menu"] = "invalid"

                for item in rv:
                    if rv[item] == "invalid":
                        return render_template("dishes.html", menus_list=session["menus_list"], dishes=session["dishes"], menus=session["menus"], types=session["types"], rv=item, br_currency=br_currency, form_err=request.args), 400

                if request.args.get("adicionar_menu"):
                    # Insert menu and dishes into database
                    run_db("INSERT INTO menus (user_id, entry_dish_id, main_dish_id, dessert_dish_id, menu, description, price) VALUES (?, ?, ?, ?, ?, ?, ?)", [session["user_id"], request.form["entry_menu"], request.form["main_menu"], request.form["dessert_menu"], request.form["name_menu"], request.form["description_menu"], request.form["price_menu"]])

                    get_last_menu = run_db("SELECT id FROM menus WHERE user_id = ? ORDER BY id DESC LIMIT 1", [session["user_id"]])[0]["id"]

                    # Insert menu and dishes into database
                    run_db("INSERT INTO dishes_m (dish_id, menu_id) VALUES (?, ?), (?, ?), (?, ?)", [request.form["entry_menu"], get_last_menu, request.form["main_menu"], get_last_menu, request.form["dessert_menu"], get_last_menu])

                elif request.args.get("atualizar_menu"):

                    current_dishes = run_db("SELECT entry_dish_id, main_dish_id, dessert_dish_id FROM menus WHERE id = ? AND user_id = ?", [request.args["atualizar_menu"], session["user_id"]])[0]

                    if request.form["entry_menu"] != current_dishes["entry_dish_id"]:
                        # Update entry dishes that belongs to menus
                        run_db("UPDATE dishes_m SET dish_id = ? WHERE menu_id = ? AND dish_id = ?", [request.form["entry_menu"], request.args["atualizar_menu"], current_dishes["entry_dish_id"]])
                    if request.form["main_menu"] != current_dishes["main_dish_id"]:
                        # Update main dishes that belongs to menus
                        run_db("UPDATE dishes_m SET dish_id = ? WHERE menu_id = ? AND dish_id = ?", [request.form["main_menu"], request.args["atualizar_menu"], current_dishes["main_dish_id"]])
                    if request.form["dessert_menu"] != current_dishes["dessert_dish_id"]:
                        # Update dessert dishes that belongs to menus
                        run_db("UPDATE dishes_m SET dish_id = ? WHERE menu_id = ? AND dish_id = ?", [request.form["dessert_menu"], request.args["atualizar_menu"], current_dishes["dessert_dish_id"]])

                    # Update menus
                    run_db("UPDATE menus SET menu = ?, description = ?, entry_dish_id = ?, main_dish_id = ?, dessert_dish_id = ?, price = ? WHERE id = ? AND user_id = ?", [request.form["name_menu"], request.form["description_menu"], request.form["entry_menu"], request.form["main_menu"], request.form["dessert_menu"], price, request.args["atualizar_menu"], session["user_id"]])

        # Redirect user after completing the submit
        return redirect("/pratos")
    
    # Route accessed via link or url
    else:
        if session["profile_created"]:
            return render_template("dishes.html", menus_list=session["menus_list"], dishes=session["dishes"], menus=session["menus"], types=session["types"], rv=None, br_currency=br_currency, form_err={})
        else:
            return render_template("403.html"), 403


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""

    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description
    })
    response.content_type = "application/json"

    if e.code == 413:
        session["invalid"] = e.code
        if request.url.split("/")[-1] == "perfil":
            # Create profile file too large
            return render_template("profile.html", rv=e.code, cats=session["cats"]), e.code
        elif request.url.split("/")[-1] == "atualizar-dados":
            # Update profile file too large
            return render_template("user_data.html", rv=e.code, cats=session["cats"], user_profile=session["user_profile"]), e.code
        else:
            # Dishes file too large
            return render_template("dishes.html", dishes=session["dishes"], menus=session["menus"], types=session["types"], rv=e.code, br_currency=br_currency, form_err=request.args), e.code
    else:
        return e