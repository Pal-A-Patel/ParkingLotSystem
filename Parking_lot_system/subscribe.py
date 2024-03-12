"""
------------------------------------------------------------------------------------------------------
The below code consists of the parking lot system. The below code is used to subscribe messages and
integrate GUI with two-way communication between the raspberry pie and the servers. This code is the
main version to signal to turn the LED ON or OFF, read temperature and humidity and produce a two-way
communication.

------------------------------------------------------------------------------------------------------
Pal Patel, Saskatoon
Email: palpatel486@gmail.com

------------------------------------------------------------------------------------------------------
"""

import paho.mqtt.client as mqtt
import smbus
import RPi.GPIO as GPIO
import time


# set up the GPIO pins
def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(23, GPIO.OUT) #GREEN LED
    GPIO.setup(18, GPIO.OUT) #RED LED
    
# Define the pins used for the keypad
ROW = [12, 16, 20, 21] #
COL = [6, 13, 19, 26] #

# Define the keypad mapping
KEYPAD = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"]
]

# Initialize the GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in ROW:
    GPIO.setup(pin, GPIO.OUT)
for pin in COL:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Function to read the keypad
def get_key():
    for row_pin in ROW:
        GPIO.output(row_pin, 0)
        for col_pin in COL:
            if GPIO.input(col_pin) == 0:
                key = KEYPAD[ROW.index(row_pin)][COL.index(col_pin)]
                while GPIO.input(col_pin) == 0:
                    pass
                GPIO.output(row_pin, 1)
                return key
        GPIO.output(row_pin, 1)
    return None


# function to read the temperature and humidity from DHT11

MAX_UNCHANGE_COUNT = 100
STATE_INIT_PULL_DOWN = 1
STATE_INIT_PULL_UP = 2
STATE_DATA_FIRST_PULL_DOWN = 3
STATE_DATA_PULL_UP = 4
STATE_DATA_PULL_DOWN = 5

def read_dht11_dat():
    """
    Functionality:
         Reads data from the DHT11 sensor connected to GPIO pin 25.

    Returns:
        tuple: A tuple containing the temperature and humidity values read from the sensor.
        If the data read is not valid, False is returned.
    """
    GPIO.setup(25, GPIO.OUT)
    GPIO.output(25, GPIO.HIGH)
    time.sleep(0.05)
    GPIO.output(25, GPIO.LOW)
    time.sleep(0.02)
    GPIO.setup(25, GPIO.IN, GPIO.PUD_UP)

    unchanged_count = 0
    last = -1
    data = []
    while True:
        current = GPIO.input(25)
        data.append(current)
        if last != current:
            unchanged_count = 0
            last = current
        else:
            unchanged_count += 1
            if unchanged_count > MAX_UNCHANGE_COUNT:
                break

    state = STATE_INIT_PULL_DOWN

    lengths = []
    current_length = 0

    for current in data:
        current_length += 1

        if state == STATE_INIT_PULL_DOWN:
            if current == GPIO.LOW:
                state = STATE_INIT_PULL_UP
            else:
                continue
        if state == STATE_INIT_PULL_UP:
            if current == GPIO.HIGH:
                state = STATE_DATA_FIRST_PULL_DOWN
            else:
                continue
        if state == STATE_DATA_FIRST_PULL_DOWN:
            if current == GPIO.LOW:
                state = STATE_DATA_PULL_UP
            else:
                continue
        if state == STATE_DATA_PULL_UP:
            if current == GPIO.HIGH:
                current_length = 0
                state = STATE_DATA_PULL_DOWN
            else:
                continue
        if state == STATE_DATA_PULL_DOWN:
            if current == GPIO.LOW:
                lengths.append(current_length)
                state = STATE_DATA_PULL_UP
            else:
                continue
    if len(lengths) != 40:
        return False

    shortest_pull_up = min(lengths)
    longest_pull_up = max(lengths)
    halfway = (longest_pull_up + shortest_pull_up) / 2
    bits = []
    the_bytes = []
    byte = 0

    for length in lengths:
        bit = 0
        if length > halfway:
            bit = 1
        bits.append(bit)
    for i in range(0, len(bits)):
        byte = byte << 1
        if (bits[i]):
            byte = byte | 1
        else:
            byte = byte | 0
        if ((i + 1) % 8 == 0):
            the_bytes.append(byte)
            byte = 0
    checksum = (the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3]) & 0xFF
    if the_bytes[4] != checksum:
        return False

    return the_bytes[0], the_bytes[2]
       
