import os
import broker as bk
import datetime
from dotenv import load_dotenv

if __name__ == "__main__":
    # Grab all credentials from .env
    load_dotenv()
    HOST = os.getenv("HOST")
    PORT = int(os.getenv("PORT"))
    TIMEOUT = int(os.getenv("TIMEOUT"))
    TOPIC = os.getenv("TOPIC")
    ASSET_UID = os.getenv("ASSET_UID")
    DATAUSERNAME = os.getenv("DATAUSERNAME")
    PASSWORD = os.getenv("PASSWORD")
    # print(HOST, PORT, TIMEOUT, TOPIC, ASSET_UID, DATAUSERNAME, PASSWORD)

    mqttc = bk.MqttWrapper(HOST, PORT, DATAUSERNAME, PASSWORD)
    
    mqttc.connect()
    
    now = datetime.datetime.now()
    timestamp = int(datetime.datetime.timestamp(now))

    message = {
        'timestamp': str(timestamp),
        'topic': TOPIC,
        'device_asset_uid': ASSET_UID
    }
    
    light_sensor = bk.Sensor('Arduino_light_sensor', 
                             'Analog', 
                             'LDR (Light Dependent Resistor)', 
                             'Measures light intensity and converts it into an electrical signal. Used in cameras, streetlights, etc.',
                             5)

    # Below function could be a publish specific to the Sensor Class
    # Could overload the publish function in MqttWrapper
    # e.g. passing a board will publish every sensor on there, but passing it a device will publish EVERY sensor on that device. 
    # Streamlined mass publishing
    message[light_sensor.name] = light_sensor.value

    mqttc.start()

    mqttc.publish(TOPIC, message, timeout=TIMEOUT)

    mqttc.stop()
