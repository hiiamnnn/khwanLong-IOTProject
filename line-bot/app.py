from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError,
    LineBotApiError
)
from linebot.models import *
import paho.mqtt.client as mqtt
import threading
import time

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('1Di0x6yqmxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
# Channel Secret
handler = WebhookHandler('e90300105xxxxxxxxxxxxxxxxxxxxxxx')

auto_status = "on"
manual_status = {}
alert_triggered = False
mq135 = None
temp = 0
flame = None

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("sensor/#")

def on_message(client, userdata, msg):
    global mq135, temp, flame
    payload = msg.payload.decode('utf-8')
    if msg.topic == "sensor/mq135":
        mq135 = payload
    elif msg.topic == "sensor/temp":
        temp = float(payload)
    elif msg.topic == "sensor/flame":
        flame = payload
    print(payload)

def send_alert():
    global auto_status, manual_status, alert_triggered
    reply_to_user = ""

    while((mq135 == "Gas detected!") or (flame == "Flame detected!") or (temp >= 50)):
        if auto_status == "on" and not manual_status:
            if mq135 == "Gas detected!":
                reply_to_user = "MQ135 Sensor: ตรวจพบควันและปริมาณความเข้มข้นแก๊สพิษเกินกำหนด !!"
                line_bot_api.broadcast(TextSendMessage(text=reply_to_user))
            if flame == "Flame detected!":
                reply_to_user = "Flame Sensor: ตรวจพบว่าเปลวไฟอยู่ใกล้ ๆ !!"
                line_bot_api.broadcast(TextSendMessage(text=reply_to_user))
            if temp >= 50:
                reply_to_user = "Temperature Sensor: ตรวจพบว่าค่าอุณหภูมิเกินกำหนด " + str(temp) + " °C"
                line_bot_api.broadcast(TextSendMessage(text=reply_to_user))
        elif auto_status == "off":
            for user_id, status in manual_status.items():
                if status == "on":        
                    if mq135 == "Gas detected!":
                        reply_to_user = "MQ135 Sensor: ตรวจพบควันและปริมาณความเข้มข้นแก๊สพิษเกินกำหนด !!"
                        line_bot_api.push_message(user_id, TextSendMessage(text=reply_to_user))
                    if flame == "Flame detected!":
                        reply_to_user = "Flame Sensor: ตรวจพบว่าเปลวไฟอยู่ใกล้ ๆ !!"
                        line_bot_api.push_message(user_id, TextSendMessage(text=reply_to_user))
                    if temp >= 50:
                        reply_to_user = "Temperature Sensor: ตรวจพบว่าค่าอุณหภูมิเกินกำหนด " + str(temp) + " °C"
                        line_bot_api.push_message(user_id, TextSendMessage(text=reply_to_user))
            if status == "off" and not alert_triggered:
                reply_to_user = "ขณะนี้มีผู้ใช้งานดำเนินการปิดใช้งานควันหลงอัตโนมัติ\n\n"
                reply_to_user += "ผู้ใช้สามารถพิมพ์ on เพื่อเปิดใช้งานควันหลงใหม่อีกครั้ง"
                line_bot_api.broadcast(TextSendMessage(text=reply_to_user))
                alert_triggered = True
        time.sleep(5)
        return 'OK'
    
# Listen for all Post Requests from /callback
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# Process messages
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    msg_from_user = event.message.text
    reply = ""
    global auto_status
    
    # Process the received message
    if msg_from_user == "ช่วยเหลือ" or msg_from_user.lower() == "-h" or msg_from_user.lower() == "help":
        reply = "คำสั่ง: \n"
        # reply += "พิมพ์ connect เพื่อเชื่อมต่อบัญชีของคุณ\n"
        reply += "พิมพ์ on เพื่อเปิดใช้งานควันหลง\n"
        reply += "พิมพ์ off เพื่อปิดใช้งานควันหลง"
    elif msg_from_user.lower() == "on":
        client.publish("status/msg_from_user", msg_from_user.lower())
        auto_status = "off"
        manual_status[event.source.user_id] = "on"
        reply = "เปิดใช้งานควันหลงเรียบร้อย"   
    elif msg_from_user.lower() == "off":
        client.publish("status/msg_from_user", msg_from_user.lower())
        auto_status = "off"
        manual_status[event.source.user_id] = "off"   
        reply = "ปิดใช้งานควันหลงเรียบร้อย"
    else: 
        reply = "ขอโทษ ควันหลงไม่เข้าใจคำสั่ง"
    print("auto_status: {}, status_from_user: {}".format(auto_status, manual_status))
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

def start_auto():
    print("auto_status: {}, status_from_user: {}".format(auto_status, manual_status))
    send_alert()
    threading.Timer(10, start_auto).start()  # Check for alert every 5 seconds

import os
if __name__ == "__main__":

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("192.168.xxx.xx", 1883)  # Connect to the broker
    client.loop_start()  # Start the MQTT client loop

    # Start the program and trigger "on" functionality
    start_auto()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)