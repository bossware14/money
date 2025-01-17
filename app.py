from flask import Flask, request, jsonify, render_template,send_file 
from flask_socketio import SocketIO, emit, send
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
import logging, ngrok
import RPi.GPIO as GPIO
import threading
import math
from time import sleep, localtime

# port
API_PORT = 5000
# เซ็นเซอร์  


deviceId = str(uuid.getnode())
secret = os.urandom(24).hex()
DEBUG_MODE = False# โหมด ทดลอง  True|False
app = Flask(__name__,template_folder="")
app.logger.info("Starting...")
app.config['SECRET_KEY'] = secret
app.logger.critical("secret: %s" % secret)
#socketio = SocketIO(app,cors_allowed_origins="*")
#logging.basicConfig(level=logging.INFO)

CORS(app)
if os.path.isfile('cert.pem'):
    print('ok ssl')
else:
    os.system('pip install pyopenssl')
    print('create ssl')
    create_ssl = os.system('openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/C=TH/ST=Thailand/L=Bangkok/O=All123TH/CN=app-wash.all123th.com"')
    print(create_ssl)

def GetSerial():
    returned_output = uuid.getnode()#subprocess.call("cat /sys/firmware/devicetree/base/serial-number",shell=True)
    return returned_output

### end
@app.route('/')
def index():
    return render_template('money.html')

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


@app.route('/favicon.ico')
def favicon():
    filename = 'favicon.ico'
    return send_file(filename, mimetype='image/png')
    #return render_template('images.png')

@app.route('/ngrok')
def NGrok():
      subprocess.call("ngrok http http://localhost:"+str(API_PORT),shell=True)

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


if os.path.isfile('data.json'):
    with open('data.json', 'r') as f:
      json_data = json.load(f)
else:
    json_data = {
  "data": {
    "action": 0,
    "modewash": "modewash1",
    "monitor": "พร้อม",
    "msg": "พร้อม",
    "persen": "0",
    "runtime": "00:00:00",
    "sec": 0,
    "start": 0,
    "status": "STOP",
    "temperature": "temperature1",
    "time": "00:00:00",
    "timeout": "00:00:00",
    "update": "2024-12-01 00:00:00"
  },
  "date": "2024-12-20 00:00:00",
  "id": "a2d08c2d74594940ae6e6d39e96451bb",
  "ip": "127.0.0.1",
  "mode": {
    "modewash1": 15,
    "modewash2": 10,
    "modewash3": 30,
    "modewash4": 25
  },
  "msg": "พร้อมใช้งาน",
  "price": {
    "modewash1": 30,
    "modewash2": 30,
    "modewash3": 50,
    "modewash4": 40,
    "temperature1": 0,
    "temperature2": 30,
    "temperature3": 0
  },
  "status": "ONLINE"
}

tz = timezone(timedelta(hours = 7))
json_data['id'] = socket.gethostname()
json_data['date'] = datetime.now(tz=tz).strftime('%Y-%m-%d %H:%M:%S')
json_data['status'] = 'ONLINE'
json_data['msg'] = 'พร้อมใช้งาน'
json_data['ip'] = get_ip()
json_data['port'] = API_PORT
json_data['data']['time'] = datetime.now(tz=tz).strftime('%H:%M:%S')
json_data['serial-number'] = GetSerial()

