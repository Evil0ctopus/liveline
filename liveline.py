import tkinter as tk
import requests
from bs4 import BeautifulSoup
import json
import itertools
import threading
from pystray import Icon, MenuItem
from PIL import Image, ImageDraw

def load_feeds():
    with open("feeds.json", "r") as f:
        data = json.load(f)
        return data["feeds"]

def fetch_feed(url):
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.content, "xml")

        # Try RSS <item> first
        items = soup.find_all("item")
        # Fallback for Atom feeds
        if not items:
            items = soup.find_all("entry")

        headlines = []
        for item in items[:5]:
            title_tag = item.find("title")
            if title_tag:
                headlines.append(title_tag.text.strip())

        return " | ".join(headlines) if headlines else "No headlines found"
    except Exception as e:
        return f"Error fetching {url}: {e}"

class TickerApp:
    def __init__(self, root, feeds, direction="left"):
        self.root = root
        self.canvas = tk.Canvas(root, height=50, width=800, bg="black")
        self.canvas.pack()
        self.direction = direction
        self.feed_cycle = itertools.cycle(feeds)

        self.text_item = self.canvas.create_text(
            800 if direction=="left" else 0, 25,
            text="Loading feeds...",
            fill="white",
            font=("Arial", 16),
            anchor="w" if direction=="left" else "e"
        )

        # 🌈 Rainbow colors
        self.colors = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
        self.color_index = 0

        self.update_feed()
        self.scroll()

    def update_feed(self):
        url = next(self.feed_cycle)
        headlines = fetch_feed(url)

        print(f"\n[Liveline] Loaded feed: {url}")
        print(f"[Liveline] Headlines: {headlines}\n")

        self.canvas.itemconfig(self.text_item, text=headlines)

        # Cycle rainbow colors each feed update
        self.canvas.itemconfig(self.text_item, fill=self.colors[self.color_index])
        self.color_index = (self.color_index + 1) % len(self.colors)

        self.root.after(60000, self.update_feed)

    def scroll(self):
        dx = -4 if self.direction=="left" else 4
        self.canvas.move(self.text_item, dx, 0)

        # Optional: cycle colors continuously while scrolling
        self.canvas.itemconfig(self.text_item, fill=self.colors[self.color_index])
        self.color_index = (self.color_index + 1) % len(self.colors)

        x = self.canvas.coords(self.text_item)[0]
        if self.direction=="left" and x < -2000:
            self.canvas.coords(self.text_item, 800, 25)
        elif self.direction=="right" and x > 2000:
            self.canvas.coords(self.text_item, 0, 25)
        self.root.after(50, self.scroll)

# --- System Tray Support ---
def create_image():
    # Simple tray icon (red square)
    image = Image.new("RGB", (64, 64), "black")
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 48, 48), fill="red")
    return image

def on_quit(icon, item):
    icon.stop()
    root.quit()

def run_tray():
    icon = Icon("Liveline", create_image(), menu=(
        MenuItem("Show Ticker", lambda icon, item: (root.deiconify(), root.lift(), root.focus_force())),
        MenuItem("Hide Ticker", lambda icon, item: root.withdraw()),
        MenuItem("Quit", on_quit)
    ))
    icon.run()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Liveline Ticker")

    # 👇 Start minimized so it shows in the taskbar
    root.iconify()

    # Start tray in background thread
    threading.Thread(target=run_tray, daemon=True).start()

    feeds = load_feeds()
    app = TickerApp(root, feeds, direction="left")
    root.mainloop()


