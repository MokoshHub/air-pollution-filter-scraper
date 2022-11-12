import time, os, requests, wget
from tqdm import tqdm
import jsonlines, csv
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from gcloud import storage

def download_data_by_date(date, data_path="pms_data"):
    # DATE = '2022-11-10'
    # DATA_PATH = 'pms_data'

    if not os.path.exists(data_path):
        os.makedirs(data_path)

    chrome_options = Options()
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)

    # dht - temperature and humidity
    # bme - temperature, humidity and pressure
    # sds - pm2.5 and pm10
    # pms - pm2.5 and pm10

    if not os.path.exists(os.path.join(data_path, date)):
        os.makedirs(os.path.join(data_path, date))

    driver.get(('http://archive.sensor.community/%s/' % date));
    files_list = driver.find_elements(By.XPATH, "/html/body/pre[2]")[0]
    a_tags = files_list.find_elements(By.TAG_NAME, "a")[1:]

    for a in tqdm(a_tags):
        if ('indoor' not in a.get_attribute("href") and 'sds011' in a.get_attribute("href")):
            wget.download(a.get_attribute("href"), os.path.join(data_path, date), bar=None)

    driver.quit()

def clean_data(date, data_path="pms_data"):
    # DATA_PATH = 'pms_data'

    for root, dirs, files in os.walk(os.path.join(data_path, date)):
        print("Iterating files:\n")
        for file in tqdm(files):
            if file.endswith(".csv"):
                with open(os.path.join(root, file)) as csv_file:
                    single_sensor_file = csv.reader(csv_file, delimiter=';')
                    next(single_sensor_file) # skip first line
                    for row in tqdm(single_sensor_file, leave=False):
                        with jsonlines.open(os.path.join(data_path, 'mika' + '.jsonl'), mode='a') as writer:
                            sensor_id = row[0]
                            timestamp = row[5]
                            lat = row[3]
                            lon = row[4]
                            P1 = row[6]
                            P2 = row[9]

                            writer.write({
                                'sensor_id': sensor_id,
                                'timestamp': timestamp,
                                'lat': lat,
                                'lon': lon,
                                'P1': P1,
                                'P2': P2
                            })
            # break

def get_sensors_last_five_mins(data_path):
    # past 5 minutes URL
    # https://data.sensor.community/airrohr/v1/filter/type=SDS011/
    past_5_mins_url = 'https://data.sensor.community/airrohr/v1/filter/type=SDS011'
    response = requests.get(past_5_mins_url)
    data = response.json()
    
    # change to append mode when script is running autonomously
    with jsonlines.open(os.path.join(data_path, 'mika' + '.jsonl'), mode='a') as writer:
        for entry in data:
            sensor_id = entry['sensor']['id']
            # timestamp is 1 hour behind
            timestamp = str(fix_timestamp(entry['timestamp']))
            lat = entry['location']['latitude']
            lon = entry['location']['longitude']
            
            try:
                if entry['sensordatavalues'][0]['value_type'] == 'P1':
                    p1 = entry['sensordatavalues'][0]['value']
                elif entry['sensordatavalues'][1]['value_type'] == 'P1':
                    p1 = entry['sensordatavalues'][1]['value']
            except:
                p1 = None

            try:
                if entry['sensordatavalues'][0]['value_type'] == 'P2':
                    p2 = entry['sensordatavalues'][0]['value']
                elif entry['sensordatavalues'][1]['value_type'] == 'P2':
                    p2 = entry['sensordatavalues'][1]['value']
            except:
                p2 = None

            if p1 != None and p2 != None:
                writer.write({
                    'sensor_id': sensor_id,
                    'timestamp': timestamp,
                    'lat': lat,
                    'lon': lon,
                    'P1': p1,
                    'P2': p2
                })

def clean_old_sensors(DATA_PATH):
    # delete sensor data from more than 48h ago
    with jsonlines.open(os.path.join(DATA_PATH, 'mika' + '.jsonl'), mode='r') as reader:
        fresh_lines = []
        for entry in reader:
            fresh_lines.append(entry)

    with jsonlines.open(os.path.join(DATA_PATH, 'mika' + '.jsonl'), mode='w') as updater:
        for entry in fresh_lines:
            timestamp = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S')
            current_time = datetime.now()
            if not current_time - timestamp > timedelta(hours=48):
                updater.write(entry)

def fix_timestamp(timestamp):
    # check if timestamp 1 hour behind
    # if so, add 1 hour
    # else, return timestamp
    timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    current_time = datetime.now()

    if timestamp.hour == current_time.hour - 1:
        timestamp = timestamp + timedelta(hours=1)
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def push_data_to_bucket(DATA_PATH):
    # push data to bucket
    client = storage.Client.from_service_account_json('creds.json')
    bucket = client.get_bucket('mika_air_quality')
    blob = bucket.blob('mika.jsonl')
    blob.upload_from_filename(os.path.join(DATA_PATH, 'mika' + '.jsonl'))

def main():
    DATA_PATH = './pms_data'
    # DATE = '2022-11-10'

    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    # download_data_by_date(DATE, DATA_PATH)
    # clean_data(DATE, DATA_PATH)
    get_sensors_last_five_mins(DATA_PATH)
    clean_old_sensors(DATA_PATH)
    push_data_to_bucket(DATA_PATH)

if __name__ == "__main__":
    main()