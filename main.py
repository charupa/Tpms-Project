import tkinter as tk
from tkinter import ttk
from tyremate_gui import TyremateGUI  # your config class
from tyremate_backend import TyremateApp     # your main scan class

class UnifiedTyremateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tyremate System")
        self.root.geometry("1000x700")

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill='both', expand=True)

        # Create frames for each tab
        self.config_frame = ttk.Frame(self.tabs)
        self.scan_frame = ttk.Frame(self.tabs)

        self.tabs.add(self.config_frame, text="Configuration")
        self.tabs.add(self.scan_frame, text="Scan")

        # Inject config tab with callback to switch to scan tab
        self.config_page = TyremateGUI(self.config_frame, self.start_scan_in_scan_tab)

    def start_scan_in_scan_tab(self, config):
        # Clear any old widgets in scan tab
        for widget in self.scan_frame.winfo_children():
            widget.destroy()
        # Load scan UI into scan_frame
        TyremateApp(self.scan_frame, config)
        # Switch to scan tab
        self.tabs.select(self.scan_frame)

if __name__ == "__main__":
    root = tk.Tk()
    app = UnifiedTyremateApp(root)
    root.mainloop()
