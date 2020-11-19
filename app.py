import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect

from flask import Flask, jsonify
import datetime as dt

# Setup for the Hawaii database

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

 #automap base to reflect database in a model
Base = automap_base()

# fetch tables 
Base.prepare(engine, reflect=True)

# Save reference to the table
measurement = Base.classes.measurement
station = Base.classes.station

app = Flask(__name__)

@app.route("/")
def home():
    # List all available API Routes.
    return"""<html>
    <h1 align =Left> Hawaii API Routes</h1>

    <br><br><br>
    <ul>
   
    <li>
    Return a list of precipitations from last year:
       <a href="/api/v1.0/precipitation">/api/v1.0/precipitation</a>
    </li>
    <br><br><br><br>
    <li>
    Return a JSON list of stations from the dataset: 
    <br>
   <a href="/api/v1.0/stations">/api/v1.0/stations</a>
   </li>
   <br><br><br><br>
    <li>
    Return a JSON list of Temperature Observations (tobs) , date observations of the most active station for the last year of data.
    <br>
    <a href="/api/v1.0/tobs">/api/v1.0/tobs</a>
    </li>
    <br>
    <br><br><br>
    <li>
    Return a JSON list of tmin, tmax, tavg for the dates greater than or equal to the date provided:
    <br>Replace &ltstart&gt with a date in YYYY-MM-DD format.
    <br>
    eg:
    <a href="/api/v1.0/2017-08-07">/api/v1.0/2017-08-07</a>
    </li>
    <br>
    <br><br><br>
    <li>
    Return a JSON list of tmin, tmax, tavg for the dates in range of start date and end date inclusive:
    <br>
    Replace &ltstart&gt and &ltend&gt with a date in YYYY-MM-DD/YYYY-MM-DD format. 
    <br>
    <br>
    eg:
    <a href="/api/v1.0/2016-03-01/2017-07-01">/api/v1.0/2016-03-01/2017-07-01</a>
    </li>
    <br>
    </ul>
    </html>
    """

# Convert the query results to a dictionary using date as the key and prcp as the value.

@app.route("/api/v1.0/precipitation")

def precipitation():
    # Create  session
    session = Session(engine)
    most_current_date = session.query(measurement.date).order_by(measurement.date.desc()).first()
    most_current_date = str(most_current_date)[2:-3]
    # Calculate the date 1 year ago from the last data point in the database

    last_12mnth = str(eval(most_current_date[0:4])-1) + most_current_date[4:]

    # Perform a query to retrieve the data and precipitation scores
    query = session.query(measurement.date, measurement.prcp).filter(measurement.date >= last_12mnth).all()

    last_12mnth_dict = dict(query)
    session.close()

    return jsonify(last_12mnth_dict)

#Return a JSON list of stations from the dataset.
@app.route("/api/v1.0/stations")
def stations(): 
    # Docstring
    """Return a JSON list of stations from the dataset."""
    session = Session(engine)

    # Query stations

    stations_query =  session.query(measurement.station).group_by(measurement.station).all()

    # Convert list of tuples into normal list
    stations_query_dict = list(np.ravel(stations_query))
    session.close()

    return jsonify(stations_query_dict)

#Query the dates and temperature observations of the most active station for the last year of data.
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)

    act_stn = session.query(measurement.station, func.count(measurement.station)).group_by(measurement.station).order_by(func.count(measurement.station).desc()).first()
    most_active_station = act_stn[0]

    print (most_active_station)
    most_current_date = session.query(measurement.date).order_by(measurement.date.desc()).first()
    most_current_date = str(most_current_date)[2:-3]
    # Calculate the date 1 year ago from the last data point in the database

    last_12mnth = str(eval(most_current_date[0:4])-1) + most_current_date[4:]

    #results_tobs = session.query(Measurement.date, Measurement.tobs).filter(Measurement.date >= last_12mnth).all()
    last_12tobs_query = session.query(measurement.tobs, measurement.date).filter(measurement.date > last_12mnth).filter(measurement.station == most_active_station).all()
    print(last_12tobs_query)
    last_12tobs =[]
    for varx in last_12tobs_query:
            last_12tobs_dict = {}
            last_12tobs_dict["tobs"] = varx[0]
            last_12tobs_dict["date"] = varx[1]
            last_12tobs.append(last_12tobs_dict) 

    var_dict = {
        "most active station" : most_active_station,
        "observations" :last_12tobs
    }
    session.close()

    return jsonify(var_dict)

  
