from flask import Flask, request, jsonify, render_template,send_file 
#from flask_socketio import SocketIO, emit, send
from flask_cors import CORS, cross_origin
import requests
import gpiod
import subprocess
import os
import time
import json
from datetime import datetime, timezone, timedelta
import socket
import uuid
from gpiozero import MotionSensor , AngularServo , LED ,Servo
from signal import pause
import RPi.GPIO as GPIO
import threading
import math
from time import sleep, localtime
from threading import Timer
import asyncio 

# port
API_PORT = 5000
# เซ็นเซอร์  

#time.sleep(10)

# AUTO START
#sudo nano /etc/rc.local
#python3 ~/Desktop/money/app.py &

deviceId = str(uuid.getnode())
secret = os.urandom(24).hex()
DEBUG_MODE = False
app = Flask(__name__,template_folder="")
#app.logger.info("Starting...")
app.config['SECRET_KEY'] = secret

CORS(app)

def GetSerial():
    returned_output = uuid.getnode()#subprocess.call("cat /sys/firmware/devicetree/base/serial-number",shell=True)
    return returned_output

### end
@app.route('/')
def index():
    return render_template('money.html')

@app.route('/favicon.ico')
def favicon():
    msg = {}
    msg['status'] = "success"
    msg['msg'] = "close"
    return jsonify(msg),200

@app.route('/update',methods=['GET'])
def get_update():
    os.system("git pull https://github.com/bossware14/money.git")
    os.system("pkill chromium")
    msg = {}
    msg['status'] = "success"
    msg['msg'] = "update"
    return jsonify(msg),200

@app.route('/version')
def version():
    msg = {}
    msg['version'] = 1.0
    return jsonify(msg),200


@app.route('/close')
def close_app():
    os.system("pkill chromium")
    msg = {}
    msg['status'] = "success"
    msg['msg'] = "close"
    return jsonify(msg),200

@app.route('/exit')
def close_exit(): 
    os.system("pkill chromium")
    os.system("fuser -k 5000/tcp")
    msg = {}
    msg['status'] = "success"
    msg['msg'] = "close"
    return jsonify(msg),200


@app.route('/start')
def start_app():
    msg = {}
    msg['status'] = "success"
    msg['msg'] = "start"
    url = "http://localhost:"+str(API_PORT)
    subprocess.Popen(['chromium-browser','--start-fullscreen','--kiosk',url]) 
    return jsonify(msg),200


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


if os.path.isfile('main.json'):
    with open('main.json', 'r') as f:
      json_data = json.load(f)
else:
    json_data = {
  "id": "AUTO",
  "ip": "127.0.0.1",
  "payment":{
      "createPayment":"",
      "checkRef":"",
      "device": "db46767m980se",
      "walletId":"",
      "type":"qrcode",
      "status":"1"
  },
  "wallet": {
    "in": 0,
    "out": 0,
    "coin": 0,
    "MONEY": 0,
    "qrcode": 0,
    "payment": 'AUTO',
    "Agent": 'AUTO',
    "walletId": 'AUTO'
  }
}

tz = timezone(timedelta(hours = 7))
json_data['id'] = socket.gethostname()
json_data['ip'] = get_ip()

def update_data(json_data):
    json_data['id'] = socket.gethostname()
    json_data['ip'] = get_ip()
    with open('main.json', 'w') as f:
        json.dump(json_data, f) 
    return json_data


@app.errorhandler(501)
def page_not_304():
   return jsonify({"status": "error","code": "304","msg":"304"}),200
@app.errorhandler(500)
def page_not_s():
   return jsonify({"status": "error","code": "500","msg":"500"}),200
@app.errorhandler(404)
def page_not_found():
   return jsonify({"status": "error","code": "404","msg":"404"}),200
@app.errorhandler(400)
def page_not_found_400():
   return jsonify({"status": "error","code": "400","msg":"400"}),200


HexDigits = [0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 
            0x6F, 0x77, 0x7C, 0x39, 0x5E, 0x79, 0x71, 0x3D, 0x76, 
            0x06, 0x1E, 0x76, 0x38, 0x55, 0x54, 0x3F, 0x73, 0x67, 
            0x50, 0x6D, 0x78, 0x3E, 0x1C, 0x2A, 0x76, 0x6E, 0x5B,
            0x00, 0x40, 0x63, 0xFF]

ADDR_AUTO = 0x40
ADDR_FIXED = 0x44
STARTADDR = 0xC0
# DEBUG = False

