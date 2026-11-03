"""Render full.liquid with mock WillyWeather data at TRMNL OG (800x480, 1-bit) and X (1872x1404) sizes."""
import json, math, random, sys, datetime as dt
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image

HERE = Path(__file__).parent
OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
random.seed(4)
start = dt.date(2026, 11, 3)
codes = ["partly-cloudy", "showers-rain", "mostly-fine", "chance-thunderstorm-showers", "fine", "cloudy", "chance-shower-fine"]
maxs, mins, rain = [24, 21, 26, 28, 25, 22, 23], [15, 16, 14, 18, 17, 15, 14], [20, 80, 10, 60, 5, 30, 40]
fc = {k: {"days": []} for k in ["weather", "temperature", "precis", "rainfallprobability", "rainfall"]}
for d in range(7):
    day = start + dt.timedelta(days=d); ds = day.isoformat()
    fc["weather"]["days"].append({"dateTime": ds + " 00:00:00", "entries": [{"dateTime": ds + " 00:00:00", "precisCode": codes[d], "precis": codes[d].replace("-", " ").capitalize(), "min": mins[d], "max": maxs[d]}]})
    fc["rainfall"]["days"].append({"dateTime": ds + " 00:00:00", "entries": [{"dateTime": ds + " 00:00:00", "probability": rain[d], "startRange": 0, "endRange": 5}]})
    te, pe, re = [], [], []
    for h in range(24):
        g = d*24+h; v = (mins[d]+maxs[d])/2 + (maxs[d]-mins[d])/2*math.cos((h-15)/24*2*math.pi) + 0.6*math.sin(g/7)
        te.append({"dateTime": f"{ds} {h:02d}:00:00", "temperature": round(v, 1)})
        if h % 3 == 0:
            night = h < 6 or h >= 19
            c = codes[d] if 9 <= h <= 18 else ("fine" if rain[d] < 30 else "showers-rain")
            if d == 0 and h >= 18: c = "partly-cloudy"
            if d == 1 and h in (3, 6): c = "chance-shower-cloud"
            pe.append({"dateTime": f"{ds} {h:02d}:00:00", "precisCode": c, "precis": c.replace("-", " ").capitalize(), "night": night})
            re.append({"dateTime": f"{ds} {h:02d}:00:00", "probability": max(0, min(100, rain[d] + random.randint(-25, 15)))})
    fc["temperature"]["days"].append({"dateTime": ds + " 00:00:00", "entries": te})
    fc["precis"]["days"].append({"dateTime": ds + " 00:00:00", "entries": pe})
    fc["rainfallprobability"]["days"].append({"dateTime": ds + " 00:00:00", "entries": re})

payload = {"location": {"id": 4950, "name": "Sydney", "timeZone": "Australia/Sydney"}, "forecasts": fc,
           "observational": {"observations": {"temperature": {"temperature": 19.4}}}}
(HERE / "mock_weather.json").write_text(json.dumps(payload, indent=1))

src = (HERE.parent / "src" / "full.liquid").read_text()
def render(mode, hours):
    s = src.replace("{{ location | json }}", json.dumps(payload["location"]))
    s = s.replace("{{ forecasts | json }}", json.dumps(fc)).replace("{{ observational | json }}", json.dumps(payload["observational"]))
    s = s.replace("{{ trmnl.plugin_settings.custom_fields_values.mode | default: 'hourly' }}", mode)
    s = s.replace("{{ trmnl.plugin_settings.custom_fields_values.hours | default: '24' }}", str(hours))
    s = s.replace("{{ trmnl.user.utc_offset | default: 0 }}", "39600")
    s = s.replace("utcOffset:", 'nowOverride: "2026-11-03 21:47:00", utcOffset:')
    return "<!doctype html><html><head><meta charset='utf-8'></head><body style='margin:0'>" + s + "</body></html>"

with sync_playwright() as p:
    b = p.chromium.launch()
    for mode, hours in [("hourly", 24), ("daily", 24), ("hourly", 12)]:
        html = render(mode, hours)
        for name, (w, h) in {"og": (800, 480), "x": (1872, 1404)}.items():
            if hours == 12 and name == "x": continue
            pg = b.new_page(viewport={"width": w, "height": h})
            errs = []; pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None); pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.set_content(html); pg.wait_for_timeout(300)
            f = OUT / f"{mode}{hours}_{name}.png"; pg.screenshot(path=str(f))
            if name == "og": Image.open(f).convert("L").convert("1").save(OUT / f"{mode}{hours}_{name}_1bit.png")
            if name == "x": Image.open(f).convert("L").quantize(16).convert("L").save(f)
            print(f.name, errs or "ok"); pg.close()
    b.close()
