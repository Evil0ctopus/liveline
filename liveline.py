import tkinter as tk
import requests
from bs4 import BeautifulSoup
import json
import itertools
import webbrowser
from PIL import Image, ImageTk
import io

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
            link_tag = item.find("link")

            if title_tag:
                text = title_tag.get_text(strip=True)
                if text:
                    link = link_tag.get_text(strip=True) if link_tag else None
                    headlines.append((text, link))
                    continue

            summary_tag = item.find("summary")
            if summary_tag:
                text = summary_tag.get_text(strip=True)
                if text:
                    headlines.append((text, None))
                    continue

        return headlines if headlines else [("No headlines found", None)]
    except Exception as e:
        return [(f"Error fetching {url}: {e}", None)]

class TickerApp:
    def __init__(self, root, feeds, direction="left"):
        self.root = root
        self.canvas = tk.Canvas(root, height=50, width=480, bg="black", highlightthickness=0)
        self.canvas.pack()
        self.direction = direction
        self.feed_cycle = itertools.cycle(feeds)

        self.text_item = self.canvas.create_text(
            480 if direction == "left" else 0, 25,
            text="Loading feeds...",
            fill="white",
            font=("Arial", 16),
            anchor="w" if direction == "left" else "e"
        )

        # Close Button (smaller click area, far right)
        self.close_button = tk.Button(
            root,
            text="X",
            command=self.root.destroy,
            bg="black",
            fg="white",
            bd=0,
            font=("Arial", 10),
            padx=1,
            pady=0
        )
        self.close_button.place(x=465, y=5)

        # Store headlines + URLs
        self.headlines = []

        self.update_feed()
        self.scroll()

        # Enable dragging the widget (safe detection)
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)

        # Double-click anywhere on ticker to open popup
        self.canvas.bind("<Double-Button-1>", self.show_popup)

    def update_feed(self):
        url = next(self.feed_cycle)
        self.headlines = fetch_feed(url)

        print(f"\n[Liveline] Loaded feed: {url}")
        print(f"[Liveline] Headlines: {[h[0] for h in self.headlines]}\n")

        display_text = " | ".join([h[0] for h in self.headlines])
        self.canvas.itemconfig(self.text_item, text=display_text)
        self.root.after(60000, self.update_feed)

    def scroll(self):
        dx = -4 if self.direction == "left" else 4
        self.canvas.move(self.text_item, dx, 0)

        x = self.canvas.coords(self.text_item)[0]
        if self.direction == "left" and x < -2000:
            self.canvas.coords(self.text_item, 480, 25)
        elif self.direction == "right" and x > 2000:
            self.canvas.coords(self.text_item, 0, 25)
        self.root.after(50, self.scroll)

    def show_popup(self, event=None):
        popup = tk.Toplevel(self.root)
        popup.title("Liveline Headlines")
        popup.geometry("400x300+100+100")
        popup.attributes("-topmost", True)

        tk.Label(popup, text="Latest Headlines", font=("Arial", 14, "bold")).pack(pady=5)

        for headline, link in self.headlines:
            frame = tk.Frame(popup)
            frame.pack(anchor="w", pady=2)

            thumb_img = None
            if link:
                try:
                    resp = requests.get(link, timeout=5)
                    soup = BeautifulSoup(resp.content, "html.parser")
                    og_image = soup.find("meta", property="og:image")
                    if og_image and og_image.get("content"):
                        img_url = og_image["content"]
                        img_resp = requests.get(img_url, timeout=5)
                        if "image" in img_resp.headers.get("Content-Type", ""):
                            img_data = img_resp.content
                            try:
                                pil_img = Image.open(io.BytesIO(img_data))
                                pil_img.thumbnail((40, 40))
                                thumb_img = ImageTk.PhotoImage(pil_img)
                            except Exception as e:
                                print(f"PIL error: {e}")
                except Exception as e:
                    print(f"Thumbnail error: {e}")

            if thumb_img:
                img_label = tk.Label(frame, image=thumb_img)
                img_label.image = thumb_img  # keep reference
                img_label.pack(side="left")

            link_label = tk.Label(frame, text=headline, fg="blue", cursor="hand2",
                                  wraplength=320, justify="left")
            link_label.pack(side="left")
            if link:
                link_label.bind("<Button-1>", lambda e, url=link: webbrowser.open(url))

    # --- Dragging support with safe detection ---
    def start_move(self, event):
        self._x = event.x
        self._y = event.y
        self._dragging = False

    def do_move(self, event):
        dx = abs(event.x - self._x)
        dy = abs(event.y - self._y)
        if dx > 2 or dy > 2:   # only drag if moved more than 2px
            self._dragging = True
            x = self.root.winfo_x() + event.x - self._x
            y = self.root.winfo_y() + event.y - self._y
            self.root.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Liveline Ticker")

    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.config(bg="black")
    root.wm_attributes("-transparentcolor", "black")

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = 480
    window_height = 50
    x = 144   # ~1.5 inches to the right
    y = screen_height - window_height
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    feeds = load_feeds()
    app = TickerApp(root, feeds, direction="left")
    root.mainloop()


