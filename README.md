<h2>Digital Air Pollution Filter Scraper</h2>

Script collector of sensor.community data which saves all data points into a single jsonline file.

The script runs autonomously every 30 minutes and updates the data accordingly.

To run it manually, simply execute the `data_scraper.py` file.

**Note** - Functions **1 & **2 are not used when automating this script.

<h3>**1 download_data_by_date</h3>
Downloads all sensor .csv files by specified date from the sensor community archive into {DATA_PATH}/{DATE} folder.

**Each 24h data file is around 800MB.** 

<h3>**2 clean_data</h3>
Goes through all downloaded .csv files by specified date, removes indoor sensors and creates a single jsonline file where the data points from all sensors is stored in a single file, keeping only the sensor_id, timestamp, lat, lon, P1 and P2 (sensor mesasurements) values.

<h3>**3 get_sensors_last_five_mins</h3>
Pull all sensor data for the last five minutes and append to jsonline file.
Additionally removes broken sensor data points & filters out sensors without measurements.

<h3>**4 clean_old_sensors</h3>
Overwrites existing jsonline file previously collected by the get_sensors_last_five_mins function and deletes all entries older than 48h.

<h3>**5 fix_timestamp</h3>
Sensor timestamps seem to be 1 hour behind GMT+1, this function checks for that and fixes the timestamp to match actual time.

<h3>**6 push_data_to_bucket</h3>
Pushes & overwrites file to GCP bucket.

**Requires GCP credentials file.**
