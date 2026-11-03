# TRMNL · WillyWeather Curve

Private plugin. Hourly or 7-day view, one API call per refresh. Works on OG (800×480, 1-bit) and X (1872×1404, 4-bit); scales from viewport.

## Setup
1. TRMNL → Plugins → Private Plugin → new.
2. **Form fields**: in `src/settings.yml` (`custom_fields`).
3. **Strategy**: Polling · GET · URL:
   ```
   https://api.willyweather.com.au/v2/{{ api_key }}/locations/{% if location_id == "other" %}{{ custom_location_id }}{% else %}{{ location_id }}{% endif %}/weather.json?forecasts=weather,temperature,precis,rainfall,rainfallprobability&days=7&observational=true
   ```
4. **Refresh**: 60 min (≈24 calls/day per plugin instance, shared across devices).
5. **Markup → Full**: `src/full.liquid`.
6. Add to playlist. For hourly + daily on same device: create two instances (mode differs), both in playlist.

## Location examples
Find the ID with `https://api.willyweather.com.au/v2/<key>/search.json?query=<name>` → `id` of the matching result.
| Place | Query | Location ID |
|---|---|---|
| Sydney | `query=Sydney` | `4950` |
| Canberra (International Airport) | `query=Canberra` | `19662` |

## Data used
| WW forecast | Granularity | Used for |
|---|---|---|
| `temperature` | hourly | hourly curve, current temp fallback |
| `precis` | 3-hourly | hourly icons, current condition |
| `rainfallprobability` | 3-hourly | hourly rain band (linear-interpolated) |
| `weather` | daily | max/min curves, daily icons |
| `rainfall` | daily | daily rain % (fallback: max of 3-hourly) |
| `observational` | latest | current temp (optional; drop `&observational=true` if not subscribed) |

## Notes / risks
- Key sits in polling URL path (WW has no header auth). Masked in TRMNL UI via `password` field but still in TRMNL server-side request logs. Higher-assurance option: proxy (Azure Function/Lambda, key in Key Vault, TRMNL authenticates with own bearer token, proxy trims payload + caches).
- Timezone: uses `location.timeZone` from WW response via `Intl`; fallback `trmnl.user.utc_offset`.
- Rendering is client-side JS in TRMNL's headless renderer; relies on Liquid `json` filter.
- Only full layout; half/quadrant mashup layouts not built.
- Field shapes (`precisCode`, `night`, `probability`, `min`/`max`) from WW v2; verify against a live response — `preview/mock_weather.json` shows expected shape.

## Preview
`python3 preview/render.py` → `preview/out/*.png` (mock data, OG + 1-bit sim + X).

## GitHub sync
1. Create empty private repo.
2. TRMNL: create private plugin → GitHub sync widget → connect repo (folder blank or e.g. `plugins/willyweather`). TRMNL pushes stub `src/` + `.trmnlp.yml`.
3. `git pull`, overwrite `src/` with this repo's files (keep TRMNL's `.trmnlp.yml` or merge), push.
4. TRMNL prompts import → accept. GitHub→TRMNL is manual; TRMNL→GitHub automatic on Save.
5. Set API key in plugin settings in TRMNL UI (never in repo).

Local dev: `gem install trmnl_preview && WILLYWEATHER_API_KEY=… trmnlp serve`.
