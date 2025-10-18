import tkinter as tk
import pyotp
import time
import pygetwindow as gw
import threading
import pystray
from PIL import Image, ImageDraw
import sys
import os

def load_properties(path="properties.txt"):
    props = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    props[k.strip()] = v.strip()
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
    return props

props = load_properties()
SECRET = props.get("key")
if not SECRET:
    tmp = tk.Tk()
    tmp.withdraw()
    messagebox.showerror("2FA - Missing secret",
                         "Could not find 'key=' in properties.txt.\n\n"
                         "Example:\nkey=YOURSECRET\n")
    tmp.destroy()
    sys.exit(1)

WINDOW_TITLES = [t.strip() for t in props.get("window.titles", "").split(",") if t.strip()]

if not WINDOW_TITLES:
    WINDOW_TITLES = ["PuTTY", "2FA - Imran", "Termius"]  # default fallback

totp = pyotp.TOTP(SECRET)

# --- System Tray ---
def create_image():
    """Generate a simple tray icon"""
    size = 64
    image = Image.new("RGB", (size, size), (255, 255, 255))
    dc = ImageDraw.Draw(image)
    dc.rectangle((0, 0, size, size), fill=(50, 150, 250))
    dc.text((size//4, size//4), "2F", fill=(255, 255, 255))
    return image

def on_exit(icon, item):
    icon.stop()
    root.quit()

def setup_tray():
    icon = pystray.Icon("2FA Helper")
    icon.icon = create_image()
    icon.menu = pystray.Menu(pystray.MenuItem("Exit", on_exit))
    icon.run()

#---------

def update_code():
    code = totp.now()
    remaining = 30 - int(time.time()) % 30
    code_label.config(text=code)
    timer_label.config(text=f"Valid for {remaining}s")
    root.after(1000, update_code)

def monitor_focus():
    try:
        active = gw.getActiveWindow()
        if active and "PuTTY" in active.title or "2FA - Imran" in active.title or "Termius" in active.title:
            root.deiconify()
        else:
            root.withdraw()
    except:
        pass
    root.after(1000, monitor_focus)

# --- Dragging logic ---
def start_drag(event):
    root._drag_x = event.x
    root._drag_y = event.y

def do_drag(event):
    x = root.winfo_x() + (event.x - root._drag_x)
    y = root.winfo_y() + (event.y - root._drag_y)
    root.geometry(f"+{x}+{y}")

# --- Click-to-copy ---
def copy_code(event=None):
    code = code_label.cget("text")
    root.clipboard_clear()
    root.clipboard_append(code)
    root.update()  # Keeps clipboard even after closing
    # temporary feedback
    timer_label.config(text="✅ Copied!")
    root.after(1500, update_code)
    
# GUI setup
root = tk.Tk()
root.title("2FA - Imran")
root.resizable(False, False)
root.overrideredirect(True)


frame = tk.Frame(root, bg="white")
frame.pack()

code_label = tk.Label(frame, text="", font=("Consolas", 28, "bold"), fg="black", bg="white")
code_label.pack()

timer_label = tk.Label(frame, text="", font=("Arial", 10), bg="white")
timer_label.pack()

update_code()
monitor_focus()
root.attributes("-topmost", True)

# Bind drag to the whole frame
root.bind("<Button-1>", start_drag)
root.bind("<B1-Motion>", do_drag)

# Bind click-to-copy
code_label.bind("<Button-1>", copy_code)

# Tray-- Run tray in a separate thread
threading.Thread(target=setup_tray, daemon=True).start()
# ------

root.mainloop()
