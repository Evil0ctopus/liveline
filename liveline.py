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
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "xml")
        items = soup.find_all("title")
        headlines = [item.get_text() for item in items[1:6]]  # skip feed title
        return " | ".join(headlines)
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
            800 if direction=="left" else 0,
            25,
            text="Loading feeds...",
            fill="white",
            font=("Arial", 16),
            anchor="w" if direction=="left" else "e"
        )
        self.update_feed()
        self.scroll()

    def update_feed(self):
        url = next(self.feed_cycle)
        headlines = fetch_feed(url)

        # 👇 Debug print to terminal
        print(f"\n[Liveline] Loaded feed: {url}")
        print(f"[Liveline] Headlines: {headlines}\n")

        self.canvas.itemconfig(self.text_item, text=headlines)
        # refresh every 60 seconds
        self.root.after(60000, self.update_feed)


    def scroll(self):
        dx = -2 if self.direction=="left" else 2
        self.canvas.move(self.text_item, dx, 0)
        x = self.canvas.coords(self.text_item)[0]
        if self.direction=="left" and x < -2000:
            self.canvas.coords(self.text_item, 800, 25)
        elif self.direction=="right" and x > 2000:
            self.canvas.coords(self.text_item, 0, 25)
        self.root.after(50, self.scroll)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Liveline Ticker")
    feeds = load_feeds()
    app = TickerApp(root, feeds, direction="left")
    root.mainloop()
