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

- index
- show_profile
- register
- login
- logout
- update_user_data
- dishes
- handle_exception

### Other Functions

- get_db
- run_db
- login_required
- allowed_file
- validate_file
- validate_fields
- validate_file
- br_currency

### Cities and States API (IBGE)

This API from IBGE generates a .json response to find all the states from Brazil and their cities. With  JQuery's getJSON function, a dynamic search from can be easily created using this API.

More about the API on: https://servicodados.ibge.gov.br/api/docs/localidades

### Database Tables

- users
- cats
- types
- dishes
- menus
- dishes_m
- professionals

## Github Repository

https://github.com/rafantinel/Cookway-App