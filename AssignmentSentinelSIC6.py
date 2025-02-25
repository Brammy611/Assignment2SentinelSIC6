from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import requests

app = Flask(__name__)

# **🔹 Koneksi ke MongoDB**
MONGO_URI = "mongodb+srv://bramantyo989:jkGjM7paFoethotj@cluster0.zgafu.mongodb.net/?appName=Cluster0"  
client = MongoClient(MONGO_URI)
db = client["SentinelSIC"]
collection = db["SensorSentinel"]

# **🔹 Konfigurasi Ubidots**
UBIDOTS_TOKEN = "BBUS-uR3eDVaspOWqwibr9FTE1GRL4bSBTj"
UBIDOTS_URL = "https://industrial.api.ubidots.com/api/v1.6/devices/esp32-sic6-sentinel/"

# **🔹 Fungsi mengirim data ke Ubidots**
def send_to_ubidots(data):
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": UBIDOTS_TOKEN
    }
    
    formatted_data = {
        "temperature": {"value": data.get("temperature", 0)},
        "humidity": {"value": data.get("humidity", 0)},
        "motion": {"value": data.get("motion", 0)},
        "light_duration": {"value": data.get("light_duration", 0)},
        "ldr_value": {"value": data.get("ldr_value", 0)} 
    }

    try:
        response = requests.post(UBIDOTS_URL, json=formatted_data, headers=headers)
        print("✅ Data dikirim ke Ubidots:", response.text)
    except Exception as e:
        print("❌ Gagal mengirim ke Ubidots:", e)

# **🔹 Endpoint Utama**
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Flask API is running!"})

# **🔹 Endpoint untuk menerima data dari ESP32**
@app.route("/send_data", methods=["POST"])
def receive_data():
    try:
        data = request.json
        data["timestamp"] = datetime.utcnow()  
        
        # **Simpan ke MongoDB**
        collection.insert_one(data)
        
        # **Kirim data ke Ubidots**
        send_to_ubidots(data)

        return jsonify({"message": "Data berhasil disimpan dan dikirim ke Ubidots!", "data": data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# **🔹 Endpoint untuk mendapatkan data terbaru**
@app.route("/get_data", methods=["GET"])
def get_data():
    try:
        latest_data = collection.find().sort("timestamp", -1).limit(1)
        data_list = [doc for doc in latest_data]  

        for doc in data_list:
            doc["_id"] = str(doc["_id"])  

        return jsonify(data_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
