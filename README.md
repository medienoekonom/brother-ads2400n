# Brother ADS-2400N — Home Assistant Integration

A custom Home Assistant integration for the **Brother ADS-2400N** network document scanner. It polls the scanner's built-in web interface and exposes device status, page counters, roller life, and maintenance data as entities in Home Assistant.

> **No cloud. No special firmware. No extra software required.** The integration communicates directly with the scanner's HTTP web interface on your local network.

---

## Requirements

- Home Assistant 2023.1 or newer
- Brother ADS-2400N connected to your local network via Ethernet or Wi-Fi
- The scanner's web interface must be reachable from your Home Assistant host (port 80 by default)
- The web interface password (factory default: `initpass`)

> **Note:** This integration uses local polling via HTTP. The scanner does **not** need internet access and no data leaves your network.

---

## Installation

### Option A — HACS (recommended)

1. Open HACS in Home Assistant.
2. Go to **Integrations** → click the three-dot menu → **Custom repositories**.
3. Add `https://github.com/medienoekonom/brother-ads2400n` as an **Integration**.
4. Search for **Brother ADS-2400N** and click **Download**.
5. Restart Home Assistant.

### Option B — Manual

1. Download or clone this repository.
2. Copy the `custom_components/brother_ads2400n/` folder into your Home Assistant config directory:
   ```
   <config>/custom_components/brother_ads2400n/
   ```
3. Restart Home Assistant.

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Brother ADS-2400N**.
3. Enter:
   - **IP address or hostname** — the scanner's local IP (find it in your router or the scanner's network settings)
   - **Web interface password** — factory default is `initpass`
   - **HTTP port** — default is `80`, change only if you have a non-standard setup
4. Click **Submit**. Home Assistant will connect to the scanner and verify the credentials.

---

## Entities

After setup, the following entities are created under a single device entry:

### Sensors

| Entity | Description | Unit |
|--------|-------------|------|
| `sensor.*_device_status` | Current scanner state (Ready / Sleep / Scanning / Error / …) | — |
| `sensor.*_total_pages_scanned` | Cumulative total pages scanned (all-time) | pages |
| `sensor.*_adf_duplex_pages` | Cumulative duplex (2-sided) pages scanned | pages |
| `sensor.*_pick_up_roller_life` | Pick-up roller remaining life | % |
| `sensor.*_pick_up_roller_pages_remaining` | Pages remaining before pick-up roller replacement | pages |
| `sensor.*_reverse_roller_life` | Reverse roller remaining life | % |
| `sensor.*_reverse_roller_pages_remaining` | Pages remaining before reverse roller replacement | pages |
| `sensor.*_scheduled_maintenance_remaining` | Scheduled maintenance remaining | % |
| `sensor.*_maintenance_pages_until_service` | Pages remaining until next scheduled service | pages |

### Binary Sensors

| Entity | Description |
|--------|-------------|
| `binary_sensor.*_online` | `on` when the scanner is reachable on the network |
| `binary_sensor.*_ready` | `on` when the scanner is Ready, Scanning, or Warming Up |

Data is refreshed every **60 seconds**.

---

## Example Automations

**Notify when a roller needs replacement:**
```yaml
automation:
  - alias: "Brother Scanner — Pick-up Roller Low"
    trigger:
      - platform: numeric_state
        entity_id: sensor.brother_ads_2400n_pick_up_roller_life
        below: 20
    action:
      - service: notify.notify
        data:
          message: "Brother scanner: pick-up roller is below 20%. Plan a replacement soon."
```

**Notify when the scanner goes offline:**
```yaml
automation:
  - alias: "Brother Scanner — Offline Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.brother_ads_2400n_online
        to: "off"
        for: "00:05:00"
    action:
      - service: notify.notify
        data:
          message: "Brother ADS-2400N is not reachable."
```

---

## How It Works

The integration logs into the scanner's HTTP web interface (the same interface you use in a browser) and scrapes two pages:

- `/general/status.html` — device status
- `/general/information.html?kind=item` — counters, roller life, firmware, serial number

Authentication uses the scanner's built-in form login (field `B1264`). A session cookie is held for the duration of each poll cycle. No credentials are stored in plain text beyond what Home Assistant's config entry system provides (encrypted at rest).

The integration uses `aiohttp` (Home Assistant's native async HTTP library) — no blocking calls, no threads.

---

## Troubleshooting

**"Cannot connect" during setup**
- Verify the scanner is powered on and reachable: open `http://<scanner-ip>` in a browser from the same network.
- Check that port 80 is not blocked by a firewall between HA and the scanner.

**"Invalid auth" during setup**
- The password is wrong. Try `initpass` (factory default) or the password you set in the scanner's web interface under **Administrator → Login Password**.
- Make sure you are entering the **administrator** password, not a user-level one.

**Entities show `unavailable` after setup**
- The scanner went to sleep and is not responding. Most Brother network scanners enter deep sleep and stop responding to HTTP requests. The `binary_sensor.*_online` entity will reflect this. Entities recover automatically once the scanner wakes up (e.g. by pressing a button or sending a scan job).

**All roller percentages are `unknown`**
- The HTML structure of the web interface may differ slightly on your firmware version. Open an issue and include your firmware version (visible in the scanner's web interface under **General → Information**).

---

## Compatibility

Developed and tested on:
- **Brother ADS-2400N** (firmware as of early 2026)

The web interface layout is likely identical or very similar on related models (ADS-2800W, ADS-3600W, etc.). If you test it on another model, feel free to open an issue or PR to update this list.

---

## Contributing

Bug reports, firmware-version reports, and pull requests are welcome. Please open an issue first if you plan a larger change.

---

## License

MIT
