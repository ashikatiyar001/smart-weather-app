// ==========================================================
// Daily Briefing — Frontend Logic
// ==========================================================

const state = {
  unit: "metric",
  lastCity: "",
  lastPayload: null,
};

// ---------- DOM refs ----------
const cityInput = document.getElementById("cityInput");
const searchForm = document.getElementById("searchForm");
const unitToggle = document.getElementById("unitToggle");
const goBtn = document.querySelector(".go-btn");
const statusMsg = document.getElementById("statusMsg");
const briefing = document.getElementById("briefing");
const historyChips = document.getElementById("historyChips");
const modeToggle = document.getElementById("modeToggle");

// ---------- Dark mode ----------
modeToggle.addEventListener("click", () => {
  document.body.classList.toggle("dark");
});

// ---------- Unit toggle ----------
unitToggle.addEventListener("click", () => {
  state.unit = state.unit === "metric" ? "imperial" : "metric";
  unitToggle.textContent = state.unit === "metric" ? "°C" : "°F";
  if (state.lastCity) fetchWeather(state.lastCity);
});

// ---------- Search ----------
searchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const city = cityInput.value.trim();
  if (city) fetchWeather(city);
});

// ---------- History chips (delegated, since chips get re-rendered) ----------
historyChips.addEventListener("click", (e) => {
  const btn = e.target.closest(".chip");
  if (btn) {
    const city = btn.dataset.city;
    cityInput.value = city;
    fetchWeather(city);
  }
});

// ---------- Status helpers ----------
function showStatus(text, isError = false) {
  statusMsg.hidden = false;
  statusMsg.textContent = text;
  statusMsg.classList.toggle("error", isError);
}
function hideStatus() {
  statusMsg.hidden = true;
}

// ---------- Fetch weather ----------
async function fetchWeather(city) {
  goBtn.disabled = true;
  goBtn.textContent = "…";
  showStatus("Weather laa rahe hain…");
  briefing.hidden = true;

  try {
    const res = await fetch(`/api/weather?city=${encodeURIComponent(city)}&unit=${state.unit}`);
    const data = await res.json();

    if (!res.ok) {
      showStatus(data.error || "Kuch galat ho gaya", true);
      return;
    }

    hideStatus();
    state.lastCity = data.city;
    state.lastPayload = data;
    renderBriefing(data);
    renderHistoryChips(data.history);
    loadMoodChart(data.city);

  } catch (err) {
    showStatus("Server se connect nahi ho paya. Flask app chal raha hai kya?", true);
  } finally {
    goBtn.disabled = false;
    goBtn.textContent = "Dekho";
  }
}

// ---------- Render history chips ----------
function renderHistoryChips(history) {
  if (!history || !history.length) return;
  historyChips.innerHTML = history
    .map((c) => `<button class="chip" data-city="${c}">${c}</button>`)
    .join("");
}

// ---------- Render main briefing ----------
function renderBriefing(data) {
  briefing.hidden = false;

  document.getElementById("weatherIcon").src = `https://openweathermap.org/img/wn/${data.icon}@2x.png`;
  document.getElementById("tempValue").textContent = data.temp;
  document.getElementById("unitLabel").textContent = data.unit_symbol;
  document.getElementById("cityName").textContent = data.city;
  document.getElementById("conditionDesc").textContent = data.description;
  document.getElementById("humidityValue").textContent = `${data.humidity}%`;
  document.getElementById("windValue").textContent = `${data.wind_speed} m/s`;

  // Rain alert
  const rainSection = document.getElementById("rainAlert");
  if (data.rain_alert) {
    rainSection.hidden = false;
    document.getElementById("rainAlertText").textContent = data.rain_alert.message;
  } else {
    rainSection.hidden = true;
  }

  // AQI gauge
  renderAqiGauge(data.aqi);

  // Outfit advice
  const list = document.getElementById("adviceList");
  list.innerHTML = data.outfit_advice
    .map((a) => `<li><span class="adv-icon">${a.icon}</span><span>${a.text}</span></li>`)
    .join("");

  // Forecast strip
  const strip = document.getElementById("forecastStrip");
  strip.innerHTML = data.forecast
    .map(
      (d) => `
      <div class="forecast-day">
        <div class="f-date">${d.day_label}</div>
        <img src="https://openweathermap.org/img/wn/${d.icon}.png" alt="${d.condition}">
        <div class="f-temp">${d.temp}${data.unit_symbol}</div>
        <div class="f-cond">${d.condition}</div>
      </div>`
    )
    .join("");
}

