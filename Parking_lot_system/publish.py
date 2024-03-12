"""
------------------------------------------------------------------------------------------------------
The below code consists of the parking lot system. The below code is used to publish messages and
integrate GUI with two-way communication between the raspberry pie and the servers. This code is the
main version to signal to turn the LED ON or OFF, read temperature and humidity and produce a two-way
communication.

------------------------------------------------------------------------------------------------------
Pal Patel, Saskatoon
Email: palpatel486@gmail.com

------------------------------------------------------------------------------------------------------
"""

# Importing packages
from PyQt5 import QtWidgets
import pal_del3
import sys
import paho.mqtt.client as mqtt_client
client_id = "fake_temp2"

pub_topic = "test/publisher"
sub_topic = "test/subscriber"


class MainWindow(QtWidgets.QMainWindow, pal_del3.Ui_MainWindow):
    def __init__(self):
        """
        This function Initializes the MainWindow class and sets up the user interface.
        Connects the button signals to their respective slot functions.
        Sets the initial text of the Terminal widget based on the subscribe function.
        """
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.Warning_On.clicked.connect(self.Warning_ON)
        self.Warning_Off.clicked.connect(self.Warning_OFF)
        self.Submit.clicked.connect(self.Submit_message)
        self.Terminal.setText(self.subscribe(client))

    def Warning_ON(self):
        """
        Functionality:
        This function turns on the warning lights.

        Args:
            self: The instance of class.

        Returns:
            None
        """
        msg = "RL_ON"
        # Publishes a message to a client to enable the warning functionality.
        client.publish(pub_topic, msg, qos=0, retain=False)
        print(msg)

    #
    def Warning_OFF(self):
        """
        Functionality:
        Function to turn off the warning lights.
        It publishes a message to a client to enable the warning functionality.
        The message contains the string "GL_ON" which suggests green LED On.

        Args:
            self: The instance of class.

        Returns:
            None
        """
        msg = "GL_ON"
        client.publish(pub_topic, msg, qos=0, retain=False)
        print(msg)
    def Submit_message(self):
        """
        Functionality:
        The function submits a message for publishing.
        Retrieves the message entered in the Send_Command text input.
        Publishes the message to the specified pub_topic using the MQTT client.

        Args:
            self: The instance of the class.

        Returns:
            None
        """
        msg = self.Send_Command.toPlainText()
        client.publish(pub_topic, msg, qos=0, retain=False)
        print(msg)

    #
    def on_connect(client, userdata, flags, rc):
        """
        Functionality:
        Callback function triggered upon successful connection to the MQTT broker.
        If the connection is successful, it prints a confirmation message
        and subscribes to the specified sub_topic. If the connection fails, it prints
        an error message along with the return code.

        Args:
            client: The MQTT client instance.
            userdata: User-defined data passed to the callback.
            flags: Response flags sent by the broker.
            rc: The connection result or return code.

        Returns:
            None
        """
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(sub_topic)
        else:
            print("Failed to connect, return code %d\n", rc)

    def connect_mqtt() -> mqtt_client:
        """
        Functionality:
        Connects to the MQTT broker and returns the MQTT client.

        Returns:
            mqtt_client: The connected MQTT client.

        """
        return client

    def subscribe(self,client: mqtt_client):
        """
        Functionality:
        This function subscribes to a specific topic and defines an on_message callback function.
        Upon receiving a message, the on_message callback is triggered, and the payload of the message is processed.
        The payload is split into spot, temp, and hum values. This values are utilized to update
        parking spots which are marked as checked on GUI.

        Args:
            client: The MQTT client instance.

        Returns:
            None
        """
        def on_message(client, userdata, msg):
            # Callback function triggered upon receiving a message.
            main_message = (msg.payload.decode('utf-8'))
            spot = main_message.split(",")[0]
            temp = main_message.split(",")[2]
            hum = main_message.split(",")[1]

            # Update checkbox states based on the parking spot value entered
            if spot == "1":
                self.checkBox.setChecked(True)
            elif spot == "2":
                self.checkBox_9.setChecked(True)
            elif spot == "3":
                self.checkBox_8.setChecked(True)
            elif spot == "4":
                self.checkBox_7.setChecked(True)
            elif spot == "5":
                self.checkBox_6.setChecked(True)
            elif spot == "6":
                self.checkBox.setChecked(False)
            elif spot ==  "7":
                self.checkBox_9.setChecked(False)
            elif spot == "8":
                self.checkBox_8.setChecked(False)
            elif spot == "9":
                self.checkBox_7.setChecked(False)
            elif spot == "0":
                self.checkBox_6.setChecked(False)
            elif spot == "C":
                self.checkBox_6.setChecked(False)
                self.checkBox_7.setChecked(False)
                self.checkBox_8.setChecked(False)
                self.checkBox_9.setChecked(False)
                self.checkBox.setChecked(False)
                      
            mainWindow.Terminal.setText("Temperature: "+temp+" Humidity: "+hum)
            print(main_message)

        # Start the MQTT client loop.
        client.loop_start()
        # Subscribe to the specified sub_topic with a QoS of 2.
        client.subscribe(sub_topic, qos=2)
        client.on_message = on_message


if __name__ == "__main__":
    mqttBroker = "broker.hivemq.com"
    client_id = "fake_temp2"
    client = mqtt_client.Client(client_id)  # Client Name
    client.connect(mqttBroker)
    client.loop_start()
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())

