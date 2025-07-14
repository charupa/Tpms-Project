# Tyremate BLE TPMS Monitor

This project is a GUI application for monitoring Tire Pressure Monitoring System (TPMS) sensor data over BLE (Bluetooth Low Energy). It connects to a device named **"Tyremate"**, receives sensor data, displays it, generates QR codes, logs it to a notepad, and saves it into a MySQL database.

---

## 📦 Project Structure

```
TPMS/
│
├── config/              # config.json - stores QR and DB settings
├── qr_codes/            # generated QR code images
├── tyremate_gui.py      # main GUI + BLE logic (merged GUI + backend)
├── tyremate_backend.py  # (optional: for separating backend logic)
├── main.py              # entry point (can call GUI)
├── tyremate_log.txt     # plain text log of sensor data
├── tyremate_error.txt   # error logs
├── README.md            # project overview
├── requirements.txt     # dependencies
└── __pycache__/         # Python cache
```

---

## ✅ Features

- 🔍 BLE scanning for **Tyremate** device
- 🔔 Notification decoding: pressure, temperature, voltage, sensor ID
- 🧾 Realtime logging to MySQL
- 📓 Optional logging to `tyremate_log.txt`
- 📲 QR code generation from sensor data
- 📋 View database (opens phpMyAdmin)
- 📘 View notepad log (opens in Notepad)
- 💾 Configurable via `config.json`

---

## ⚙️ Requirements

- Python 3.9 or above
- MySQL (XAMPP recommended)
- BLE-compatible adapter

---

## 🔧 Setup Instructions

1. **Clone or Download** this repo.

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up MySQL**:
   - Start MySQL server (default port `3306` or `3307` if using XAMPP).
   - Ensure credentials match in `DB_CONFIG` inside `tyremate_gui.py`.

4. **Run the GUI**:
   ```bash
   python tyremate_gui.py
   ```

5. Configure optional logging and QR fields in `config.json`.

---

## 📝 Sample `config.json`

```json
{
  "separator": "-",
  "fields": {
    "pressure": true,
    "temperature": true,
    "battery": true,
    "datetime": true,
    "raw": false
  },
  "log_enabled": true
}
```

---

## 🚀 Future Enhancements

- Export data as CSV  
- Auto email reports  
- Mobile version  

---

## 📩 Author

**Charupa** | B.Tech CSE | TPMS BLE GUI Project | 2025