class TM1637:
    __doublePoint = False
    __Clkpin = 0
    __Datapin = 0
    __brightness = 1.0  # default to max brightness
    __currentData = [0, 0, 0, 0]

    def __init__(self, CLK, DIO, brightness):
        self.__Clkpin = CLK
        self.__Datapin = DIO
        self.__brightness = brightness
        GPIO.setup(self.__Clkpin, GPIO.OUT)
        GPIO.setup(self.__Datapin, GPIO.OUT)

    def cleanup(self):
        """Stop updating clock, turn off display, and cleanup GPIO"""
        self.StopClock()
        self.Clear()
        GPIO.cleanup()

    def Clear(self):
        b = self.__brightness
        point = self.__doublePoint
        self.__brightness = 0
        self.__doublePoint = False
        data = [0x7F, 0x7F, 0x7F, 0x7F]
        self.Show(data)
        # Restore previous settings:
        self.__brightness = b
        self.__doublePoint = point

    def ShowInt(self, i):
        s = str(i)
        self.Clear()
        for i in range(0, len(s)):
            self.Show1(i, int(s[i]))

    def Show(self, data):
        for i in range(0, 4):
            self.__currentData[i] = data[i]

        self.start()
        self.writeByte(ADDR_AUTO)
        self.br()
        self.writeByte(STARTADDR)
        for i in range(0, 4):
            self.writeByte(self.coding(data[i]))
        self.br()
        self.writeByte(0x88 + int(self.__brightness))
        self.stop()

    def Show1(self, DigitNumber, data):
        """show one Digit (number 0...3)"""
        if(DigitNumber < 0 or DigitNumber > 3):
            return  # error

        self.__currentData[DigitNumber] = data

        self.start()
        self.writeByte(ADDR_FIXED)
        self.br()
        self.writeByte(STARTADDR | DigitNumber)
        self.writeByte(self.coding(data))
        self.br()
        self.writeByte(0x88 + int(self.__brightness))
        self.stop()
    # Scrolls any integer n (can be more than 4 digits) from right to left display.
    def ShowScroll(self, n):
        n_str = str(n)
        k = len(n_str)

        for i in range(0, k + 4):
            if (i < k):
                self.Show([int(n_str[i-3]) if i-3 >= 0 else None, int(n_str[i-2]) if i-2 >= 0 else None, int(n_str[i-1]) if i-1 >= 0 else None, int(n_str[i]) if i >= 0 else None])
            elif (i >= k):
                self.Show([int(n_str[i-3]) if (i-3 < k and i-3 >= 0) else None, int(n_str[i-2]) if (i-2 < k and i-2 >= 0) else None, int(n_str[i-1]) if (i-1 < k and i-1 >= 0) else None, None])
            sleep(1)

    def SetBrightness(self, percent):
        """Accepts percent brightness from 0 - 1"""
        max_brightness = 7.0
        brightness = math.ceil(max_brightness * percent)
        if (brightness < 0):
            brightness = 0
        if(self.__brightness != brightness):
            self.__brightness = brightness
            self.Show(self.__currentData)

    def ShowDoublepoint(self, on):
        """Show or hide double point divider"""
        if(self.__doublePoint != on):
            self.__doublePoint = on
            self.Show(self.__currentData)

    def writeByte(self, data):
        for i in range(0, 8):
            GPIO.output(self.__Clkpin, GPIO.LOW)
            if(data & 0x01):
                GPIO.output(self.__Datapin, GPIO.HIGH)
            else:
                GPIO.output(self.__Datapin, GPIO.LOW)
            data = data >> 1
            GPIO.output(self.__Clkpin, GPIO.HIGH)
 
        # wait for ACK
        GPIO.output(self.__Clkpin, GPIO.LOW)
        GPIO.output(self.__Datapin, GPIO.HIGH)
        GPIO.output(self.__Clkpin, GPIO.HIGH)
        GPIO.setup(self.__Datapin, GPIO.IN)

        while(GPIO.input(self.__Datapin)):
            sleep(0.001)
            if(GPIO.input(self.__Datapin)):
                GPIO.setup(self.__Datapin, GPIO.OUT)
                GPIO.output(self.__Datapin, GPIO.LOW)
                GPIO.setup(self.__Datapin, GPIO.IN)
        GPIO.setup(self.__Datapin, GPIO.OUT)

    def start(self):
        """send start signal to TM1637"""
        GPIO.output(self.__Clkpin, GPIO.HIGH)
        GPIO.output(self.__Datapin, GPIO.HIGH)
        GPIO.output(self.__Datapin, GPIO.LOW)
        GPIO.output(self.__Clkpin, GPIO.LOW)

    def stop(self):
        GPIO.output(self.__Clkpin, GPIO.LOW)
        GPIO.output(self.__Datapin, GPIO.LOW)
        GPIO.output(self.__Clkpin, GPIO.HIGH)
        GPIO.output(self.__Datapin, GPIO.HIGH)

    def br(self):
        """terse break"""
        self.stop()
        self.start()

    def coding(self, data):
        if(self.__doublePoint):
            pointData = 0x80
        else:
            pointData = 0

        if(data == 0x7F or data is None):
            data = 0
        else:
            data = HexDigits[data] + pointData
        return data

    def clock(self, military_time):
        """Clock script modified from:
            https://github.com/johnlr/raspberrypi-tm1637"""
        self.ShowDoublepoint(True)
        while (not self.__stop_event.is_set()):
            t = localtime()
            hour = t.tm_hour
            if not military_time:
                hour = 12 if (t.tm_hour % 12) == 0 else t.tm_hour % 12
            d0 = hour // 10 if hour // 10 else 36
            d1 = hour % 10
            d2 = t.tm_min // 10
            d3 = t.tm_min % 10
            digits = [d0, d1, d2, d3]
            self.Show(digits)
            # # Optional visual feedback of running alarm:
            # print digits
            # for i in tqdm(range(60 - t.tm_sec)):
            for i in range(60 - t.tm_sec):
                if (not self.__stop_event.is_set()):
                    sleep(1)

    def StartClock(self, military_time=True):
        # Stop event based on: http://stackoverflow.com/a/6524542/3219667
        self.__stop_event = threading.Event()
        self.__clock_thread = threading.Thread(
            target=self.clock, args=(military_time,))
        self.__clock_thread.start()

    def StopClock(self):
        try:
            print ('Attempting to stop live clock')
            self.__stop_event.set()
        except:
            print ('No clock to close')

