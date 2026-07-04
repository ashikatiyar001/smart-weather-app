# Daily Briefing — Smart Weather Web App

Ek **Flask-based web app** jo sirf temperature nahi dikhata — 4 unique
features ke saath ek "personal weather briefing" deta hai.

## Unique Features
1. **Smart Outfit & Health Advisor** — temperature + humidity + wind +
   condition ka combination dekh ke real, specific advice deta hai
   (generic "umbrella lao" nahi).
2. **AQI Dial Gauge** — Air Quality Index ko ek analog instrument-panel
   style dial me dikhata hai, saath me health advice.
3. **Hyperlocal Rain Alert** — agle ~9 ghanton me rain ka chance ho toh
   proactively alert karta hai (time + probability ke saath).
4. **Mood-Weather Journal** — apna mood log karo, app ek hand-plotted
   style chart me tumhara mood aur weather ka pattern dikhata hai.

## Setup

```bash
cd weather_web_app
pip install -r requirements.txt
```

Phir `app.py` file kholo aur ye line dhoondo:

```python
OPENWEATHER_API_KEY = "YOUR_API_KEY_HERE"
```

Apni asli [OpenWeatherMap](https://openweathermap.org/api) free API
key daal do.

> Note: Air Pollution (AQI) API bhi wahi free API key se kaam karta hai,
> koi extra signup nahi chahiye.

## Run

```bash
python app.py
```

Terminal me ye dikhega:
```
Running on http://127.0.0.1:5000
```

Browser me ye URL kholo — **isse aap ek real web app ki tarah use kar
paoge**, VS Code me terminal chalu rakhna hoga jab tak app use karna ho.

## Folder Structure
```
weather_web_app/
├── app.py                # Flask backend (routes + weather logic)
├── requirements.txt
├── templates/
│   └── index.html        # Main page
├── static/
│   ├── style.css          # Design (instrument-panel / field-note theme)
│   └── script.js          # Frontend logic (fetch calls, gauge, chart)
└── data/                  # Auto-created — search history & mood logs
```

## Notes
- Data (search history, mood logs) JSON files me `data/` folder ke
  andar save hote hain — koi database setup nahi chahiye.
- Dark mode toggle (◐ icon) top-right corner me hai.
- App fully responsive hai — mobile browser me bhi test kar sakte ho
  (same WiFi par `http://<your-pc-ip>:5000` se).
