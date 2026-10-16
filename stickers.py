import json
import os
import tkinter as tk
from tkinter import colorchooser

APP_DIR = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "SimpleStickers")
DATA_FILE = os.path.join(APP_DIR, "stickers.json")
os.makedirs(APP_DIR, exist_ok=True)
DEFAULT_COLOR = "#fff59d"

class StickyNote:
    def __init__(self, app, data=None):
        self.app = app
        data = data or {}
        self.color = data.get("color", DEFAULT_COLOR)
        x, y = int(data.get("x", 120)), int(data.get("y", 120))
        w, h = int(data.get("width", 270)), int(data.get("height", 220))
        self.topmost = bool(data.get("topmost", False))
        self.win = tk.Toplevel(app.root)
        self.win.geometry(f"{w}x{h}+{x}+{y}")
        self.win.title("Стикер")
        self.win.configure(bg=self.color)
        self.win.attributes("-topmost", self.topmost)
        self.win.protocol("WM_DELETE_WINDOW", self.close)

        bar = tk.Frame(self.win, bg=self.color, padx=5, pady=4)
        bar.pack(fill="x")
        tk.Label(bar, text="Заметка", bg=self.color, font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Button(bar, text="Цвет", command=self.pick_color).pack(side="right", padx=(4, 0))
        self.pin = tk.Button(bar, text="📌 Поверх: " + ("ВКЛ" if self.topmost else "выкл"),
                             command=self.toggle_pin)
        self.pin.pack(side="right", padx=(4, 0))
        tk.Button(bar, text="+", command=app.new_note, width=2).pack(side="right", padx=(4, 0))

        self.text = tk.Text(self.win, wrap="word", undo=True, relief="flat",
                            font=("Segoe UI", 11), padx=8, pady=7,
                            bg=self.color, insertbackground="#222222")
        self.text.pack(fill="both", expand=True)
        self.text.insert("1.0", data.get("text", ""))
        self.text.bind("<KeyRelease>", lambda e: app.schedule_save())
        self.win.bind("<Configure>", lambda e: app.schedule_save() if e.widget == self.win else None)
        app.notes.append(self)

    def pick_color(self):
        color = colorchooser.askcolor(color=self.color, title="Цвет стикера")[1]
        if color:
            self.color = color
            self.win.configure(bg=color)
            for child in self.win.winfo_children():
                if isinstance(child, (tk.Frame, tk.Label)):
                    child.configure(bg=color)
            self.text.configure(bg=color)
            self.app.schedule_save()

    def toggle_pin(self):
        self.topmost = not self.topmost
        self.win.attributes("-topmost", self.topmost)
        self.pin.configure(text="📌 Поверх: " + ("ВКЛ" if self.topmost else "выкл"))
        self.app.schedule_save()

    def data(self):
        return {"text": self.text.get("1.0", "end-1c"), "color": self.color,
                "x": self.win.winfo_x(), "y": self.win.winfo_y(),
                "width": self.win.winfo_width(), "height": self.win.winfo_height(),
                "topmost": self.topmost}

    def close(self):
        if self in self.app.notes:
            self.app.notes.remove(self)
        self.win.destroy()
        self.app.schedule_save()

class App:
    def __init__(self):
        self.notes = []
        self.save_job = None
        self.root = tk.Tk()
        self.root.withdraw()
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            for item in saved:
                StickyNote(self, item)
        except (OSError, ValueError, TypeError):
            pass
        if not self.notes:
            self.new_note()
        self.control = tk.Toplevel(self.root)
        self.control.title("Стикеры")
        self.control.geometry("220x76+25+25")
        self.control.resizable(False, False)
        tk.Label(self.control, text="Мои стикеры", font=("Segoe UI", 11, "bold")).pack(pady=(7, 3))
        tk.Button(self.control, text="+ Новая заметка", command=self.new_note).pack()
        self.control.protocol("WM_DELETE_WINDOW", self.hide_control)
        self.root.mainloop()

    def hide_control(self):
        self.control.withdraw()

    def new_note(self):
        StickyNote(self)

    def schedule_save(self):
        if self.save_job:
            try: self.root.after_cancel(self.save_job)
            except tk.TclError: pass
        self.save_job = self.root.after(500, self.save)

    def save(self):
        self.save_job = None
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump([n.data() for n in self.notes], f, ensure_ascii=False, indent=2)
        except (OSError, tk.TclError):
            pass

if __name__ == "__main__":
    App()
