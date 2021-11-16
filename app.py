# Import Dependencies
from flask import Flask, render_template, redirect, url_for, request
import numpy as np
import re
from sqlalchemy import create_engine
import psycopg2
from config import db_password
import time


#################################################
# START Flask Setup
#################################################

app = Flask(__name__)

# Define Flask Routes

@app.route("/")

def index():
    return render_template("index.html")

#@app.route("/testDBConnection")

#def testDBConnection():  
    # Connect data to SQL - postgreSQL
#    db_string = f'postgresql://postgres:{db_password}@127.0.0.1:5432/MoviesRecommendationDB'
#    engine=create_engine(db_string)
#    print(engine)
#    return redirect('/', code=302)

#@app.route("/recommendation", methods = ['POST'])

#def recommendation():
#   print("input is here")
#   result = request.form
#   print(request.form)
   #Here once we decide connecting to the DB or giving input directly to the model for getting the recommendations
#   return redirect('/', code=302)

#################################################
# END Flask Setup
#################################################

# main behavior
if __name__ == "__main__":
   #app.run()
   app.run(debug=True)
