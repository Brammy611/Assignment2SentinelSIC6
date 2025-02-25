from machine import Pin, ADC, PWM
import network
import utime as time
import dht
import urequests as requests

# **🔹 Konfigurasi jaringan**
FLASK_SERVER = "http://192.168.238.229:5000/send_data"  # Ganti dengan IP Flask server
WIFI_SSID = "ceweknya senku"
WIFI_PASSWORD = "senku111"

# **🔹 Koneksi WiFi**
def connect_wifi():
    wifi_client = network.WLAN(network.STA_IF)
    wifi_client.active(True)
    
    if not wifi_client.isconnected():
        print("🔄 Menghubungkan ke WiFi...")
        wifi_client.connect(WIFI_SSID, WIFI_PASSWORD)
        
        timeout = 10  
        while not wifi_client.isconnected() and timeout > 0:
            print("🔄 Menyambungkan...")
            time.sleep(1)
            timeout -= 1
    
    if wifi_client.isconnected():
        print("✅ WiFi Terhubung! IP:", wifi_client.ifconfig()[0])
    else:
        print("❌ Gagal menghubungkan ke WiFi")

    return wifi_client

wifi_client = connect_wifi()

# **🔹 Konfigurasi sensor**
dht_sensor = dht.DHT11(Pin(21))  
pir_sensor = Pin(22, Pin.IN)  

# **🔹 Konfigurasi LDR**
ldr_pin = ADC(Pin(34))  
ldr_pin.atten(ADC.ATTN_11DB)  

# **🔹 Konfigurasi LED dan Buzzer**
led = Pin(5, Pin.OUT)   
buzzer = PWM(Pin(18), freq=2000, duty=0)  

motion_count = 0  
light_on_duration = 0  
last_pir_state = 0  
light_on = False  

# **🔹 Fungsi membaca sensor**
def read_sensors():
    global last_pir_state, motion_count

    try:
        dht_sensor.measure()
        time.sleep_ms(500)  
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
    except Exception as e:
        print("❌ Error membaca sensor DHT11:", e)
        temperature, humidity = None, None

    pir_state = pir_sensor.value()

    if pir_state == 1 and last_pir_state == 0:
        motion_count += 1  

    last_pir_state = pir_state  
    return temperature, humidity, motion_count

# **🔹 Fungsi membaca LDR**
def read_ldr():
    ldr_value = ldr_pin.read()
    print(f"Nilai LDR: {ldr_value}")  # Debugging
    return ldr_value

# **🔹 Fungsi mengirim data ke Flask**
def send_data(temperature, humidity, motion, light_duration, ldr_value):
    headers = {"Content-Type": "application/json"}
    data = {
        "temperature": temperature,
        "humidity": humidity,
        "motion": motion,
        "light_duration": light_duration,
        "ldr_value": ldr_value  
    }
    
    try:
        response = requests.post(FLASK_SERVER, json=data, headers=headers)
        print("✅ Data Dikirim ke Flask!")
        print("Response:", response.text)
    except Exception as e:
        print("❌ Gagal mengirim data ke Flask:", e)


# **🔹 Loop utama**
while True:
    if not wifi_client.isconnected():
        print("🔄 WiFi terputus! Menghubungkan kembali...")
        wifi_client = connect_wifi()

    temp, hum, motion = read_sensors()
    ldr_value = read_ldr()  

    if ldr_value < 3500:
        led.value(0)  
        light_on = False  
        buzzer.duty(0)  
    else:
        led.value(1)  
        light_on = True  
        buzzer.duty(1023)  

    if light_on:
        light_on_duration += 0.5  

    if temp is not None and hum is not None:
        print(f"🌡 Suhu: {temp}°C, 💧 Kelembaban: {hum}%")
        send_data(temp, hum, motion, light_on_duration, ldr_value)  

    time.sleep(5)