@app.route("/api/v1.0/<start>")
def start(start=None):
    session = Session(engine)
    start_dt =start

    #Return a JSON list of tmin, tmax, tavg for all dates greater than and equal to the start date.


    # Check if the date entered is a valid date or not
    # future devlopment convert this checking of a valid date into a separate function/or a custom library
    try :
        year,month,day =start_dt.split('-')
    except ValueError :
        #    " Invalid Date format"
        print ("Input date is not valid..")
        return"""<html>
            <br><br><br>
            Please enter a valid  Start Date as in 'YYYY-MM-DD/YYYY-MM-DD' format
            <br><br>
            <a href="http://localhost:5000/">Go back to the Hawaii API Routes Main Page</a>
            </html>
            """

    isValidDate = True
    try :
        dt.datetime(int(year),int(month),int(day))
    except ValueError :
        isValidDate = False

    if(isValidDate) :
       # print ("Input date is valid ..")
        from_start = session.query(measurement.date, func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).filter(measurement.date >= start_dt).all()
        start_list = []
        
        for vary in from_start:
            start_dict = {}
            start_dict["min"] = vary[1]
            start_dict["avg"] = vary[2]
            start_dict["max"] = vary[3]
            start_list.append(start_dict)

        var_return_start_list = {
            "Start date" : start_dt,
            "observation data":start_list
        }
        session.close()

        return jsonify(var_return_start_list)
    else :
        " Invalid Date "
        #print ("Input date is not valid..")
        return"""<html>
            <br><br><br>
            Please enter a valid  Start Date as in 'YYYY-MM-DD' format
            <br><br>
            <a href="http://localhost:5000/">Go back to the Hawaii API Routes Main Page</a>
            </html>
            """


@app.route("/api/v1.0/<start>/<end>")
def start_end(start=None, end=None):

    session = Session(engine)
    start_dt = start
    end_dt   = end
    #Return a JSON list of tmin, tmax, tavg for all dates greater than and equal to the start date.
     # Check if the date entered is a valid date or not
    # future devlopment convert this checking of a valid date into a separate function/or a custom library
    try :
        year_st,month_st,day_st =start_dt.split('-')
        year_end,month_end,day_st =end_dt.split('-')
        dt.datetime(int(year_st),int(month_st),int(day_st))
        dt.datetime(int(year_end),int(month_end),int(day_st))

    except ValueError :
        #    " Invalid Date format"
        print ("Input date is not valid..")
        #return ("Please enter a valid  Start Date/End Date  as in 'YYYY-MM-DD/YYYY-MM-DD' format")
        return"""<html>
            <br><br><br>
            Please enter a valid  Start Date/End Date  as in 'YYYY-MM-DD/YYYY-MM-DD' format
            <br><br>
            <a href="http://localhost:5000/">Go back to the Hawaii API Routes Main Page</a>
            </html>
            """


    from_start = session.query(measurement.date, func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).filter(measurement.date >= start_dt).filter(measurement.date <= end_dt).all()
    start_end_list = []
     
    for vary in from_start:
        start_end_dict = {}
        start_end_dict["min"] = vary[1]
        start_end_dict["avg"] = vary[2]
        start_end_dict["max"] = vary[3]
        start_end_list.append(start_end_dict)

    var_return_start_end_list = {
        "Start date" : start_dt,
        "end date"   :end_dt,
        "observation data":start_end_list
    }  
    session.close()

    return jsonify(var_return_start_end_list)

if __name__ == "__main__":
    app.run(debug=True)