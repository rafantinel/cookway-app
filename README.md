# CS50 Final Project - Cookway App

## Video

https://www.youtube.com/watch?v=StS0pmg21k8

## Description

The project is a web app where customers search for gastronomy professionals based on a specific location. Everyone can register and add dishes and menus that they would offer in some kind of professional service.

Technologies used:

- Flask
- JQuery
- SQLite
- Other small libraries or packages

## How the app works?

Users can search for professionals on the main page, with or without registration. If they want to register, they can create a professional profile with personal info and a list of dishes with ingredients or menus with three types of dishes (entry, main and dessert). Registered users can also update or delete every information about their account or professional profile.

### Routing Functions

- index - if the search form is submitted, returns a template with the searched professionals
- show_profile - returns a template with the information about one profile
- register - registers users
- login - logs user in and start session
- logout - logs user out and clear session
- update_user_data - returns a template where user can update or delete his profile or account data
- dishes - returns a template with forms for adding, editing and deleting dishes and menus
- handle_exception - basically handles an exception when user tries to upload a file too large

### Other Functions

- get_db - gets database connection
- run_db - executes queries (returns an array of dictionaries if the application wants to select data)
- login_required - login required decorator (some routes requires user to be logged in)
- allowed_file - returns "True" if the file extension is .jpg, .jpeg, .bmt or .png
- validate_fields - validates form submissions with regular expressions
- validate_file - validates and changes file name with a hash function
- br_currency - formats a float number to local currency style

### Cities and States API (IBGE)

This API from IBGE generates a .json response to find all the states from Brazil and their cities. With  JQuery's getJSON function, a dynamic search form can be easily created using this API.

More about the API on: https://servicodados.ibge.gov.br/api/docs/localidades

### Database Tables

- users - contains users' email and password hash
- cats - profile categories
- types - types of dishes (entry, main and dessert)
- dishes - information about the dishes, like name price and description
- menus - information about the menus, like name price and description
- dishes_m - contains all the dishes that are included in menus
- professionals - information about the created profiles, like phone, name, description and location

## Github Repository

https://github.com/rafantinel/Cookway-App
