# IMPORTS
from dotenv import load_dotenv
# import os
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
  return jsonify({"message": "You have authorization!"})


# ROUTES
@app.route('/')
def index():
  return "Hello, world!"

# SERVER HANDLER
app.run()


