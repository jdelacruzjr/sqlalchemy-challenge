import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
import datetime as dt

# Database connection
engine = create_engine("sqlite:///Resources/hawaii.sqlite",connect_args={'check_same_thread': False})
base = automap_base()
base.prepare(autoload_with=engine)
print(base.classes.keys())

# References to tables
measurement = base.classes.measurement
Station = base.classes.station

# Flask Setup
app = Flask(__name__)

# Flask Routes
@app.route("/")
def home():
    return (
        f"<h1>Welcome to the Climate App API!</h1>"
        f"<h1>Climate App: A Flask API for Climate Analysis</h1>"
        f"<br/>"
        f" <img width='900' src='https://img.olympicchannel.com/images/image/private/t_s_w2440/t_s_16_9_g_auto/f_auto/primary/ojpcg2xlihwx84ipvrcw'/ >"
        f"<h2>Here is a list of the available URL routes:</h2>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end<br/>"

        f"<h2>Or you can click these hyperlinks below to access the pages faster:</h2>"
        f"<ol><li><a href=http://127.0.0.1:5000/api/v1.0/precipitation>"
        f"JSON list of precipitation amounts by date for the most recent year of data available</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/stations>"
        f"JSON list of weather stations and their details</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/tobs>"
        f"JSON list of the last 12 months of recorded temperatures</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/2017-08-23>"
        f"Calculate the mimimum, average, and maximum temperature for all dates greater than and equal to the start date using the following format at the end of the URL. Start date(YYYY--MM--DD), for example: 2017-08-23</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/2016-08-23/2017-08-23>"
        f"Calculate the mimimum, average, and maximum temperature for a range of dates using the following format at the end of the URL. Start date(YYYY--MM--DD)/End date(YYYY--MM--DD), for example: 2016-08-23/2017-08-23</a></li><br/><br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Query to retrieve the last 12 months of precipitation data and return the results."""
    # Create our session (link) from Python to the DB.
    session = Session(engine)

    # Calculate the date 1 year ago from the last data point in the database.
    last_measurement_data_point_tuple = session.query(
        measurement.date).order_by(measurement.date.desc()).first()
    (latest_date, ) = last_measurement_data_point_tuple
    latest_date = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    latest_date = latest_date.date()
    date_year_ago = latest_date - dt.timedelta(days=365)

    # Perform a query to retrieve the data and precipitation scores.
    data_from_last_year = session.query(measurement.date, measurement.prcp).filter(
        measurement.date >= date_year_ago).all()

    session.close()

    # Convert the query results to a dictionary using date as the key and prcp as the value.
    all_precipication = []
    for date, prcp in data_from_last_year:
        if prcp != None:
            precip_dict = {}
            precip_dict[date] = prcp
            all_precipication.append(precip_dict)

    # Return the JSON representation of dictionary.
    return jsonify(all_precipication)

@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query for stations.
    stations = session.query(Station.station, Station.name,
                             Station.latitude, Station.longitude, Station.elevation).all()

    session.close()

    # Convert the query results to a dictionary.
    all_stations = []
    for station, name, latitude, longitude, elevation in stations:
        station_dict = {}
        station_dict["station"] = station
        station_dict["name"] = name
        station_dict["latitude"] = latitude
        station_dict["longitude"] = longitude
        station_dict["elevation"] = elevation
        all_stations.append(station_dict)

    # Return the JSON representation of dictionary.
    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    """Query for the dates and temperature observations from a year from the last data point for the most active station."""
    # Create our session (link) from Python to the DB.
    session = Session(engine)

    # Calculate the date 1 year ago from the last data point in the database.
    last_measurement_data_point_tuple = session.query(
        measurement.date).order_by(measurement.date.desc()).first()
    (latest_date, ) = last_measurement_data_point_tuple
    latest_date = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    latest_date = latest_date.date()
    date_year_ago = latest_date - dt.timedelta(days=365)

    # Find the most active station.
    most_active_station = session.query(measurement.station).\
        group_by(measurement.station).\
        order_by(func.count().desc()).\
        first()

    # Get the station id of the most active station.
    (most_active_station_id, ) = most_active_station
    print(
        f"The station id of the most active station is {most_active_station_id}.")

    # Perform a query to retrieve the data and temperature scores for the most active station from the last year.
    data_from_last_year = session.query(measurement.date, measurement.tobs).filter(
        measurement.station == most_active_station_id).filter(measurement.date >= date_year_ago).all()

    session.close()

    # Convert the query results to a dictionary using date as the key and temperature as the value.
    all_temperatures = []
    for date, temp in data_from_last_year:
        if temp != None:
            temp_dict = {}
            temp_dict[date] = temp
            all_temperatures.append(temp_dict)
    # Return the JSON representation of dictionary.
    return jsonify(all_temperatures)

@app.route('/api/v1.0/<start>', defaults={'end': None})

@app.route("/api/v1.0/<start>/<end>")
def determine_temps_for_date_range(start, end):
    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range."""
    """When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date."""
    """When given the start and the end date, calculate the TMIN, TAVG, and TMAX for dates between the start and end date inclusive."""
    # Create our session (link) from Python to the DB.
    session = Session(engine)

    # If we have both a start date and an end date.
    if end != None:
        temperature_data = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
            filter(measurement.date >= start).filter(
            measurement.date <= end).all()
    # If we only have a start date.
    else:
        temperature_data = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
            filter(measurement.date >= start).all()

    session.close()

    # Convert the query results to a list.
    temperature_list = []
    no_temperature_data = False
    for min_temp, avg_temp, max_temp in temperature_data:
        if min_temp == None or avg_temp == None or max_temp == None:
            no_temperature_data = True
        temperature_list.append(min_temp)
        temperature_list.append(avg_temp)
        temperature_list.append(max_temp)
    # Return the JSON representation of dictionary.
    if no_temperature_data == True:
        return f"No temperature data found for the given date range. Try another date range."
    else:
        return jsonify(temperature_list)

if __name__ == "__main__":
    app.run(debug=True)