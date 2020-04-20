import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

## ROUTES
'''
Public endpoint to get all the drinks
'''
@app.route("/drinks")
def get_drinks():

    # retrieve all the drinks from the database
    drinks_all = Drink.query.order_by(Drink.id).all()

    print(drinks_all)

    # abort 404 if no drinks are found
    if len(drinks_all) == 0:
        abort(404)

    # short format of the drinks
    drinks = [drink.short() for drink in drinks_all]

    # return status code 200 and json file where drinks is the list of drinks
    return jsonify({
        "success": True,
        "drinks": drinks
    })


'''
Endpoint for getting all the drinks with all details
'''
@app.route("/drinks-detail")
@requires_auth("get:drinks-detail")
def get_drinks_detail(payload):

    # retrieve all the drinks from the database
    drinks_all = Drink.query.order_by(Drink.id).all()

    # abort 404 if no drinks are found
    if len(drinks_all) == 0:
        abort(404)

    # long format of the drinks
    drinks = [drink.long() for drink in drinks_all]

    # return status code 200 and json file where drinks is the list of drinks
    return jsonify({
        "success": True,
        "drinks": drinks
    })


'''
Private endpoint to create a new drink
'''
@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def post_drinks(payload):

    # retrieve data fields from the request body
    body = request.get_json()

    new_title = body.get("title", None)
    new_recipe = body.get("recipe", None)

    # abort 422 if any field is blank
    if ((new_title is None) or (new_recipe is None)):
        abort(422)

    # try to add the new data into db
    new_drink = Drink(title=new_title, recipe=json.dumps([new_recipe]))
    try:
        new_drink.insert()
    # abort 422 if any error
    except Exception as e:
        print("Error: ", str(e))
        abort(422)

    # returns status code 200 and json file where drink 
    # is an array containing only the newly created drink
    return jsonify({
        "success": True,
        "drinks": [new_drink.long()]
    })

'''
Endpoint for patching a drink by using its ID
'''
@app.route("/drinks/<int:id>", methods=["PATCH"])
@requires_auth("patch:drinks")
def update_drink(*args, **kwargs):

    # get id from kwargs
    id = kwargs["id"]

    # get drink by a given id
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    # abort 404 if no drink found
    if drink is None:
        abort(404)

    # retrieve data fields from the request body
    body = request.get_json()

    if "title" in body:
        drink.title = body.get("title")

    if "recipe" in body:
        drink.recipe = json.dumps(body.get("recipe"))

    # update new data in db
    try:
        drink.update()
    # abort 422 if any error
    except Exception as e:
        print("Error: ", str(e))
        abort(422)

    # return status code 200
    return jsonify({
        "success": True,
        "drinks": [drink.long()]
    })



'''
Endpoint for deleting a drink using its ID
'''
@app.route("/drinks/<int:id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drink(*args, **kwargs):

    # get id from kwargs
    id = kwargs["id"]

    # get drink by a given id
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    # abort 404 if no drink found
    if drink is None:
        abort(404)

    # deletr data from db
    try:
        drink.delete()
    # abort 422 if any error
    except Exception as e:
        print("Error: ", str(e))
        abort(422)

    # return status code 200
    return jsonify({
        "success": True,
        "delete": id
    })

## Error Handling
'''
Error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

'''
Error handling for Resource Not Found
'''
@app.errorhandler(404)
def resource_not_found(error):
    return jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''
Error handler for AuthError
'''
@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

