# IMPORTS
from dotenv import load_dotenv
import os
load_dotenv()

from flask import Flask, jsonify
import jwt
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
@app.route('/sign-token', methods=['GET'])
def sign_token():
  user = {
    "id": 1,
    "username": "TEST",
    "password": "test"
  }
  token = jwt.encode(user, os.getenv('JWT_SECRET'), algorithm="HS256")
  return jsonify({"token": token})

@app.route('/auth/login', methods=['POST'])
def login():
  return jsonify({"message": "Login route reached."})


# ROUTES
@app.route('/')
def index():
  return "Hello, world!"

# SERVER HANDLER
app.run()