// ---------- AQI gauge (semi-circle dial) ----------
function renderAqiGauge(aqi) {
  const label = document.getElementById("aqiLabel");
  const advice = document.getElementById("aqiAdvice");
  const fillPath = document.getElementById("gaugeFill");
  const needle = document.getElementById("gaugeNeedle");

  if (!aqi) {
    label.textContent = "N/A";
    advice.textContent = "AQI data abhi available nahi hai.";
    fillPath.style.strokeDasharray = "0 999";
    needle.style.transform = "rotate(0deg)";
    return;
  }

  const fraction = (aqi.aqi - 1) / 4; // 0 (good) -> 1 (very poor)
  const totalLength = fillPath.getTotalLength();
  fillPath.style.stroke = aqi.color;
  fillPath.style.strokeDasharray = `${totalLength}`;
  fillPath.style.strokeDashoffset = `${totalLength * (1 - fraction)}`;

  const angle = -90 + fraction * 180;
  needle.style.transform = `rotate(${angle}deg)`;

  label.textContent = `${aqi.label} (AQI ${aqi.aqi})`;
  advice.textContent = aqi.advice;
}

// ---------- Mood journal ----------
const moodPicker = document.getElementById("moodPicker");

moodPicker.addEventListener("click", async (e) => {
  const btn = e.target.closest(".mood-btn");
  if (!btn || !state.lastPayload) return;

  document.querySelectorAll(".mood-btn").forEach((b) => b.classList.remove("selected"));
  btn.classList.add("selected");

  const mood = btn.dataset.mood;

  try {
    await fetch("/api/mood", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mood: Number(mood),
        city: state.lastPayload.city,
        temp: state.lastPayload.temp,
        condition: state.lastPayload.condition,
      }),
    });
    loadMoodChart(state.lastPayload.city);
  } catch (err) {
    console.error("Mood save failed", err);
  }
});

async function loadMoodChart(city) {
  try {
    const res = await fetch(`/api/mood-history?city=${encodeURIComponent(city)}`);
    const data = await res.json();
    drawMoodChart(data.entries || []);
  } catch (err) {
    console.error("Mood history load failed", err);
  }
}

function drawMoodChart(entries) {
  const svg = document.getElementById("moodChart");
  const emptyMsg = document.getElementById("chartEmpty");
  svg.innerHTML = "";

  if (!entries.length) {
    emptyMsg.style.display = "block";
    return;
  }
  emptyMsg.style.display = "none";

  const W = 600, H = 180;
  const padL = 40, padR = 20, padT = 20, padB = 30;
  const innerW = W - padL - padR;
  const innerH = H - padT - padB;

  const n = entries.length;
  const xStep = n > 1 ? innerW / (n - 1) : 0;

  const svgns = "http://www.w3.org/2000/svg";
  const moodColor = { 1: "#D9634A", 2: "#E2A54D", 3: "#8A8F98", 4: "#7C9473", 5: "#5C8A63" };

  // Baseline grid (mood levels 1-5)
  for (let m = 1; m <= 5; m++) {
    const y = padT + innerH - ((m - 1) / 4) * innerH;
    const line = document.createElementNS(svgns, "line");
    line.setAttribute("x1", padL);
    line.setAttribute("x2", W - padR);
    line.setAttribute("y1", y);
    line.setAttribute("y2", y);
    line.setAttribute("stroke", "var(--paper-line)");
    line.setAttribute("stroke-width", "1");
    svg.appendChild(line);
  }

  // Points
  const points = entries.map((entry, i) => {
    const x = padL + i * xStep;
    const y = padT + innerH - ((entry.mood - 1) / 4) * innerH;
    return { x, y, entry };
  });

  // Dashed connecting path (hand-plotted feel)
  const pathData = points.map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(" ");
  const path = document.createElementNS(svgns, "path");
  path.setAttribute("d", pathData);
  path.setAttribute("fill", "none");
  path.setAttribute("stroke", "var(--dusk-soft)");
  path.setAttribute("stroke-width", "1.5");
  path.setAttribute("stroke-dasharray", "4 3");
  svg.appendChild(path);

  // Dots
  points.forEach((p) => {
    const circle = document.createElementNS(svgns, "circle");
    circle.setAttribute("cx", p.x);
    circle.setAttribute("cy", p.y);
    circle.setAttribute("r", 5);
    circle.setAttribute("fill", moodColor[p.entry.mood] || "#8A8F98");
    circle.setAttribute("stroke", "var(--paper-card)");
    circle.setAttribute("stroke-width", "2");

    const title = document.createElementNS(svgns, "title");
    title.textContent = `${p.entry.date} — Mood ${p.entry.mood}/5, ${p.entry.temp}° ${p.entry.condition}`;
    circle.appendChild(title);

    svg.appendChild(circle);
  });

  // X labels (only show a few to avoid clutter)
  const labelEvery = Math.max(1, Math.ceil(n / 6));
  points.forEach((p, i) => {
    if (i % labelEvery !== 0 && i !== n - 1) return;
    const text = document.createElementNS(svgns, "text");
    text.setAttribute("x", p.x);
    text.setAttribute("y", H - 8);
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("font-size", "9");
    text.setAttribute("font-family", "var(--font-mono)");
    text.setAttribute("fill", "var(--ink-soft)");
    text.textContent = p.entry.date.slice(5); // MM-DD
    svg.appendChild(text);
  });
}
