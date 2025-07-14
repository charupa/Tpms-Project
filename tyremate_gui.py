import tkinter as tk
from tkinter import ttk
import mysql.connector
import json
import os

CONFIG_FILE = "config.json"

class TyremateGUI:
    def __init__(self, root, start_callback=None):
        self.root = root
        self.start_callback = start_callback

        if isinstance(self.root, tk.Tk):
            self.root.title("Configuration")
            self.root.geometry("800x600")
            self.root.resizable(False, False)

        self.prev_config = self.load_config()

        self.db_enabled = tk.BooleanVar(value=bool(self.prev_config.get("host")))
        self.log_enabled = tk.BooleanVar(value=self.prev_config.get("log_enabled", False))
        self.separator = tk.StringVar(value=self.prev_config.get("separator", "|"))
        self.db_status_msg = tk.StringVar(value="Not tested")
        self.table_status_msg = tk.StringVar(value="")

        self.fields = {
            'datetime': tk.BooleanVar(value=self.prev_config.get("fields", {}).get("datetime", False)),
            'pressure': tk.BooleanVar(value=self.prev_config.get("fields", {}).get("pressure", False)),
            'temperature': tk.BooleanVar(value=self.prev_config.get("fields", {}).get("temperature", False)),
            'battery': tk.BooleanVar(value=self.prev_config.get("fields", {}).get("battery", False)),
            'raw': tk.BooleanVar(value=self.prev_config.get("fields", {}).get("raw", False)),
        }

        self.host_var = tk.StringVar(value=self.prev_config.get("host", "localhost"))
        self.port_var = tk.StringVar(value=self.prev_config.get("port", "3307"))
        self.user_var = tk.StringVar(value=self.prev_config.get("user", "root"))
        self.pass_var = tk.StringVar(value=self.prev_config.get("password", ""))

        self.create_gui()

    def create_gui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        ble_frame = ttk.LabelFrame(main_frame, text="BLE Settings", padding=10)
        ble_frame.pack(fill="x", pady=5)

        ttk.Label(ble_frame, text="Target Name:").grid(row=0, column=0, sticky="w")
        ttk.Label(ble_frame, text="Tyremate").grid(row=0, column=1, sticky="w")

        ttk.Label(ble_frame, text="Notify UUID:").grid(row=1, column=0, sticky="w")
        ttk.Label(ble_frame, text="15005991-b131-3396-014c-664c9867b917").grid(row=1, column=1, sticky="w")

        ttk.Label(ble_frame, text="Write UUID:").grid(row=2, column=0, sticky="w")
        ttk.Label(ble_frame, text="default-write-uuid").grid(row=2, column=1, sticky="w")

        db_frame = ttk.LabelFrame(main_frame, text="Database & Log Settings", padding=10)
        db_frame.pack(fill="x", pady=5)

        db_check = ttk.Checkbutton(db_frame, text="Enable DB Saving", variable=self.db_enabled, command=self.toggle_db_fields)
        db_check.grid(row=0, column=0, sticky="w")

        reset_btn = ttk.Button(db_frame, text="🔁", width=2, command=self.reset_db_defaults)
        reset_btn.grid(row=0, column=1, sticky="w", padx=5)

        self.log_check = ttk.Checkbutton(db_frame, text="Enable Notepad Log", variable=self.log_enabled)
        self.log_check.grid(row=1, column=0, columnspan=2, sticky="w")

        status_frame = ttk.Frame(db_frame)
        status_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(status_frame, textvariable=self.db_status_msg, foreground="gray").pack(side="left")
        ttk.Label(status_frame, textvariable=self.table_status_msg, foreground="green").pack(side="left", padx=10)

        btn_frame = ttk.Frame(db_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=2, sticky="w")
        ttk.Button(btn_frame, text="Test DB Connection", command=self.test_db_connection).pack(side="left")
        self.view_btn = ttk.Button(btn_frame, text="View Table", command=self.view_table)
        self.view_btn.pack(side="left", padx=5)
        self.view_btn.pack_forget()

        self.host_label = ttk.Label(db_frame, text="Host:")
        self.host_entry = ttk.Entry(db_frame, textvariable=self.host_var)

        self.port_label = ttk.Label(db_frame, text="Port:")
        self.port_entry = ttk.Entry(db_frame, textvariable=self.port_var)

        self.user_label = ttk.Label(db_frame, text="User:")
        self.user_entry = ttk.Entry(db_frame, textvariable=self.user_var)

        self.pass_label = ttk.Label(db_frame, text="Password:")
        self.pass_entry = ttk.Entry(db_frame, textvariable=self.pass_var, show="*")

        self.table_frame = ttk.LabelFrame(db_frame, text="🧹 Table Creation", padding=10)
        self.table_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
        self.table_frame.grid_remove()

        ttk.Label(self.table_frame, text="Database Name:").grid(row=0, column=0, sticky="w")
        self.dbname_var = tk.StringVar(value="tyremate_data")
        ttk.Entry(self.table_frame, textvariable=self.dbname_var).grid(row=0, column=1, sticky="ew")

        ttk.Label(self.table_frame, text="Table Name:").grid(row=1, column=0, sticky="w")
        self.tablename_var = tk.StringVar(value="sensor_readings")
        ttk.Entry(self.table_frame, textvariable=self.tablename_var).grid(row=1, column=1, sticky="ew")

        create_btn = ttk.Button(self.table_frame, text="Create Table", command=self.create_table)
        create_btn.grid(row=2, column=0, columnspan=2, pady=5)

        qr_frame = ttk.LabelFrame(main_frame, text="QR Code Configuration", padding=10)
        qr_frame.pack(fill="x", pady=5)

        ttk.Label(qr_frame, text="Separator:").grid(row=0, column=0, sticky="w")
        sep_menu = ttk.OptionMenu(qr_frame, self.separator, self.separator.get(), "|", ",", " ")
        sep_menu.grid(row=0, column=1, sticky="w")

        row = 1
        col = 0
        for key, var in self.fields.items():
            cb = ttk.Checkbutton(qr_frame, text=key.capitalize(), variable=var)
            cb.grid(row=row, column=col, sticky="w", padx=5, pady=2)
            col += 1

        self.output = ttk.Label(main_frame, text="Sensor Data: Waiting...", padding=10, background="white", anchor="w")
        self.output.pack(fill="x", pady=5)

        start_btn = ttk.Button(main_frame, text="Start Scan", command=self.launch_main_gui)
        start_btn.pack(pady=10)

        delete_btn = ttk.Button(main_frame, text="🗑️ Delete Previous Readings", command=self.delete_previous_readings)
        delete_btn.pack(pady=5)

        self.toggle_db_fields()

    def toggle_db_fields(self):
        widgets = [
            (self.host_label, self.host_entry),
            (self.port_label, self.port_entry),
            (self.user_label, self.user_entry),
            (self.pass_label, self.pass_entry),
        ]
        for i, (label, entry) in enumerate(widgets, start=4):
            if self.db_enabled.get():
                label.grid(row=i, column=0, sticky="w")
                entry.grid(row=i, column=1, sticky="ew")
            else:
                label.grid_remove()
                entry.grid_remove()

    def reset_db_defaults(self):
        self.host_var.set("localhost")
        self.port_var.set("3307")
        self.user_var.set("root")
        self.pass_var.set("")
        self.output.config(text="🔁 DB fields set to default.")

    def test_db_connection(self):
        try:
            conn = mysql.connector.connect(
                host=self.host_var.get(),
                port=int(self.port_var.get() or 3307),
                user=self.user_var.get(),
                password=self.pass_var.get(),
                database="tyremate_data"
            )
            conn.close()
            self.db_status_msg.set("\u2705 Connected")
            self.table_frame.grid()
        except Exception as e:
            self.db_status_msg.set(f"❌ {str(e)}")
            self.table_frame.grid_remove()

    def create_table(self):
        db_name = self.dbname_var.get()
        table_name = self.tablename_var.get()
        try:
            conn = mysql.connector.connect(
                host=self.host_var.get(),
                port=int(self.port_var.get() or 3307),
                user=self.user_var.get(),
                password=self.pass_var.get(),
                database=db_name
            )
            cursor = conn.cursor()
            create_query = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sensor_id VARCHAR(20),
                pressure FLOAT,
                temperature FLOAT,
                battery FLOAT,
                raw_data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(create_query)
            conn.commit()
            conn.close()
            self.output.config(text=f"✅ Table `{table_name}` created in `{db_name}`.")
            self.table_frame.grid_remove()
            self.table_status_msg.set(f"✅ Table '{table_name}' created successfully.")
            self.view_btn.pack()
        except Exception as e:
            self.output.config(text=f"❌ Table creation failed: {e}")
            self.table_status_msg.set("")

    def delete_previous_readings(self):
        if not (self.db_enabled.get() and self.log_enabled.get() and any(v.get() for v in self.fields.values())):
            self.output.config(text="❌ Enable DB, Notepad Log & select at least one field to delete.")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Confirm Deletion")
        popup.geometry("340x280")
        popup.resizable(False, False)

        ttk.Label(popup, text="🧹 Select what you want to delete:", font=("Segoe UI", 11)).pack(pady=10)
        delete_choice = tk.StringVar(value="all")
        options = [
            ("🧹 All (DB + QR + Log)", "all"),
            ("🖼️ QR Codes Only", "qr"),
            ("🗃️ Database Only", "db"),
            ("🗒️ Log File Only", "log")
        ]

        for text, value in options:
            ttk.Radiobutton(popup, text=text, variable=delete_choice, value=value).pack(anchor="w", padx=30, pady=2)

        def confirm_and_delete():
            choice = delete_choice.get()
            messages = []

            if choice in ("all", "db"):
                try:
                    conn = mysql.connector.connect(
                        host=self.host_var.get(),
                        port=int(self.port_var.get()),
                        user=self.user_var.get(),
                        password=self.pass_var.get(),
                        database="tyremate_data"
                    )
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM sensor_readings")
                    conn.commit()
                    conn.close()
                    messages.append("DB rows deleted")
                except Exception as e:
                    messages.append(f"DB deletion failed: {e}")

            if choice in ("all", "log"):
                try:
                    if os.path.exists("tyremate_log.txt"):
                        open("tyremate_log.txt", "w").close()
                    messages.append("Log file cleared")
                except Exception as e:
                    messages.append(f"Log clear failed: {e}")

            if choice in ("all", "qr"):
                try:
                    qr_folder = "qr_codes"
                    if os.path.exists(qr_folder):
                        for filename in os.listdir(qr_folder):
                            os.remove(os.path.join(qr_folder, filename))
                    messages.append("QR codes deleted")
                except Exception as e:
                    messages.append(f"QR delete failed: {e}")

            self.output.config(text="✅ " + ", ".join(messages))
            popup.destroy()

        button_frame = ttk.Frame(popup)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="✅ Yes", command=confirm_and_delete).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="❌ Cancel", command=popup.destroy).grid(row=0, column=1, padx=10)

    def view_table(self):
        db_name = self.dbname_var.get()
        table_name = self.tablename_var.get()
        try:
            conn = mysql.connector.connect(
                host=self.host_var.get(),
                port=int(self.port_var.get() or 3307),
                user=self.user_var.get(),
                password=self.pass_var.get(),
                database=db_name
            )
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM `{table_name}`")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            conn.close()
        except Exception as e:
            self.output.config(text=f"❌ View failed: {e}")
            return

        view_window = tk.Toplevel(self.root)
        view_window.title(f"{table_name} in {db_name}")
        view_window.geometry("700x400")

        tree = ttk.Treeview(view_window, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        for row in rows:
            tree.insert("", "end", values=row)

        tree.pack(fill="both", expand=True)
        ttk.Button(view_window, text="Close", command=view_window.destroy).pack(pady=10)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
        return {}

    def launch_main_gui(self):
        config = {
            "host": self.host_var.get() if self.db_enabled.get() else "",
            "port": self.port_var.get() if self.db_enabled.get() else "",
            "user": self.user_var.get() if self.db_enabled.get() else "",
            "password": self.pass_var.get() if self.db_enabled.get() else "",
            "log_enabled": self.log_enabled.get(),
            "separator": self.separator.get(),
            "fields": {k: v.get() for k, v in self.fields.items()}
        }
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

        if self.start_callback:
            self.start_callback(config)
        else:
            from sattry import TyremateApp
            self.root.destroy()
            root2 = tk.Tk()
            app = TyremateApp(root2, config)
            root2.protocol("WM_DELETE_WINDOW", app.on_closing)
            root2.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = TyremateGUI(root)
    root.mainloop()
