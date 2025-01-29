# IMPORTS
from dotenv import load_dotenv
import os
load_dotenv()

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
# @app.route('/sign-token', methods=['GET'])
# def sign_token():
#   user = {
#     "id": 1,
#     "username": "TEST",
#     "password": "test"
#   }
#   token = jwt.encode(user, os.getenv('JWT_SECRET'), algorithm="HS256")
#   return jsonify({"token": token})

@app.route('/auth/sign-up', methods=['POST'])
def sign_up():
  # try:
  #   return jsonify({"message": "Sign up route reached"})
  # except Exception as err:
  #   return jsonify({"err": err.message})
  try:
    new_user_data = request.get_json()
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE username = %s;", (new_user_data["username"],)) 
    existing_user = cursor.fetchone()
    if existing_user:
      cursor.close()
      return jsonify({"err": "Username is already taken."}), 400
    hashed_password = bcrypt.hashpw(bytes(new_user_data["password"], 'utf-8'), bcrypt.gensalt())
    cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (new_user_data["username"], hashed_password.decode('utf-8')))
    created_user = cursor.fetchone()
    connection.commit()
    connection.close()
    return jsonify(created_user), 201
  except Exception as err:
    return jsonify({"err": err}), 401


@app.route('/auth/login', methods=['POST'])
def login():
  try:
    return jsonify({"messege": "Login route reached"})
  except Exception as err:
    return jsonify({"err": err.message})



# ROUTES
@app.route('/')
def index():
  return "Hello, world!"

# SERVER HANDLER
app.run()


