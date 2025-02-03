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
    database="whisky_journal_db"
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
    new_whisky["user_id"] = g.user.get("payload")["id"]
    print(g.user.get("payload")["id"])
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
                   INSERT INTO whiskies (name, distillery, image, type, origin, age, flavor, hue, alcohol_content, notes, user_id )
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *;
                   """,
                   (new_whisky["name"], new_whisky["distillery"], new_whisky["image"], new_whisky["type"], new_whisky["origin"], new_whisky["age"], new_whisky["flavor"],new_whisky["hue"], new_whisky["alcohol_content"], new_whisky["notes"], new_whisky['user_id'])
                   )
    created_whisky = cursor.fetchone()
    connection.commit()
    connection.close()
    return jsonify({"whisky": created_whisky}), 201
  except Exception as err:
    return jsonify({"err": err}), 500

@app.route('/whiskies', methods=['GET'])
@token_required  
def whiskies_index():
  try:
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
                  SELECT whiskies.name, whiskies.distillery, whiskies.image, whiskies.type, whiskies.origin, whiskies.age, whiskies.flavor, whiskies.hue, whiskies.alcohol_content, whiskies.notes, whiskies.user_id
                  FROM whiskies INNER JOIN users
                  ON whiskies.user_id = users.id;
                  """)
    
    whiskies = cursor.fetchall()
    connection.commit()
    connection.close()
    return jsonify({"whiskies": whiskies}), 200
  except Exception as err:
    return jsonify({"err": err.message}), 500
  
@app.route('/whiskies/<whisky_id>', methods=['GET'])
@token_required 
def show_whisky(whisky_id):
  try:
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
                  SELECT whiskies.name, whiskies.distillery, whiskies.image, whiskies.type, whiskies.origin, whiskies.age, whiskies.flavor, whiskies.hue, whiskies.alcohol_content, whiskies.notes
                  FROM whiskies INNER JOIN users
                  ON whiskies.user_id = users.id
                  WHERE whiskies.id = %s;""", 
                  (whisky_id,))

    whisky = cursor.fetchone()
    if whisky is None:
      connection.close()
      return "Whisky Not Found", 404
    connection.close()
    return jsonify({"whisky": whisky}), 200
  except Exception as err:
    return jsonify({"err": err.message}), 500


@app.route('/whiskies/<whisky_id>', methods=['PUT'])
@token_required
def update_whisky(whisky_id):
  try:
    updated_whisky_data = request.json
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM whiskies WHERE whiskies.id = %s;", (whisky_id,))
    whisky_to_update = cursor.fetchone()
    if whisky_to_update is None:
      return jsonify({"err": "Whisky Not Found"}), 404
    connection.commit()
    if whisky_to_update["user_id"] is not g.user.get("id"):
      return jsonify({"err:" "Unauthorized"}), 401
    cursor.execute("""
                  UPDATE whiskies SET name = %s, distillery = %s, image = %s, type = %s, origin = %s, age = %s, flavor = %s, hue = %s, alcohol_content = %s, notes = %s
                  WHERE whiskies.id = %s RETURNING *;""",
                  (updated_whisky_data["name"], updated_whisky_data["distillery"], updated_whisky_data["image"], updated_whisky_data["type"], updated_whisky_data["origin"], updated_whisky_data["age"], updated_whisky_data["flavor"], updated_whisky_data["hue"], updated_whisky_data["alcohol_content"], updated_whisky_data["notes"], whisky_id))
    updated_whisky = cursor.fetchone()
    connection.commit()
    connection.close()
    return jsonify({"whisky": updated_whisky}), 200
  except Exception as err:
    return jsonify({"err": err.message}), 500

@app.route('/whiskies/<whisky_id>', methods=['DELETE'])
@token_required
def delete_whisky(whisky_id):
  try:
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM whiskies WHERE whiskies.id = %s;", (whisky_id,))
    whisky_to_delete = cursor.fetchone()
    if whisky_to_delete is None:
      return jsonify({"err": "Whisky Not Found"}), 404
    connection.commit()
    if whisky_to_delete["user.id"] is not g.user.get("id"):
      return jsonify({"err": "Unauthorized"}), 401
    cursor.execute("DELETE FROM whiskies WHERE whiskies.id = %s;", (whisky_id,))
    connection.commit()
    connection.close()
    return jsonify({"message": "whisky deletion sucessful"}), 200
  except Exception as err:
    return jsonify({"err": err.message}), 500

    
# SERVER HANDLER
app.run()