# IMPORTS
from dotenv import load_dotenv
import os
load_dotenv()

from auth_middleware import token_required

from flask import Flask, jsonify, request, g
import jwt
import bcrypt
import psycopg2, psycopg2.extras


# APP & CONFIGURATIONS / INITIALIZING FLASK
app = Flask(__name__)

def get_db_connection():
  connection = psycopg2.connect(
    host="localhost",
    database="whiskies_db"
  )
  return connection


# AUTH ROUTES
@app.route('/auth/sign-up', methods=['POST'])
def sign_up():
  try:
    new_user_data = request.get_json()
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE username = %s or email = %s;", (new_user_data["username"], new_user_data["email"],)) 
    existing_user = cursor.fetchone()
    if existing_user:
      cursor.close()
      return jsonify({"err": "Username is already taken."}), 400
    hashed_password = bcrypt.hashpw(bytes(new_user_data["password"], 'utf-8'), bcrypt.gensalt())
    cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id, username", (new_user_data["username"], new_user_data["email"], hashed_password.decode('utf-8')))
    created_user = cursor.fetchone()
    connection.commit()
    connection.close()
    payload = {"username": created_user["username"], "id": created_user["id"]}
    token = jwt.encode({ "payload": payload }, os.getenv('JWT_SECRET'))
    return jsonify({"token": token, "user": created_user}), 201
  except Exception as err:
    return jsonify({"err": err}), 401


@app.route('/auth/login', methods=['POST'])
def login():
  try:
    login_form_data = request.get_json()
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE username = %s;", (login_form_data["username"],))
    existing_user = cursor.fetchone()
    if existing_user is None:
      return jsonify({"err": "Invalid"}), 401
    password_is_valid = bcrypt.checkpw(bytes(login_form_data["password"], 'utf-8'), bytes(existing_user["password"], 'utf-8'))
    if not password_is_valid:
      return jsonify({"err": "Invalid"}), 401
    payload = {"username": existing_user["username"], "id": existing_user["id"]}
    token = jwt.encode({"payload": payload}, os.getenv('JWT_SECRET'))
    return jsonify({"token": token}), 200
  except Exception as err: 
    return jsonify({"err": err.message}), 500
  finally:
    connection.close

@app.route('/verify-token', methods=['POST'])
def verify_token():
  try:
    token = request.headers.get('Authorization').split(' ')[1]
    decoded_token = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=["HS256"])
    return jsonify({"user: decoded_token"})
  except Exception as err:
    return jsonify({"err": err.message})



# ROUTES
@app.route('/')
def index():
  return "Landing Page"


@app.route('/whiskies', methods=['POST'])
@token_required
def create_whisky():
  try:
    new_whisky = request.json
    new_whisky["users_id"] = g.user["id"]
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
                   INSERT INTO whiskies (users_id, name, distillery, image, type, origin, age, flavor, hue, alcohol_content, notes )
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *
                   """,
                   (new_whisky['users_id'], new_whisky["name"], new_whisky["distillery"], new_whisky["image"], new_whisky["type"], new_whisky["origin"], new_whisky["age"], new_whisky["flavor"], new_whisky["notes"])
                   )
    created_whisky = cursor.fetchone()
    connection.commit()
    connection.close()
    return jsonify({"hoot": created_whisky}), 201
  except Exception as err:
    return jsonify({"err": err}), 500



# SERVER HANDLER
app.run()