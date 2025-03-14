#https://private-user-images.githubusercontent.com/191635996/422769524-bd831ecf-651c-410b-a59f-8e03e5c643dd.jpg?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDE5NTI5ODEsIm5iZiI6MTc0MTk1MjY4MSwicGF0aCI6Ii8xOTE2MzU5OTYvNDIyNzY5NTI0LWJkODMxZWNmLTY1MWMtNDEwYi1hNTlmLThlMDNlNWM2NDNkZC5qcGc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUwMzE0JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MDMxNFQxMTQ0NDFaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT0zM2Q3ZjFjMzAyNmUxMzIwNjU3MzMzZjQ3MjU3ZTBhMzU3MzY5N2MwZDc1MTMzN2ZjODMyODAyNjM5MjFjNjE2JlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.q3-4kC_QGwDU8cuGrChBElD2EE9nu8QxtZAvMOPyGzM


from machine import Pin
import time
from tm1637 import TM1637

# กำหนดขา GPIO
counter_pin = Pin(23, Pin.IN)
relay_pin = Pin(22, Pin.OUT)
add_button_pin = Pin(19, Pin.IN, Pin.PULL_UP)  # ขาสำหรับปุ่มเพิ่มเหรียญ (pull-up resistor ภายใน)
dio = Pin(2, Pin.OUT)
clk = Pin(4, Pin.OUT)

# สร้างออบเจ็กต์ TM1637
display = TM1637(dio, clk)

# ตัวแปร
count = 0
target_count = 5  # จำนวนเงินที่ต้องการนับ

# ฟังก์ชันนับเงิน (จากเครื่องนับเงิน)
def count_money():
  global count
  if counter_pin.value() == 1 and count < target_count:  # ตรวจสอบว่านับถึงเป้าหมายแล้วหรือยัง
    count += 1
    time.sleep_ms(50)  # ป้องกันการนับซ้ำ

# ฟังก์ชันเพิ่มเงินด้วยปุ่มกด
def add_money():
  global count
  if add_button_pin.value() == 0 and count < target_count:  # ตรวจสอบว่าปุ่มถูกกดและนับถึงเป้าหมายหรือยัง
    count += 1
    time.sleep_ms(50)  # ป้องกันการนับซ้ำ

# ฟังก์ชันควบคุมรีเลย์
def control_relay(state):
  relay_pin.value(state)

# ฟังก์ชันแสดงตัวเลข
def show_number(number):
  display.number(number)

# ฟังก์ชันหลัก
def main():
  # เริ่มต้น GPIO
  counter_pin.irq(trigger=Pin.IRQ_RISING, handler=count_money)

  while True:
    # ตรวจสอบการกดปุ่มเพิ่มเงิน
    add_money()

    # แสดงจำนวนเงินที่นับได้
    print("Count:", count)
    show_number(count)  # แสดงบนจอ 4-digit display

    # ควบคุมรีเลย์ (ตัวอย่าง: เปิดรีเลย์เมื่อนับได้ 10)
    if count >= 10:
      control_relay(1)  # เปิดรีเลย์
    else:
      control_relay(0)  # ปิดรีเลย์

    # ตรวจสอบว่านับถึงเป้าหมายแล้วหรือยัง
    if count >= target_count:
      print("นับครบ", target_count, "เหรียญแล้ว")
      break  # หยุดการนับ

    time.sleep_ms(100)

if __name__ == "__main__":
  main()