def update_data(json_data):
    json_data['id'] = socket.gethostname()
    json_data['date'] = datetime.now(tz=tz).strftime('%Y-%m-%d %H:%M:%S')
    json_data['status'] = 'ONLINE'
    json_data['msg'] = 'พร้อมใช้งาน'
    json_data['ip'] = get_ip()
    json_data['data']['update'] = datetime.now(tz=tz).strftime('%Y-%m-%d %H:%M:%S')
    json_data['data']['time'] = datetime.now(tz=tz).strftime('%H:%M:%S')
    if json_data['data']['start'] ==  1 and json_data['data']['status'] == "START" :
                json_data['data']['time'] = datetime.now(tz=tz).strftime('%H:%M:%S')
                t1 = json_data['data']['timeout'].split(':')
                t2 = json_data['data']['time'].split(':')
                HOUR = int(t1[0]) - int(t2[0])
                MIN = int(t1[1]) - int(t2[1])
                SEC = int(t1[2]) - int(t2[2])
                xper = HOUR-MIN-SEC
                if xper <= 0 :
                    json_data['data']['persen'] = 100
                TOSEC = 0#int(json_data['data']['TIMSEC'])
                if HOUR > 0:
                    TOSEC = TOSEC + int(HOUR*60)
                if MIN > 0:
                    TOSEC = TOSEC + int(MIN*60)
                if SEC >= 0:
                    TOSEC = TOSEC + int(SEC)
                else:
                    TOSEC = TOSEC + int(SEC)
                    json_data['data']['runtime'] = str(HOUR)+':'+str(MIN)+':'+str(SEC)
                    json_data['data']['runtime'] = datetime.fromtimestamp(TOSEC).strftime('00:%M:%S')
                if HOUR <= 0 and MIN <= 0 and SEC <= 0:
                    json_data['data']['TIMSEC'] = 0
                    json_data['data']['runtime'] = "00:00:00"
                    json_data['data']['timeout'] = "00:00:00"
                    json_data['data']['msg'] = "ว่าง"
                    json_data['data']['monitor'] = "เสร็จแล้ว"
                    json_data['msg'] = 'พร้อมใช้งาน'
                    json_data['data']['minute'] = '00:00:00'
                    json_data['data']['status'] = 'STOP'
                    json_data['data']['start'] = 0
                    json_data['data']['action'] = 0
                    json_data['data']['persen'] = 100
                else:
                    json_data['data']['persen'] = 100-TOSEC*100/int(json_data['data']['sec'])
                    json_data['data']['TIMSEC'] = TOSEC
                    json_data['data']['msg'] = "กำลังทำงาน"
                    json_data['data']['monitor'] = "เครื่องกำลังปั่นผ้า"
                    json_data['data']['start'] = 1
                    json_data['msg'] = 'กำลังซัก'
                with open('data.json', 'w') as f:
                    json.dump(json_data, f) 
                return json_data
    else:
        json_data['data']['status'] = 'ONLINE'
    with open('data.json', 'w') as f:
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
#ขา 17 relay
LCDOFF()
#update
#sudo apt remove python3-rpi.gpio
#pip3 install rpi-lgpio
#ขา 17 relay
#
#print('จำนวนเหรียญ')
#maxcoint = input() #MAX
def sendcoin_ok(maxcoint):
 try:
  LCD_NUMBER(maxcoint)
  time.sleep(1)
  print('เริ่ม')
  LCD_NUMBER(0)
  inout = 'in'#input()
  if inout == 'in':
      GPIO.setup(int(gpio_relay),GPIO.OUT)
      GPIO.setup(int(gpio_sensor),GPIO.IN)
  if inout == 'out':
      GPIO.setup(int(gpio_sensor),GPIO.OUT)
  isok = 1
  isSum = 0
  oldSum = 0
  while True:
      lf1 = int(GPIO.input(int(gpio_sensor)))
      time.sleep(0.03) #ตั่งเวลานับเหรียญ
      if lf1 == 1 and isok == 0:
        isSum = isSum +1;
        print("coin : ",isSum)
        LCD_NUMBER(isSum)
        isok=1
        if isSum == int(maxcoint) :
           GPIO.setup(int(gpio_relay),GPIO.IN)
           break
      else:
        isok=0
        oldSum = isSum 

 finally:
     isok = 1
     isSum = 0
     oldSum = 0
     print("สิ้นสุด")
     #time.sleep(10)
     #LCDOFF()

def destroy():
    print("--------") 
    GPIO.cleanup()



def UpdateOnline(app,data):
    headers = {"Content-Type": "application/json"}
    url = str("https://app-wash.all123th.com/api/")+str(app)
    requests.put(url, data=json.dumps(data), headers=headers)
    url = "http://localhost:"+str(API_PORT)
    subprocess.Popen(['chromium-browser','--start-fullscreen','--kiosk',url]) 

@app.route('/sendcoin',methods=['GET'])
def send_coint():
    count = request.args.get('count')
    if not count:
        LCDOFF()
        return jsonify({"status": "error"}), 200
    sendcoin_ok(count)
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

if __name__ == '__main__':
    try :
      token = '2q6m1Gd0w8fEuibiwyToH0JEyfx_2ft99jvARhHn2u8Q2EPe1'
      ngrok.set_auth_token(token)
      listener = ngrok.forward("http://"+str(json_data['ip'])+":"+str(API_PORT))
      print(f"IP: "+str(listener.url()))
      json_data["url"] = str(listener.url())
    except:
      json_data["url"] = "offline"
      print(f"IP: None")
    
    UpdateOnline(json_data['serial-number'],json_data)
    app.run(host='0.0.0.0', port=API_PORT, debug=DEBUG_MODE)
    #socketio.run(app,host="0.0.0.0",port=API_PORT, debug=DEBUG_MODE)
    os.system("pkill chromium")
