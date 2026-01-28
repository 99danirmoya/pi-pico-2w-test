import network
import time
import machine
from umqtt.simple import MQTTClient

# --- Wi-Fi Configuration ---
SSID = "Pixel_OF13"        # Replace with your Wi-Fi name
PASSWORD = "mynameisjeff" # Replace with your Wi-Fi password

# --- MQTT Configuration ---
# Public HiveMQ broker (no password required for port 1883)
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "pico_w_test_client_unique_id_temp" # Changed ID slightly to avoid conflicts
MQTT_TOPIC = b"test/topic/pico" 

# --- Temperature Sensor Setup ---
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / 65535

def read_internal_temperature():
    reading = sensor_temp.read_u16()
    voltage = reading * conversion_factor
    # Formula for RP2040/RP2350 internal temp
    temperature = 27 - (voltage - 0.706) / 0.001721
    return temperature

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    print("Connecting to Wi-Fi...", end="")
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print(".", end="")
        time.sleep(1)
        
    if wlan.status() != 3:
        raise RuntimeError('Wi-Fi connection failed')
    else:
        print("\nConnected to Wi-Fi")
        print("IP Address:", wlan.ifconfig()[0])

def mqtt_callback(topic, msg):
    print(f"New message on topic {topic.decode()}: {msg.decode()}")

def connect_mqtt():
    # Create MQTT client
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
    client.set_callback(mqtt_callback)
    
    print(f"Connecting to MQTT broker {MQTT_BROKER}...")
    client.connect()
    print("Connected to MQTT Broker!")
    
    return client

# --- Main Execution ---
try:
    connect_wifi()
    client = connect_mqtt()
    
    # Subscribe to a topic
    client.subscribe(MQTT_TOPIC)
    print(f"Subscribed to {MQTT_TOPIC.decode()}")

    print("Starting loop... Sending temperature every 10s. (Press Ctrl+C to stop)")
    
    last_publish_time = 0
    PUBLISH_INTERVAL = 10  # Seconds

    while True:
        # 1. Check for incoming messages (keep connection alive)
        client.check_msg()
        
        # 2. Check if 10 seconds have passed
        current_time = time.time()
        if current_time - last_publish_time >= PUBLISH_INTERVAL:
            # Read temp
            temp = read_internal_temperature()
            
            # Create message payload
            msg_str = f"Temp: {temp:.2f} C"
            msg_bytes = msg_str.encode('utf-8')
            
            # Publish
            print(f"Publishing: {msg_str}")
            client.publish(MQTT_TOPIC, msg_bytes)
            
            # Update timer
            last_publish_time = current_time
            
        # Small sleep to prevent tight loop CPU usage
        time.sleep(0.1)

except OSError as e:
    print("Error:", e)
    # import machine
    # machine.reset()
except KeyboardInterrupt:
    print("\nDisconnecting...")
    try:
        client.disconnect()
    except:
        pass
    print("Disconnected.")