def detect():
    """
    Functionality:
         Detects keypress and reads data from the DHT11 sensor.

    Returns:
        str: A formatted string containing the pressed key, humidity, and temperature.
        If the data read is not valid, None is returned.

    Notes:
        Retrieves a keypress using the `get_key` function and stores it in the `key` variable.
        If the key is a valid input (1-9, 0, or C), it is stored in the `pressed_key` variable.
        The `read_dht11_dat` function is called to read data from the DHT11 sensor.
        If the data is valid, it is stored in the `humidity` and `temperature` variables.
        The function returns a formatted string containing the `pressed_key`, `humidity`, and `temperature`.

    """
    key = get_key()
    pressed_key = ""
    if key in ["1","2","3","4","5", "6", "7", "8", "9", "0", "C"]:
        pressed_key = key
        result = read_dht11_dat()
        if result:
            humidity, temperature = result        
            return f"{pressed_key},{humidity},{temperature}"


def destroy():
    """
    Functionality:
         This function performs the cleanup function. It turns off RED and GREEN LEDs.

    Returns:
        None
    """
    GPIO.output(23, GPIO.LOW)
    GPIO.output(18, GPIO.LOW)

def green():
    """
    Functionality:
         This function performs the warning lights off function. It turns on GREEN LEDs.

    Returns:
        None
    """
    GPIO.output(23, GPIO.HIGH)
    GPIO.output(18, GPIO.LOW)
def Red():
    """
    Functionality:
         This function performs the warning lights ON function. It turns on RED LEDs.

    Returns:
        None
    """
    GPIO.output(23, GPIO.LOW)      # Green led off
    GPIO.output(18, GPIO.HIGH)     # Red led on


pub_topic = "test/publisher"
sub_topic = "test/subscriber"
mqttBroker ="broker.hivemq.com"  


def on_connect (client, userdata, flags,  rc):
    """
    Functionality:
        Callback function which checks if a successful connection is established.

    Returns:
        None

    """
    print("connected" + str(rc))


def subscribe(client):
    """
    Functionality:
        This function is used to subscribe to MQTT topics and defines the on_message callback function.

     The on_message function is called when a message is received.
     Depending on the payload of the received message, different actions are performed.

     Args:
         client: The MQTT client instance.

     Returns:
         None

     Notes:
         If the received string is "GL_ON", the green LED is ON.
         If the received string is "RL_ON", the red LED is ON.
         If the received string is "LD_OFF", the LEDs are OFF.
         If the received string is "OFF", the humiture sensor is turned off.
         For any other received string, the message is printed from the text box.
     """
    def on_message(client, userdata, message):
        """
        This is a callback function which is used when a message is received.
        It works according to the message received.

        Args:
            client: The MQTT client instance.
            userdata: User-defined data passed to the callback.
            message: The received message object.

        Returns:
            None
        """
        if (message.payload.decode('utf-8') == "GL_ON"):
            print("Turning green led on...")
            setup()
            green()
        elif (message.payload.decode('utf-8') == "RL_ON"):
            print("Turning Red led on...")
            setup()
            Red()
        elif (message.payload.decode('utf-8') == "LD_OFF"):
            print("Turning off led...")
            setup()
            destroy()
        elif (message.payload.decode('utf-8') == "OFF"):
            print("Turning OFF humiture sensor...")
            setup()
            destroy()
        else:
            print("MESSAGE FROM TEXT BOX: "+message.payload.decode())
            



    client.subscribe(pub_topic,  qos=0)
    client.on_message = on_message


client = mqtt.Client("Asuj_Patel")
client.connect(mqttBroker)


client.on_connect = on_connect
subscribe(client)



while True:
    msg = detect()
    print(msg)
    client.publish(sub_topic, msg)
    time.sleep(2)
    client.loop()


client.loop_forever()


