import tkinter as tk
import requests
from bs4 import BeautifulSoup
import json
import itertools

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
            # Atom/RSS: look for <title>
            title_tag = item.find("title")
            if title_tag:
                text = title_tag.get_text(strip=True)
                if text:
                    headlines.append(text)
                    continue
            # Atom fallback: <summary>
            summary_tag = item.find("summary")
            if summary_tag:
                text = summary_tag.get_text(strip=True)
                if text:
                    headlines.append(text)
                    continue

        return " | ".join(headlines) if headlines else "No headlines found"
    except Exception as e:
        return f"Error fetching {url}: {e}"

class TickerApp:
    def __init__(self, root, feeds, direction="left"):
        self.root = root
        self.canvas = tk.Canvas(root, height=50, width=800, bg="black", highlightthickness=0)
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
        self.cycle_color()   # start slower color cycling

        # Enable dragging the widget
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)

    def update_feed(self):
        url = next(self.feed_cycle)
        headlines = fetch_feed(url)

        print(f"\n[Liveline] Loaded feed: {url}")
        print(f"[Liveline] Headlines: {headlines}\n")

        self.canvas.itemconfig(self.text_item, text=headlines)
        self.root.after(60000, self.update_feed)

    def scroll(self):
        dx = -4 if self.direction=="left" else 4
        self.canvas.move(self.text_item, dx, 0)

        x = self.canvas.coords(self.text_item)[0]
        if self.direction=="left" and x < -2000:
            self.canvas.coords(self.text_item, 800, 25)
        elif self.direction=="right" and x > 2000:
            self.canvas.coords(self.text_item, 0, 25)
        self.root.after(50, self.scroll)

    def cycle_color(self):
        # Change color every 1000 ms (1 second)
        self.canvas.itemconfig(self.text_item, fill=self.colors[self.color_index])
        self.color_index = (self.color_index + 1) % len(self.colors)
        self.root.after(1000, self.cycle_color)

    # --- Dragging support ---
    def start_move(self, event):
        self._x = event.x
        self._y = event.y

    def do_move(self, event):
        x = self.root.winfo_x() + event.x - self._x
        y = self.root.winfo_y() + event.y - self._y
        self.root.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Liveline Ticker")

    # 👇 Make it a widget overlay
    root.overrideredirect(True)        # no window borders
    root.attributes("-topmost", True)  # always on top
    root.config(bg="black")            # background color
    root.wm_attributes("-transparentcolor", "black")  # transparent background

    feeds = load_feeds()
    app = TickerApp(root, feeds, direction="left")
    root.mainloop()


