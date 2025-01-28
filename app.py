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



# ROUTES
@app.route('/')
def index():
  return "Hello, world!"

# SERVER HANDLER
app.run()