def LCDOFF():
    display = TM1637(CLK=21, DIO=20, brightness=1.0)
    display.Clear()

#LEDNUMBER
def LCD_NUMBER(scrap1):
    display = TM1637(CLK=21, DIO=20, brightness=1.0)
    display.Clear()
    if int(scrap1) >= 1000 :
       splitx = list(str(scrap1))
       display.Show1(1, int(splitx[1]))
       display.Show1(2, int(splitx[2]))
       display.Show1(3, int(splitx[3]))
       display.Show1(0, int(splitx[0]))
       return True
    if int(scrap1) >= 100 :
       splitx = list(str(scrap1))
       display.Show1(1, int(splitx[0]))
       display.Show1(2, int(splitx[1]))
       display.Show1(3, int(splitx[2]))
    else:
        if int(scrap1) >= 10 :
         splitx = list(str(scrap1))
         display.Show1(2, int(splitx[0]))
         display.Show1(3, int(splitx[1]))
        else:
          display.Show1(3, int(scrap1))

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#update
#sudo apt remove python3-rpi.gpio
#pip3 install rpi-lgpio

gpio_sensor = 5  # เซนเซอร์นับเหรียญ
gpio_relay = 17
counter = 0
time_start = round(time.time(),1)
time_end = round(time.time(),1)
status_gpi = 1
MONEY = 0
ON_0 = 0
ON_1 = 0
r = 0
isSum = 0
myLcd = 0
GPIO.setup(17,GPIO.IN)
GPIO.setup(12,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)

GPIO.setup(int(gpio_sensor),GPIO.IN)
#GPIO.add_event_detect(int(gpio_sensor),GPIO.BOTH,callback=sensor_callback2)
NORELAY = 1

isCheck = 0
def sensor(ch) :
   global CC_SEN,isCheck,counter,NORELAY,MONEY,json_data
   mySession = GPIO.input(ch)
   #print("GPIO17",GPIO.output(17,0))
   if counter <= 0 and NORELAY == 1 :
     GPIO.setup(17,GPIO.IN)
     NORELAY = 0
     CC_SEN = 0
     update_data(json_data)
     LCDOFF()
     print("Close")

   if mySession == 1 and isCheck == 0 :
     counter = counter - 1
     MONEY = MONEY - 10
     json_data["wallet"]["coin"] = json_data["wallet"]["coin"] + 10
     json_data["wallet"]["out"] = json_data["wallet"]["out"] + 1

     LCD_NUMBER(1)
     print("sensor",mySession)

   isCheck = mySession

GPIO.add_event_detect(5,GPIO.BOTH,callback=sensor)


def sendcoin_ok(maxcoint):
  global NORELAY,counter,MONEY,isSum,myLcd,json_data
 #try:
  isok = 1
  isSum = 0
  oldSum = 0
  GPIO.setup(17,GPIO.OUT)

