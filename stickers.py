import json
import os
import tkinter as tk
from tkinter import colorchooser

APP_DIR = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "SimpleStickers")
DATA_FILE = os.path.join(APP_DIR, "stickers.json")
DEFAULT_COLOR = "#FFF2A6"
TEXT_COLOR = "#292929"

os.makedirs(APP_DIR, exist_ok=True)

class Sticker:
    def __init__(self, app, data=None):
        self.app = app
        data = data or {}
        self.color = data.get("color", DEFAULT_COLOR)
        self.pinned = bool(data.get("pinned", False))
        x, y = int(data.get("x", 120)), int(data.get("y", 120))
        width, height = int(data.get("width", 280)), int(data.get("height", 230))

        self.win = tk.Toplevel(app.root)
        self.win.title("Стикер")
        self.win.geometry(f"{width}x{height}+{x}+{y}")
        self.win.minsize(210, 150)
        self.win.configure(bg=self.color)
        self.win.attributes("-topmost", self.pinned)
        self.win.protocol("WM_DELETE_WINDOW", self.close)

        self.toolbar = tk.Frame(self.win, bg=self.color, height=34)
        self.toolbar.pack(fill="x", padx=7, pady=(6, 0))
        self.toolbar.pack_propagate(False)
        self.new_button = tk.Button(self.toolbar, text="+", command=self.app.new_sticker,
            font=("Segoe UI", 12), relief="flat", bd=0, bg=self.color,
            activebackground=self.color, fg=TEXT_COLOR, cursor="hand2", width=3)
        self.new_button.pack(side="left")
        self.menu_button = tk.Button(self.toolbar, text="⋯", command=self.show_menu,
            font=("Segoe UI", 16), relief="flat", bd=0, bg=self.color,
            activebackground=self.color, fg=TEXT_COLOR, cursor="hand2", width=3)
        self.menu_button.pack(side="right")

        self.text = tk.Text(self.win, wrap="word", undo=True, relief="flat", bd=0,
            font=("Segoe UI", 11), padx=10, pady=7, bg=self.color, fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR, selectbackground="#B9D7FF", spacing1=1, spacing3=2)
        self.text.pack(fill="both", expand=True, padx=7, pady=(0, 7))
        self.text.insert("1.0", data.get("text", ""))
        self.text.bind("<KeyRelease>", lambda _e: self.app.schedule_save())
        self.text.bind("<<Paste>>", lambda _e: self.app.schedule_save())
        self.text.bind("<<Cut>>", lambda _e: self.app.schedule_save())
        self.win.bind("<Configure>", self.on_configure)
        self.app.stickers.append(self)

    def on_configure(self, event):
        if event.widget == self.win:
            self.app.schedule_save()

    def apply_color(self, color):
        self.color = color
        self.win.configure(bg=color)
        self.toolbar.configure(bg=color)
        self.text.configure(bg=color)
        self.new_button.configure(bg=color, activebackground=color)
        self.menu_button.configure(bg=color, activebackground=color)

    def show_menu(self):
        menu = tk.Menu(self.win, tearoff=0, bg="#FFFFFF", fg=TEXT_COLOR,
            activebackground="#E8EEF8", activeforeground=TEXT_COLOR,
            font=("Segoe UI", 10), bd=0)
        menu.add_command(label="Снять закрепление" if self.pinned else "Закрепить поверх окон",
                         command=self.toggle_pin)
        menu.add_command(label="Выбрать цвет…", command=self.choose_color)
        menu.add_command(label="По умолчанию (жёлтый)", command=self.reset_color)
        menu.add_separator()
        menu.add_command(label="Новая заметка", command=self.app.new_sticker)
        menu.add_command(label="Закрыть заметку", command=self.close)
        try:
            menu.tk_popup(self.menu_button.winfo_rootx(),
                          self.menu_button.winfo_rooty() + self.menu_button.winfo_height())
        finally:
            menu.grab_release()

    def choose_color(self):
        selected = colorchooser.askcolor(color=self.color, title="Цвет заметки", parent=self.win)[1]
        if selected:
            self.apply_color(selected)
            self.app.schedule_save()

    def reset_color(self):
        self.apply_color(DEFAULT_COLOR)
        self.app.schedule_save()

    def toggle_pin(self):
        self.pinned = not self.pinned
        self.win.attributes("-topmost", self.pinned)
        self.app.schedule_save()

    def get_data(self):
        return {"text": self.text.get("1.0", "end-1c"), "color": self.color,
            "pinned": self.pinned, "x": self.win.winfo_x(), "y": self.win.winfo_y(),
            "width": self.win.winfo_width(), "height": self.win.winfo_height()}

    def close(self):
        self.app.save()
        if self in self.app.stickers:
            self.app.stickers.remove(self)
        try:
            self.win.destroy()
        except tk.TclError:
            pass
        if not self.app.stickers:
            self.app.shutdown()
        else:
            self.app.schedule_save()

class StickerApp:
    def __init__(self):
        self.stickers = []
        self.save_job = None
        self.shutting_down = False
        self.root = tk.Tk()
        self.root.withdraw()
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                saved = json.load(file)
            if isinstance(saved, list):
                for item in saved:
                    if isinstance(item, dict):
                        Sticker(self, item)
        except (OSError, ValueError, TypeError):
            pass
        if not self.stickers:
            self.new_sticker()
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
        self.root.mainloop()

    def new_sticker(self):
        if self.shutting_down:
            return
        sticker = Sticker(self)
        sticker.text.focus_set()
        self.schedule_save()

    def schedule_save(self):
        if self.shutting_down:
            return
        if self.save_job is not None:
            try:
                self.root.after_cancel(self.save_job)
            except tk.TclError:
                pass
        self.save_job = self.root.after(400, self.save)

    def save(self):
        if self.shutting_down:
            return
        self.save_job = None
        try:
            data = []
            for sticker in list(self.stickers):
                try:
                    if sticker.win.winfo_exists():
                        data.append(sticker.get_data())
                except tk.TclError:
                    pass
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except (OSError, tk.TclError):
            pass

    def shutdown(self):
        if self.shutting_down:
            return
        self.shutting_down = True
        if self.save_job is not None:
            try:
                self.root.after_cancel(self.save_job)
            except tk.TclError:
                pass
            self.save_job = None
        try:
            data = []
            for sticker in list(self.stickers):
                try:
                    if sticker.win.winfo_exists():
                        data.append(sticker.get_data())
                except tk.TclError:
                    pass
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except (OSError, tk.TclError):
            pass
        try:
            for sticker in list(self.stickers):
                try:
                    sticker.win.destroy()
                except tk.TclError:
                    pass
            self.root.destroy()
        except tk.TclError:
            pass

if __name__ == "__main__":
    StickerApp()
