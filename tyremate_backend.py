import asyncio
from bleak import BleakScanner, BleakClient
import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
from datetime import datetime
import mysql.connector
import qrcode
from PIL import Image, ImageTk
import os
import logging
import json

TARGET_NAME = "Tyremate"
WRITE_UUID = "2d86686a-53dc-25b3-0c4a-f0e10c8dee20"
NOTIFY_UUID = "9e1547ba-c365-57b5-2947-c5e1c1e1d528"
LOG_FILE = "tyremate_log.txt"

DB_CONFIG = {
    'host': 'localhost',
    'port': 3307,
    'user': 'root',
    'password': '',
    'database': 'tyremate_data'
}

class TyremateApp:
    def __init__(self, root, config=None, stop_callback=None):
        self.root = root
        self.config = config or {}
        self.stop_callback = stop_callback
        self.separator = self.config.get("separator", ",")
        self.fields = self.config.get("fields", {})

        logging.basicConfig(
            filename="tyremate_error.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

        if isinstance(self.root, tk.Tk):
            self.root.title("Tyremate BLE Monitor")
            self.root.geometry("1000x700")

        self.running = False
        self.client = None
        self.loop = None
        self.scanning = False
        self.db_connection = None
        self.current_qr_image = None
        self.current_sensor_id = None
        self.current_qr_path = None

        self.create_widgets()
        self.setup_async()
        self.initialize_database()

        if self.config.get("log_enabled"):
            self.initialize_log_file()

    def setup_async(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_async_loop, daemon=True)
        self.thread.start()

    def run_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_panel = ttk.LabelFrame(main_frame, text="Sensor QR Code", padding=10)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5)

        self.qr_label = ttk.Label(right_panel)
        self.qr_label.pack(pady=10)

        self.sensor_id_label = ttk.Label(right_panel, text="No Sensor Connected", font=('Helvetica', 12, 'bold'))
        self.sensor_id_label.pack()

        # Add Buttons Below QR Code
        self.qr_buttons_frame = ttk.Frame(right_panel)
        self.qr_buttons_frame.pack(pady=(10, 5))

        self.view_table_button = ttk.Button(self.qr_buttons_frame, text="📋 View Table", command=self.view_db_table)
        self.view_table_button.pack(side=tk.LEFT, padx=10)

        self.view_log_button = ttk.Button(self.qr_buttons_frame, text="📓 View Notepad Log", command=self.view_notepad_log)
        self.view_log_button.pack(side=tk.LEFT, padx=10)

        
        control_frame = ttk.LabelFrame(left_panel, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        self.scan_btn = ttk.Button(control_frame, text="Start Scan", command=self.toggle_scan)
        self.scan_btn.pack(side=tk.LEFT, padx=5)

        db_frame = ttk.LabelFrame(left_panel, text="Database Status", padding=10)
        db_frame.pack(fill=tk.X, padx=5, pady=5)

        self.db_status = scrolledtext.ScrolledText(db_frame, height=2, state=tk.DISABLED)
        self.db_status.pack(fill=tk.X)

        info_frame = ttk.LabelFrame(left_panel, text="Device Status", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        self.device_info = scrolledtext.ScrolledText(info_frame, height=4, state=tk.DISABLED)
        self.device_info.pack(fill=tk.X)

        data_frame = ttk.LabelFrame(left_panel, text="Sensor Data", padding=10)
        data_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.data_display = scrolledtext.ScrolledText(data_frame, state=tk.DISABLED)
        self.data_display.pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def initialize_log_file(self):
        try:
            if not os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'w') as f:
                    f.write("Timestamp,Sensor ID,Pressure (PSI),Temperature (°C),Voltage (V),Raw Data\n")
                self.append_to_db_status(f"📝 Created log file: {LOG_FILE}\n")
            else:
                self.append_to_db_status(f"📝 Using existing log file\n")
        except Exception as e:
            self.append_to_db_status(f"❌ Log file error: {str(e)}\n")

    def log_to_notepad(self, data):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"{timestamp},{data['Sensor ID']},{data['Pressure (PSI)']},{data['Temperature (°C)']},{data['Voltage (V)']},{data['Raw Data']}\n"
            with open(LOG_FILE, 'a') as f:
                f.write(log_line)
            self.append_to_data_display("📝 Logged to notepad\n")
        except Exception as e:
            self.append_to_data_display(f"❌ Log error: {str(e)}\n")

    def initialize_database(self):
        try:
            self.db_connection = mysql.connector.connect(**DB_CONFIG)
            cursor = self.db_connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            cursor.execute(f"USE {DB_CONFIG['database']}")
            cursor.execute("SHOW TABLES LIKE 'sensor_readings'")
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE TABLE sensor_readings (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        timestamp DATETIME,
                        sensor_id VARCHAR(10),
                        pressure_psi DECIMAL(5,2),
                        temperature DECIMAL(5,2),
                        voltage DECIMAL(5,3),
                        raw_data VARCHAR(50),
                        qr_code_path VARCHAR(255)
                    )
                """)
                self.db_connection.commit()
            self.append_to_db_status("✅ DB Ready\n")
            cursor.close()
        except Exception as e:
            self.append_to_db_status(f"❌ DB Error: {str(e)}\n")
            self.db_connection = None
    def view_db_table(self):
        try:
            os.system("start chrome http://localhost/phpmyadmin")  # Adjust if using SQLite or another DB viewer
        except Exception as e:
            self.append_to_data_display(f"❌ Could not open DB Viewer: {e}\n")

    def view_notepad_log(self):
        try:
            log_path = "tyremate_log.txt"  # Adjust to your actual log file path
            os.startfile(log_path)
        except Exception as e:
            self.append_to_data_display(f"❌ Could not open log file: {e}\n")

    def generate_qr_code(self, sensor_data, sensor_id):
        try:
            values = [sensor_id]
            if self.fields.get("pressure"):
                values.append(str(sensor_data['Pressure (PSI)']))
            if self.fields.get("temperature"):
                values.append(str(sensor_data['Temperature (°C)']))
            if self.fields.get("battery"):
                values.append(str(sensor_data['Voltage (V)']))
            if self.fields.get("datetime"):
                values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            if self.fields.get("raw"):
                values.append(sensor_data["Raw Data"])

            qr_data = self.separator.join(values)
            qr = qrcode.make(qr_data)
            qr_dir = "qr_codes"
            os.makedirs(qr_dir, exist_ok=True)
            qr_path = f"{qr_dir}/sensor_{sensor_id}_{datetime.now().strftime('%d%m%Y')}.png"

            qr.save(qr_path)
            self.current_qr_path = qr_path

            img = Image.open(qr_path).resize((200, 200))
            self.current_qr_image = ImageTk.PhotoImage(img)
            self.qr_label.config(image=self.current_qr_image)
            self.sensor_id_label.config(text=f"Sensor ID: {sensor_id}")
            self.append_to_data_display(f"📲 QR Generated: {qr_data}\n")
        except Exception as e:
            self.append_to_data_display(f"❌ QR Error: {str(e)}\n")

    
           

    def toggle_scan(self):
        if not self.scanning:
            self.start_scan()
        else:
            self.stop_scan()

    def start_scan(self):
        self.scanning = True
        self.scan_btn.config(text="Stop Scan")
        asyncio.run_coroutine_threadsafe(self.scan_and_connect(), self.loop)
        self.append_to_device_info("🔍 Starting scan...\n")
        self.update_status("Scanning")

    def stop_scan(self):
        self.scanning = False
        self.scan_btn.config(text="Start Scan")
        asyncio.run_coroutine_threadsafe(self.disconnect_if_connected(), self.loop)
        self.append_to_device_info("🛑 Scan stopped\n")
        self.update_status("Ready")

        if self.stop_callback and self.current_qr_image:
            self.stop_callback(self.current_qr_image)

    async def scan_and_connect(self):
        while self.scanning:
            try:
                self.update_status("🔍 Scanning...")
                devices = await BleakScanner.discover(timeout=5)
                tyremate = next((d for d in devices if d.name == TARGET_NAME), None)
                if tyremate:
                    self.append_to_device_info(f"✅ Found {tyremate.name}\n")
                    self.client = BleakClient(tyremate.address)
                    await self.client.connect()
                    await self.client.start_notify(NOTIFY_UUID, self.notification_handler)
                    await self.client.write_gatt_char(WRITE_UUID, bytearray([0xA5]), response=True)
                    while self.scanning and self.client.is_connected:
                        await asyncio.sleep(1)
                    await self.client.disconnect()
                else:
                    self.append_to_device_info("❌ Tyremate not found. Retrying...\n")
                await asyncio.sleep(2)
            except Exception as e:
                self.append_to_device_info(f"⚠️ Scan error: {str(e)}\n")

    async def disconnect_if_connected(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()

    def decode_tyremate_notification(self, data: bytes):
        if len(data) < 10:
            return {}
        pressure_raw = int.from_bytes([data[5], data[6]], byteorder='big')
        temp_raw = data[7]
        voltage_raw = data[8]
        return {
            "Sensor ID": f"{data[1]:02X}{data[2]:02X}",
            "Pressure (PSI)": round((pressure_raw / 6.895) - 15, 2),
            "Temperature (°C)": temp_raw - 52,
            "Voltage (V)": round((voltage_raw + 150) / 100, 3),
            "Raw Data": data.hex().upper()
        }

    def notification_handler(self, sender, data):
        decoded = self.decode_tyremate_notification(data)
        self.generate_qr_code(decoded, decoded['Sensor ID'])
        output = f"📥 Received: {decoded['Raw Data']}\n"
        output += f"Sensor ID: {decoded['Sensor ID']}, Pressure: {decoded['Pressure (PSI)']} PSI, Temp: {decoded['Temperature (°C)']}°C, Volt: {decoded['Voltage (V)']}V\n"
        self.root.after(0, self.append_to_data_display, output)
        if self.save_to_database(decoded):
            if self.config.get("log_enabled"):
                self.log_to_notepad(decoded)

    def save_to_database(self, sensor_data):
        if not self.db_connection:
            return False
        try:
            cursor = self.db_connection.cursor()
            query = """
                INSERT INTO sensor_readings 
                (timestamp, sensor_id, pressure_psi, temperature, voltage, raw_data, qr_code_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                datetime.now(),
                sensor_data['Sensor ID'],
                sensor_data['Pressure (PSI)'],
                sensor_data['Temperature (°C)'],
                sensor_data['Voltage (V)'],
                sensor_data['Raw Data'],
                self.current_qr_path
            )
            cursor.execute(query, values)
            self.db_connection.commit()
            cursor.close()
            return True
        except Exception as e:
            self.append_to_data_display(f"❌ DB Save Error: {str(e)}\n")
            return False

    def append_to_data_display(self, text):
        self.data_display.config(state=tk.NORMAL)
        self.data_display.insert(tk.END, text)
        self.data_display.config(state=tk.DISABLED)
        self.data_display.see(tk.END)

    def append_to_device_info(self, text):
        self.device_info.config(state=tk.NORMAL)
        self.device_info.insert(tk.END, text)
        self.device_info.config(state=tk.DISABLED)
        self.device_info.see(tk.END)

    def append_to_db_status(self, text):
        self.db_status.config(state=tk.NORMAL)
        self.db_status.insert(tk.END, text)
        self.db_status.config(state=tk.DISABLED)
        self.db_status.see(tk.END)

    def update_status(self, text):
        self.status_var.set(text)

    def on_closing(self):
        self.scanning = False
        if self.loop:
            asyncio.run_coroutine_threadsafe(self.disconnect_if_connected(), self.loop)
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.db_connection and self.db_connection.is_connected():
            self.db_connection.close()
        self.root.destroy()


# Standalone mode (for testing)
if __name__ == "__main__":
    root = tk.Tk()
    app = TyremateApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
