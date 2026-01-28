import network
import time
import machine
import sys
from umqtt.simple import MQTTClient

# --- SAFETY DELAY ---
# Wait for USB to become ready (optional, but helps)
time.sleep(3) 

# This 5-second pause allows you to stop the script in Thonny 
# if you need to edit the code. Otherwise, you might get locked out
# because the device sleeps (and kills USB) immediately after boot.
print("Booting... Press Ctrl+C within 5 seconds to stop!")
time.sleep(5)

# --- Configuration ---
SSID = "Pixel_OF13"
PASSWORD = "mynameisjeff"
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "pico_2_w_dormant_logger"
MQTT_TOPIC = b"test/topic/pico"

# --- Sensor Setup ---
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / 65535

def read_temperature():
    reading = sensor_temp.read_u16()
    voltage = reading * conversion_factor
    return 27 - (voltage - 0.706) / 0.001721

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    max_wait = 20
    print("Connecting to Wi-Fi...", end="")
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print(".", end="")
        time.sleep(1)
        
    if wlan.status() != 3:
        print("\nWi-Fi Failed. Sleeping...")
        go_to_sleep()
        
    print(f"\nConnected. IP: {wlan.ifconfig()[0]}")

def go_to_sleep():
    print("Entering Deep Sleep for 10 seconds (USB will disconnect)...")
    # Small delay to ensure print message gets out before USB dies
    time.sleep(0.1) 
    machine.deepsleep(10000)

# --- Main Execution ---
try:
    # Print reset cause for debugging (using raw value since constant is missing)
    # 1=PWRON, 3=WDT, etc. (varies by port)
    rc = machine.reset_cause()
    print(f"Reset Cause: {rc}")

    connect_wifi()
    
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
    client.connect()
    
    temp = read_temperature()
    msg = f"{temp:.2f}"
    
    client.publish(MQTT_TOPIC, msg)
    print(f"Published: {msg} C")
    
    client.disconnect()
    time.sleep(0.5) 

    go_to_sleep()

except Exception as e:
    print(f"Error occurred: {e}")
    time.sleep(1)
    go_to_sleep()

