import datetime
import json
import time

import paho.mqtt.client as mqtt

class Sensor:
    def __init__(self, name, sensor_type, category, description, value=0):
        self.name = name
        self.sensor_type = sensor_type
        self.category = category
        self.description = description
        self.value = value

class Board:
    def __init__(self, name, type, description):
        self.name = name
        self.type = type
        self.description = description
        self.sensors = list()
    
    def add_sensor(self, new_sensor : Sensor):
        self.sensors.append(new_sensor)
    
    def rem_board(self, sensor: Sensor):
        self.sensors.remove(sensor)
    
    def view(self):
        print("--List of Sensors--")
        for sensor in self.sensors:
            print(sensor.name)
        

class Device:
    def __init__(self, UID, name, topic):
        self.UID = UID
        self.name = name
        self.topic = topic
        self.boards = list()

    def add_board(self, new_board : Board):
        self.boards.append(new_board)
    
    def rem_board(self, board: Board):
        self.boards.remove(board)
    
    def view(self):
        print("--List of Boards--")
        for board in self.boards:
            print(board.name)



class MqttWrapper:
    # Code for arduino1
    # Reference https://github.com/eclipse/paho.mqtt.python/blob/master/README.rst
    
    def __init__(self, host, port, username, password):
        super().__init__()
        self.unacked_publish = set()
        
        self.host = host
        self.port = port
            
        def on_connect(client, userdata, flags, reason_code, properties):
            print(f'Connected with result code {reason_code}')
            if reason_code == 0:
                print('MQTT connection success')
                client.connected_flag = True
            else:
                print('MQTT connection failed', reason_code)
                client.bad_connection_flag = True
                client.bad_connection_message = str(reason_code)
            # Subscribing in on_connect() means that if we lose the connection and
            # reconnect then subscriptions will be renewed.
    
        def on_message(client, userdata, msg):
            print(msg.topic + ' ' + str(msg.payload))
    
        def on_disconnect(client, *args, **kwargs):
            print('disconnected', *args, **kwargs)
            client.bad_connection_flag = True
            client.bad_connection_message = 'Disconnected from host'
    
        def on_publish(client, userdata, mid, reason_code, properties):
            print('on_publish', client, userdata, mid, reason_code, properties)
            # reason_code and properties will only be present in MQTTv5. It's always unset in MQTTv3
            try:
                userdata.remove(mid)
            except KeyError:
                print('on_publish() is called with a mid not present in unacked_publish')
                print('This is due to an unavoidable race-condition:')
                print('* publish() return the mid of the message sent.')
                print('* mid from publish() is added to unacked_publish by the main thread')
                print('* on_publish() is called by the loop_start thread')
                print('While unlikely (because on_publish() will be called after a network round-trip),')
                print(' this is a race-condition that COULD happen')
                print('')
                print('The best solution to avoid race-condition is using the msg_info from publish()')
                print('We could also try using a list of acknowledged mid rather than removing from pending list,')
                print('but remember that mid could be re-used !')
    
        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttc.connected_flag = False
        self.mqttc.bad_connection_flag = False

        self.mqttc.username_pw_set(username, password)
    
        self.mqttc.on_publish = on_publish
        self.mqttc.on_connect = on_connect
        self.mqttc.on_disconnect = on_disconnect
    
        self.mqttc.user_data_set(self.unacked_publish)
    
    def connect(self):
        print(f'Attempting to connect to host={self.host}, port={self.port}')
        self.mqttc.connect(self.host, self.port)

    def subscribe(self, topic):
        print('subscribing to', topic)
        self.mqttc.subscribe(topic)
    
    def start(self):
        self.mqttc.loop_start()
    
        while not self.mqttc.connected_flag and not self.mqttc.bad_connection_flag:  # wait in loop
            print('In wait loop')
            time.sleep(1)
    
        if self.mqttc.bad_connection_flag:
            self.mqttc.loop_stop()  # Stop loop
            raise Exception(f'Unable to connect to MQTT: {self.mqttc.bad_connection_message}')
    
    def stop(self):
        self.mqttc.disconnect()
        self.mqttc.loop_stop()
    
    def publish(self, topic, message, timeout):
        msg_info = self.mqttc.publish(topic, json.dumps(message), qos=1)
        self.unacked_publish.add(msg_info.mid)

        # Due to race-condition described above, the following way to wait for all publish is safer
        msg_info.wait_for_publish(timeout=timeout)
    
