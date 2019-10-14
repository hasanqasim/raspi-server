import board
import busio
import adafruit_tcs34725
import adafruit_mpl3115a2
import firebase_admin
import google.cloud
from firebase_admin import credentials, firestore
from tinydb import TinyDB, Query
from datetime import datetime
import time

#this code snippet stores macaddress of the raspberri pi in the variable collection to be used for firebase collection name
# code taken from a raspberry pi forum: https://www.raspberrypi-spy.co.uk/2012/06/finding-the-mac-address-of-a-raspberry-pi/ 
interface='wlan0'
try:
    macadd = open('/sys/class/net/%s/address' %interface).read()
except:
    macadd = "00:00:00:00:00:00"
collection = macadd[0:17]
 
db_name = collection + ".json"

# create an instance of TinyDB with db_name as the macaddress.json. We use TinyDB no sql database as our offline storage
# This line of code and the other tinydb code that follows is taken from TinyDB's official python documentation: https://tinydb.readthedocs.io/en/latest/getting-started.html
db = TinyDB(db_name, sort_keys=True, indent=4, separators=(',', ': '))

# Following firebase code is from week 9 tutorial
firCredentials = credentials.Certificate("./hike-9b727-firebase-adminsdk-ov9ga-4c929d3172.json")
firApp = firebase_admin.initialize_app(firCredentials)
# get access to firestore
firStore = firestore.client()
# get access to the sensor collection
firSensorsCollectionRef = firStore.collection(collection)

# the following code snippets for working with the teperature and rgb sensor have been taken from week 8 tutorial and adafruit's github repo for setting up sensors
# adafruit github repo 1: https://github.com/adafruit/Adafruit_CircuitPython_MPL3115A2/blob/master/examples/mpl3115a2_simpletest.py
# adafruit github repo 2: https://learn.adafruit.com/adafruit-color-sensors/python-circuitpython?fbclid=IwAR0TICDgVrpCX7WUoGur6eLj0liVWJxJB4QaihXh2MKAbN1RMn74gMtYn7A
# Initialize the I2C bus.
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize the 2 sensors
rgb_sensor = adafruit_tcs34725.TCS34725(i2c)
altimeter_sensor = adafruit_mpl3115a2.MPL3115A2(i2c)

altimeter_sensor.sealevel_pressure = 101600
sReadings = []
# the following while loop runs until the script is manually stopped. Takes in all sesnor readings every minute, calculates the average of 5 readings, stores it in the offline db
# and sends it to firebase
while True:
    if len(db) > 150:
        db.purge_tables()
    pressure = altimeter_sensor.pressure
    altitude = altimeter_sensor.altitude
    lux = rgb_sensor.lux
    temperature = altimeter_sensor.temperature
    newReading = {
        "altitude": altitude,
        "lux": lux,
        "pressure": pressure,
        "temperature": temperature,
    }
    sReadings.append(newReading)
    if len(sReadings) == 5:
        avg_altitude = int(round((sReadings[0]["altitude"] + sReadings[1]["altitude"] + sReadings[2]["altitude"] + sReadings[3]["altitude"] + sReadings[4]["altitude"])/5,0))
        avg_lux = int(round((sReadings[0]["lux"] + sReadings[1]["lux"] + sReadings[2]["lux"] + sReadings[3]["lux"] + sReadings[4]["lux"])/5,0))
        avg_pressure = int(round((sReadings[0]["pressure"] + sReadings[1]["pressure"] + sReadings[2]["pressure"] + sReadings[3]["pressure"] + sReadings[4]["pressure"])/5,0))
        avg_temperature = int(round((sReadings[0]["temperature"] + sReadings[1]["temperature"] + sReadings[2]["temperature"] + sReadings[3]["temperature"] + sReadings[4]["temperature"])/5,0))
        sReadings.clear()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        avgReading = {
            "altitude": avg_altitude,
            "lux": avg_lux,
            "pressure": avg_pressure,
            "temperature": avg_temperature,
            "timestamp": timestamp
        }
        print(avgReading)
        db.insert(avgReading)
        print("size", len(db))
        firSensorsCollectionRef.add(avgReading)
    time.sleep(60)