def destroy():
    print("--------") 
    GPIO.cleanup()


CC_SEN = 0
def sensor_callback(channel):
    global CC_SEN,NORELAY,counter,MONEY,status_gpi,time_start,time_end,ON_0,ON_1,json_data
    checkGPOI = GPIO.input(channel)
    time_start = round(time.time(),1)
    if checkGPOI == 1 :
       time_start = round(time.time(),1)
       #status_gpi = 1

    if checkGPOI == 0 :
       time_end = round(time.time(),1)
       #status_gpi = 0

    if checkGPOI == 1 and status_gpi == 0 :
       MONEY = MONEY +10
       json_data["wallet"]["MONEY"] = json_data["wallet"]["MONEY"] + 10
       json_data["wallet"]["in"] = json_data["wallet"]["in"] + 1
       counter = counter +1
       #LCD_NUMBER(MONEY) 
       if counter >= 1 and CC_SEN == 0 :
         CC_SEN = 1
         NORELAY = 1
         sendcoin_ok(counter)

    #print(MONEY,checkGPOI,status_gpi)

    status_gpi = checkGPOI
    CC_SEN = checkGPOI
       

GPIO.add_event_detect(12,GPIO.BOTH,callback=sensor_callback)

LCD_NUMBER(MONEY)

def UpdateOnline(app,data):
    headers = {"Content-Type": "application/json"}
    url = str("https://app-wash.all123th.com/api/")+str(app)
    requests.put(url, data=json.dumps(data), headers=headers)
    url = "http://localhost:"+str(API_PORT)
    subprocess.Popen(['chromium-browser','--start-fullscreen','--kiosk',url]) 

@app.route('/sendcoin',methods=['GET'])
def send_coint():
    global counter,MONEY,NORELAY,CC_SEN,json_data
    count = int(request.args.get('count'))
    if not count:
        LCDOFF()
        MONEY = 0
        counter = 0
        return jsonify({"status": "error"}), 200
    if count <= 9 :
        LCDOFF()
        MONEY = 0
        counter = 0
        return jsonify({"status": "error"}), 200

    counter = count/10
    MONEY = count
    LCD_NUMBER(MONEY)
    json_data["wallet"]["qrcode"] = json_data["wallet"]["qrcode"] + MONEY
    CC_SEN = 0
    NORELAY = 1

    #GPIO.setup(17,GPIO.OUT)
    sendcoin_ok(counter)
    msg = {}
    msg['status'] = "success"
    msg['msg'] = "ok"
    return jsonify(msg),200

@app.route('/lcd',methods=['GET'])
def lcd_view():
    count = request.args.get('number')
    if not count:
        return jsonify({"status": "error"}), 200
    LCD_NUMBER(count)
    msg = {}
    msg['status'] = "success"
    msg['msg'] = "ok"
    return jsonify(msg),200


@app.route('/api',methods=['GET'])
def get_api():
    return jsonify(update_data(json_data)),200

@app.route('/reset_all',methods=['GET'])
def reset_all():
    json_data["wallet"]["MONEY"] = 0
    json_data["wallet"]["in"] = 0
    json_data["wallet"]["out"] = 0
    json_data["wallet"]["coin"] = 0
    json_data["wallet"]["qrcode"] = 0
    return jsonify(update_data(json_data)),200

@app.route('/reset_in',methods=['GET'])
def reset_in():
    json_data["wallet"]["in"] = 0
    return jsonify(update_data(json_data)),200

@app.route('/reset_money',methods=['GET'])
def reset_money():
    json_data["wallet"]["MONEY"] = 0
    return jsonify(update_data(json_data)),200

@app.route('/reset_out',methods=['GET'])
def reset_out():
    json_data["wallet"]["out"] = 0
    return jsonify(update_data(json_data)),200

@app.route('/set',methods=['GET'])
def reset_in_set():
    pset = request.args.get('set')
    if not pset:
        return jsonify({"status": "error"}), 200
    pval = request.args.get('val')
    if not pval:
        return jsonify({"status": "error"}), 200
    json_data["wallet"][str(pset)] = int(pval)
    return jsonify(update_data(json_data)),200


if __name__ == '__main__':
  try:
    url = "http://localhost:"+str(API_PORT)
    subprocess.Popen(['chromium-browser','--start-fullscreen','--kiosk',url]) 
    app.run(host='0.0.0.0', port=API_PORT, debug=DEBUG_MODE)
  finally:
    GPIO.setup(17,GPIO.IN)
    LCDOFF()