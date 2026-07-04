"""
Smart Weather Briefing - Flask Web App
----------------------------------------
Unique Features:
1. Smart Outfit & Health Advisor (temp + humidity + wind + condition combo)
2. AQI (Air Quality Index) integration with a dial gauge
3. Hyperlocal Rain Alert (agle kuch ghanton me barish ka chance, forecast 'pop' data se)
4. Mood-Weather Journal (mood log karo, weather ke saath correlate hoke chart banta hai)

Run:
    pip install flask requests
    python app.py
Phir browser me kholo: http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, jsonify
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)

# ---------------- CONFIG ----------------
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "YOUR_API_KEY_HERE") # <-- Apni API key (already filled)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "search_history.json")
MOOD_FILE = os.path.join(DATA_DIR, "mood_log.json")
MAX_HISTORY = 6

os.makedirs(DATA_DIR, exist_ok=True)


# ================= HELPERS: FILE STORAGE =================
def _read_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_search_history(city):
    history = _read_json(HISTORY_FILE, [])
    city = city.strip().title()
    if city in history:
        history.remove(city)
    history.insert(0, city)
    history = history[:MAX_HISTORY]
    _write_json(HISTORY_FILE, history)
    return history


# ================= HELPERS: WEATHER LOGIC =================
def get_outfit_advice(temp_c, humidity, wind_speed, condition):
    """Temp + humidity + wind + condition ka COMBINATION dekh ke specific advice."""
    advice = []

    if temp_c >= 35:
        advice.append({"icon": "🥵", "text": "Bahut garmi hai — loose, halke rang ke cotton clothes pehno."})
    elif temp_c >= 25:
        advice.append({"icon": "👕", "text": "Halka aur comfortable outfit theek rahega."})
    elif temp_c >= 15:
        advice.append({"icon": "🧥", "text": "Halki jacket saath rakho, shaam ko thand ho sakti hai."})
    elif temp_c >= 5:
        advice.append({"icon": "🧣", "text": "Thand hai — sweater ya jacket zaroor pehno."})
    else:
        advice.append({"icon": "❄️", "text": "Bahut thand hai — heavy woolens aur gloves pehno."})

    if humidity >= 70 and temp_c >= 25:
        advice.append({"icon": "💦", "text": "Humidity high hai — paani zyada piyo, hydrated raho."})
    elif humidity <= 30:
        advice.append({"icon": "🌵", "text": "Hawa dry hai — moisturizer use karo."})

    if wind_speed >= 8:
        advice.append({"icon": "💨", "text": "Tez hawa hai — dupatta/scarf sambhal ke, bike dhyan se chalao."})

    if "rain" in condition or "drizzle" in condition:
        advice.append({"icon": "☔", "text": "Umbrella ya raincoat zaroor rakho."})
    if "thunderstorm" in condition:
        advice.append({"icon": "⚡", "text": "Khule maidan/pedon ke neeche na jao."})
    if "clear" in condition and temp_c >= 28:
        advice.append({"icon": "🕶️", "text": "Sunglasses aur sunscreen carry karo."})

    if temp_c > 33 or (humidity > 75 and temp_c > 28):
        advice.append({"icon": "🏃", "text": "Outdoor exercise abhi avoid karo — heatstroke risk hai."})
    elif 15 <= temp_c <= 28 and "rain" not in condition:
        advice.append({"icon": "🚶", "text": "Outdoor walk ke liye aaj achha din hai!"})

    return advice


def get_rain_alert(forecast_json):
    """Agle ~9 ghanton (3 forecast slots) me rain probability check karta hai."""
    if not forecast_json or "list" not in forecast_json:
        return None

    upcoming = forecast_json["list"][:3]  # next ~9 hours (3-hour steps)
    best = max(upcoming, key=lambda e: e.get("pop", 0)) if upcoming else None

    if best and best.get("pop", 0) >= 0.4:
        time_str = best["dt_txt"].split(" ")[1][:5]
        chance = round(best["pop"] * 100)
        return {
            "message": f"Rain ka chance {chance}% hai, aaj {time_str} ke aas-paas.",
            "chance": chance,
            "time": time_str,
        }
    return None


def get_aqi_info(lat, lon):
    """OpenWeatherMap Air Pollution API se AQI (1-5 scale) fetch karta hai."""
    try:
        url = (
            f"http://api.openweathermap.org/data/2.5/air_pollution"
            OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "YOUR_API_KEY_HERE")
        )
        resp = requests.get(url, timeout=8)
        data = resp.json()
        aqi = data["list"][0]["main"]["aqi"]  # 1-5

        levels = {
            1: {"label": "Good", "color": "#7C9473", "advice": "Hawa saaf hai, bindaas bahar niklo."},
            2: {"label": "Fair", "color": "#A3B565", "advice": "Hawa theek hai, normal activities kar sakte ho."},
            3: {"label": "Moderate", "color": "#E2A54D", "advice": "Sensitive log (asthma/allergy) thoda dhyan rakhein."},
            4: {"label": "Poor", "color": "#D9634A", "advice": "Bahar zyada der na rukho, mask pehen sakte ho."},
            5: {"label": "Very Poor", "color": "#B23A2E", "advice": "Bahar nikalna avoid karo, N95 mask zaroor pehno."},
        }
        info = levels.get(aqi, levels[3])
        return {"aqi": aqi, **info}
    except Exception:
        return None


# ================= ROUTES =================
@app.route("/")
def index():
    history = _read_json(HISTORY_FILE, [])
    return render_template("index.html", history=history)


@app.route("/api/weather")
def api_weather():
    city = request.args.get("city", "").strip()
    unit = request.args.get("unit", "metric")

    if not city:
        return jsonify({"error": "City name chahiye"}), 400

    if OPENWEATHER_API_KEY == "YOUR_API_KEY_HERE":
        return jsonify({"error": "API key set nahi hai. app.py me OPENWEATHER_API_KEY daalein."}), 500

    try:
        cur_url = (
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={OPENWEATHER_API_KEY}&units={unit}"
        )
        cur_resp = requests.get(cur_url, timeout=8).json()

        if str(cur_resp.get("cod")) != "200":
            return jsonify({"error": "City nahi mili"}), 404

        forecast_url = (
            f"http://api.openweathermap.org/data/2.5/forecast"
            f"?q={city}&appid={OPENWEATHER_API_KEY}&units={unit}"
        )
        forecast_resp = requests.get(forecast_url, timeout=8).json()

        lat = cur_resp["coord"]["lat"]
        lon = cur_resp["coord"]["lon"]

        temp = cur_resp["main"]["temp"]
        humidity = cur_resp["main"]["humidity"]
        wind_speed = cur_resp["wind"]["speed"]
        condition = cur_resp["weather"][0]["main"].lower()
        description = cur_resp["weather"][0]["description"]
        icon = cur_resp["weather"][0]["icon"]

        temp_c = temp if unit == "metric" else (temp - 32) * 5 / 9

        outfit_advice = get_outfit_advice(temp_c, humidity, wind_speed, condition)
        rain_alert = get_rain_alert(forecast_resp)
        aqi_info = get_aqi_info(lat, lon)

        # 5-day forecast (approx daily, one entry per day)
        daily = {}
        for entry in forecast_resp.get("list", []):
            date_str = entry["dt_txt"].split(" ")[0]
            time_str = entry["dt_txt"].split(" ")[1]
            if time_str == "12:00:00" and date_str not in daily:
                daily[date_str] = entry
        if len(daily) < 5:
            for entry in forecast_resp.get("list", []):
                date_str = entry["dt_txt"].split(" ")[0]
                if date_str not in daily:
                    daily[date_str] = entry

        forecast_days = []
        for date_str, entry in list(daily.items())[:5]:
            forecast_days.append({
                "date": date_str,
                "day_label": date_str.split("-")[2] + "/" + date_str.split("-")[1],
                "temp": round(entry["main"]["temp"]),
                "icon": entry["weather"][0]["icon"],
                "condition": entry["weather"][0]["main"],
            })

        save_search_history(city)

        return jsonify({
            "city": cur_resp["name"],
            "temp": round(temp, 1),
            "humidity": humidity,
            "wind_speed": wind_speed,
            "condition": condition,
            "description": description.capitalize(),
            "icon": icon,
            "unit_symbol": "°C" if unit == "metric" else "°F",
            "outfit_advice": outfit_advice,
            "rain_alert": rain_alert,
            "aqi": aqi_info,
            "forecast": forecast_days,
            "history": _read_json(HISTORY_FILE, []),
        })

    except requests.exceptions.RequestException:
        return jsonify({"error": "Server se connect nahi ho paya. Internet check karein."}), 500
    except Exception as e:
        return jsonify({"error": f"Kuch galat ho gaya: {str(e)}"}), 500


@app.route("/api/mood", methods=["POST"])
def api_log_mood():
    payload = request.get_json(force=True)
    mood = payload.get("mood")
    city = payload.get("city")
    temp = payload.get("temp")
    condition = payload.get("condition")

    if not mood or not city:
        return jsonify({"error": "mood aur city chahiye"}), 400

    entries = _read_json(MOOD_FILE, [])
    entries.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "city": city,
        "mood": mood,
        "temp": temp,
        "condition": condition,
    })
    _write_json(MOOD_FILE, entries)
    return jsonify({"status": "saved", "entries": entries[-20:]})


@app.route("/api/mood-history")
def api_mood_history():
    city = request.args.get("city", "")
    entries = _read_json(MOOD_FILE, [])
    if city:
        entries = [e for e in entries if e["city"].lower() == city.lower()]
    return jsonify({"entries": entries[-30:]})


if __name__ == "__main__":
    app.run(debug=True)
