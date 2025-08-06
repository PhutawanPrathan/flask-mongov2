from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import threading
import time
import random
import os

app = Flask(__name__)
# Enable CORS for all routes to allow frontend from different domain
CORS(app, origins=["*"])

# MongoDB connection
MONGO_URI = os.environ.get('MONGO_URI', "mongodb+srv://projectEE:ee707178@cluster0.ttq1nzx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client["sensor_db"]
sensor_collection = db["sensor_data"]

# Create TTL index to auto-delete old data after 100 seconds
sensor_collection.create_index("timestamp", expireAfterSeconds=100)

def generate_random_sensor_data():
    """Generate random sensor data that mimics MPU6050 readings"""
    while True:
        try:
            # Generate random accelerometer data (-2g to +2g range)
            mpu1_ax = round(random.uniform(-2.0, 2.0), 3)
            mpu1_ay = round(random.uniform(-2.0, 2.0), 3)
            mpu1_az = round(random.uniform(-2.0, 2.0), 3)
            
            # Generate random gyroscope data (-250 to +250 degrees/sec)
            mpu1_gx = round(random.uniform(-250.0, 250.0), 3)
            mpu1_gy = round(random.uniform(-250.0, 250.0), 3)
            mpu1_gz = round(random.uniform(-250.0, 250.0), 3)
            
            # Generate random data for second MPU
            mpu2_ax = round(random.uniform(-2.0, 2.0), 3)
            mpu2_ay = round(random.uniform(-2.0, 2.0), 3)
            mpu2_az = round(random.uniform(-2.0, 2.0), 3)
            
            mpu2_gx = round(random.uniform(-250.0, 250.0), 3)
            mpu2_gy = round(random.uniform(-250.0, 250.0), 3)
            mpu2_gz = round(random.uniform(-250.0, 250.0), 3)
            
            # Insert data into MongoDB
            sensor_data = {
                "timestamp": datetime.now(),
                "mpu1_ax": mpu1_ax,
                "mpu1_ay": mpu1_ay,
                "mpu1_az": mpu1_az,
                "mpu1_gx": mpu1_gx,
                "mpu1_gy": mpu1_gy,
                "mpu1_gz": mpu1_gz,
                "mpu2_ax": mpu2_ax,
                "mpu2_ay": mpu2_ay,
                "mpu2_az": mpu2_az,
                "mpu2_gx": mpu2_gx,
                "mpu2_gy": mpu2_gy,
                "mpu2_gz": mpu2_gz,
            }
            
            sensor_collection.insert_one(sensor_data)
            print(f"✅ Random sensor data generated at {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"❌ Error generating sensor data: {e}")
        
        # Generate data every 2 seconds
        time.sleep(2)

# === API ROUTES ===
@app.route("/")
def home():
    """Health check endpoint"""
    return jsonify({
        "message": "Sensor API is running!",
        "status": "active",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/latest")
def get_latest():
    """Get latest 20 sensor readings"""
    try:
        data = list(sensor_collection.find().sort("timestamp", -1).limit(20))
        return jsonify([
            {
                "timestamp": d["timestamp"].strftime("%H:%M:%S"),
                **{k: d.get(k) for k in d if k != "_id" and k != "timestamp"}
            } for d in reversed(data)
        ])
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return jsonify([])

@app.route("/api/stats")
def get_stats():
    """Get basic statistics about the sensor data"""
    try:
        total_records = sensor_collection.count_documents({})
        latest_record = sensor_collection.find_one(sort=[("timestamp", -1)])
        
        stats = {
            "total_records": total_records,
            "latest_timestamp": latest_record["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if latest_record else "No data",
            "status": "active" if latest_record else "inactive"
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/health")
def health_check():
    """Health check for monitoring"""
    try:
        # Test MongoDB connection
        sensor_collection.find_one()
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# === ERROR HANDLERS ===
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# === START APPLICATION ===
if __name__ == '__main__':
    # Start the random data generation thread
    threading.Thread(target=generate_random_sensor_data, daemon=True).start()
    print("🚀 Starting Flask API server...")
    
    # Use environment port or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
