import tkinter as tk
from frontend.theme import Colors, Fonts
from frontend.widgets import RoundedCard
from frontend.pages.base import BasePage
from utils.common import speak_if_allowed


class CommunicatorPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.configure(bg=Colors.page_bg)

        # --- navigation state ---
        self.history_stack = []
        self.current_category = "home"
        self.vocab_sets = self._init_vocab_sets()

        # === main layout ===
        card = tk.Frame(self, bg=Colors.page_bg)
        card.pack(expand=True, fill="both")
        

        title = tk.Label(
            card, text="🗣️ Communication Aid System",
            font=("Segoe UI", 22, "bold"),
            bg=Colors.page_bg, fg=Colors.card_text
        )
        title.pack(pady=(5, 10))

        # message bar
        self.message_var = tk.StringVar(value="")
        msg_bar = tk.Entry(
            card, textvariable=self.message_var, font=("Segoe UI", 14),
            bg="white", fg="black", relief="flat", justify="center"
        )
        msg_bar.pack(pady=(0, 15), ipady=8, fill="x", padx=30)

        # grid container
        self.grid_frame = tk.Frame(card, bg=Colors.page_bg)
        self.grid_frame.pack(expand=True, fill="both", padx=20, pady=10)

        # bottom control bar
        control_frame = tk.Frame(card, bg=Colors.page_bg)
        control_frame.pack(pady=(10, 5))

        # ✅ Bottom Control Buttons
        tk.Button(
            control_frame,
            text="🔊 Speak",
            font=("Segoe UI", 14, "bold"),
            bg=Colors.pill_bg,
            fg="white",
            relief="flat",
            padx=25,
            pady=8,
            cursor="hand2",
            command=self.speak_message
        ).pack(side="left", padx=20)

        tk.Button(
            control_frame,
            text="🧹 Clear Word",
            font=("Segoe UI", 14, "bold"),
            bg="#FFA726",   # orange tone
            fg="white",
            relief="flat",
            padx=25,
            pady=8,
            cursor="hand2",
            command=lambda: self.clear_message(full=False)
        ).pack(side="left", padx=20)

        tk.Button(
            control_frame,
            text="🗑️ Clear All",
            font=("Segoe UI", 14, "bold"),
            bg="#E57373",   # red tone
            fg="white",
            relief="flat",
            padx=25,
            pady=8,
            cursor="hand2",
            command=lambda: self.clear_message(full=True)
        ).pack(side="left", padx=20)


        self._build_grid(self.vocab_sets["home"])

    # ===== grid builder =====
    def _build_grid(self, vocab):
        """Builds the grid dynamically with hybrid layout."""
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        rows, cols = 6, 5
        for i in range(rows):
            self.grid_frame.grid_rowconfigure(i, weight=1)
        for j in range(cols):
            self.grid_frame.grid_columnconfigure(j, weight=1)

        # Show core + category words together
        # Always show the core words + current category
        if self.current_category == "home":
            combined_vocab = self.vocab_sets["core"] + self.vocab_sets["home"]
        else:
            combined_vocab = self.vocab_sets["core"] + vocab


        for idx, word in enumerate(combined_vocab):
            r, c = divmod(idx, cols)
            btn = tk.Button(
        self.grid_frame,
        text=f"{word['emoji']} {word['text']}",   # ✅ one-line display
        font=("Segoe UI", 12, "bold"),
        bg=word["color"],
        fg="black",
        anchor="center",
        justify="center",
        relief="flat",
        cursor="hand2",
        bd=0,
        height=2,              # ✅ consistent height
        wraplength=0,          # ✅ disable wrapping
        command=lambda w=word: self.handle_button(w)  # ✅ <-- this line added back
    )
            btn.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")


    # ===== event handlers =====
    def handle_button(self, word):
        if "folder" in word:
            self.history_stack.append(self.current_category)
            self.load_category(word["folder"])
        elif word["text"].lower() == "back":
            self.go_back()
        else:
            self.add_word(word["text"])

    def load_category(self, category_name):
        if category_name in self.vocab_sets:
            self.current_category = category_name
            self._build_grid(self.vocab_sets[category_name])

    def go_back(self):
        if self.history_stack:
            prev = self.history_stack.pop()
            self.current_category = prev
            self._build_grid(self.vocab_sets[prev])

    def add_word(self, word):
        cur = self.message_var.get().strip()
        self.message_var.set(f"{cur} {word}".strip())

    def speak_message(self):
        text = self.message_var.get().strip()
        if text:
            speak_if_allowed(text)
            
    def handle_clear_click(self):
        """Detect single vs double click on Clear button."""
        # Cancel previous single click if a double click is detected
        if hasattr(self, "_clear_click_after") and self._clear_click_after is not None:
            # Double click detected
            self.after_cancel(self._clear_click_after)
            self._clear_click_after = None
            self.clear_message(full=True)
        else:
            # Schedule single click action
            self._clear_click_after = self.after(400, self.clear_message, False)

    def clear_message(self, full=False):
        """Clear one word or full sentence."""
        if full:
            self.message_var.set("")
        else:
            text = self.message_var.get().strip().split()
            if text:
                text.pop()  # remove last word
                self.message_var.set(" ".join(text))
        # Reset state
        self._clear_click_after = None


    # ===== vocabulary =====
    def _init_vocab_sets(self):
        return {
            # ===== Core words (always visible on top) =====
            "core": [
                {"text": "I", "emoji": "🧍", "color": "#F8BBD0"},
                {"text": "is", "emoji": "🔹", "color": "#E1BEE7"},
                {"text": "can", "emoji": "💪", "color": "#E1BEE7"},
                {"text": "will", "emoji": "🕓", "color": "#E1BEE7"},
                {"text": "do", "emoji": "✅", "color": "#E1BEE7"},
                {"text": "you", "emoji": "👉", "color": "#F8BBD0"},
                {"text": "we", "emoji": "👫", "color": "#F8BBD0"},
                {"text": "want", "emoji": "🤲", "color": "#FFF59D"},
                {"text": "like", "emoji": "❤️", "color": "#FFF59D"},
                {"text": "need", "emoji": "🤔", "color": "#FFF59D"},
                {"text": "he", "emoji": "👦", "color": "#F8BBD0"},
                {"text": "she", "emoji": "👩", "color": "#F8BBD0"},
                {"text": "stop", "emoji": "🛑", "color": "#FFF59D"},
                {"text": "go", "emoji": "➡️", "color": "#FFF59D"},
                {"text": "come", "emoji": "👣", "color": "#FFF59D"},
                {"text": "it", "emoji": "🐾", "color": "#F8BBD0"},
                {"text": "this", "emoji": "👉📦", "color": "#E1BEE7"},
                {"text": "see", "emoji": "👀", "color": "#FFF59D"},
                {"text": "look", "emoji": "🔍", "color": "#FFF59D"},
                {"text": "put", "emoji": "📦⬇️", "color": "#FFF59D"},
            ],

            # ===== Home-level folders (bottom row on main grid) =====
            "home": [
                {"text": "people", "emoji": "👨‍👩‍👧", "color": "#C8E6C9", "folder": "people"},
                {"text": "things", "emoji": "📦", "color": "#C8E6C9", "folder": "things"},
                {"text": "food", "emoji": "🍎", "color": "#C8E6C9", "folder": "food"},
                {"text": "places", "emoji": "🏠", "color": "#C8E6C9", "folder": "places"},
                {"text": "actions", "emoji": "🏃‍♀️", "color": "#C8E6C9", "folder": "actions"},
                {"text": "feelings", "emoji": "😊", "color": "#BBDEFB", "folder": "feelings"},
                {"text": "fun", "emoji": "🎉", "color": "#FFE082"},
                {"text": "time", "emoji": "⏰", "color": "#D1C4E9"},
                {"text": "chat", "emoji": "💬", "color": "#FFE0B2"},
                {"text": "help", "emoji": "🆘", "color": "#E57373"},
            ],

            # ===== PLACES page (bottom contextual grid area) =====
            "places": [
                {"text": "inside", "emoji": "🏠➡️", "color": "#E1BEE7"},
                {"text": "outside", "emoji": "🏞️", "color": "#C8E6C9"},
                {"text": "here", "emoji": "📍", "color": "#E1BEE7"},
                {"text": "out", "emoji": "↗️", "color": "#E1BEE7"},
                {"text": "good", "emoji": "👍", "color": "#BBDEFB"},
                {"text": "place", "emoji": "🗺️", "color": "#C8E6C9"},
                {"text": "home", "emoji": "🏠", "color": "#FFF9C4"},
                {"text": "school", "emoji": "🏫", "color": "#E1BEE7"},
                {"text": "bathroom", "emoji": "🚻", "color": "#C5CAE9"},
                {"text": "there", "emoji": "📍➡️", "color": "#FFF59D"},
                {"text": "bus", "emoji": "🚌", "color": "#FFECB3"},
                {"text": "cafeteria", "emoji": "🍽️", "color": "#FFE0B2"},
                {"text": "car", "emoji": "🚗", "color": "#FFECB3"},
                {"text": "classroom", "emoji": "🏫📖", "color": "#E1BEE7"},
                {"text": "living room", "emoji": "🛋️", "color": "#C8E6C9"},
                {"text": "shopping centre", "emoji": "🏬", "color": "#D1C4E9"},
                {"text": "park", "emoji": "🌳", "color": "#C8E6C9"},
                {"text": "party", "emoji": "🎉", "color": "#FFE082"},
                {"text": "playground", "emoji": "🏖️", "color": "#C8E6C9"},
                {"text": "restaurant", "emoji": "🍽️", "color": "#FFE0B2"},
                {"text": "shop", "emoji": "🛍️", "color": "#FFF9C4"},
                {"text": "therapy", "emoji": "🧘‍♂️", "color": "#E1BEE7"},
                {"text": "swim", "emoji": "🏊‍♂️", "color": "#B3E5FC"},
                {"text": "postbox", "emoji": "📮", "color": "#FFCDD2"},
                {"text": "ikea", "emoji": "🏢", "color": "#FFF176"},
                {"text": "back", "emoji": "⬅️", "color": "#E0E0E0"},
            ],
        "people": [
    {"text": "mother", "emoji": "👩‍🦰", "color": "#F8BBD0"},
    {"text": "father", "emoji": "👨‍🦱", "color": "#F8BBD0"},
    {"text": "brother", "emoji": "👦", "color": "#F8BBD0"},
    {"text": "sister", "emoji": "👧", "color": "#F8BBD0"},
    {"text": "friend", "emoji": "🤝", "color": "#C8E6C9"},
    {"text": "teacher", "emoji": "👩‍🏫", "color": "#E1BEE7"},
    {"text": "doctor", "emoji": "👨‍⚕️", "color": "#BBDEFB"},
    {"text": "student", "emoji": "🧑‍🎓", "color": "#E1BEE7"},
    {"text": "baby", "emoji": "👶", "color": "#FFF59D"},
    {"text": "back", "emoji": "⬅️", "color": "#E0E0E0"},
],

"things": [
    {"text": "book", "emoji": "📖", "color": "#DCEDC8"},
    {"text": "pen", "emoji": "🖊️", "color": "#FFF9C4"},
    {"text": "phone", "emoji": "📱", "color": "#FFECB3"},
    {"text": "bag", "emoji": "🎒", "color": "#E1BEE7"},
    {"text": "chair", "emoji": "🪑", "color": "#C8E6C9"},
    {"text": "table", "emoji": "🛋️", "color": "#D1C4E9"},
    {"text": "computer", "emoji": "💻", "color": "#C5CAE9"},
    {"text": "toy", "emoji": "🧸", "color": "#FFE082"},
    {"text": "tv", "emoji": "📺", "color": "#BBDEFB"},
    {"text": "back", "emoji": "⬅️", "color": "#E0E0E0"},
],


            "food": [
                {"text": "apple", "emoji": "🍎", "color": "#FFCDD2"},
                {"text": "banana", "emoji": "🍌", "color": "#FFF9C4"},
                {"text": "rice", "emoji": "🍚", "color": "#FFF9C4"},
                {"text": "bread", "emoji": "🍞", "color": "#FFF9C4"},
                {"text": "juice", "emoji": "🧃", "color": "#FFECB3"},
                {"text": "water", "emoji": "💧", "color": "#B3E5FC"},
                {"text": "milk", "emoji": "🥛", "color": "#E1F5FE"},
                {"text": "coffee", "emoji": "☕", "color": "#D7CCC8"},
                {"text": "tea", "emoji": "🍵", "color": "#DCEDC8"},
                {"text": "back", "emoji": "⬅️", "color": "#E0E0E0"},
            ],
            
            "feelings": [
                {"text": "happy", "emoji": "😊", "color": "#FFF59D"},
                {"text": "sad", "emoji": "😢", "color": "#BBDEFB"},
                {"text": "angry", "emoji": "😡", "color": "#EF9A9A"},
                {"text": "tired", "emoji": "😴", "color": "#C5CAE9"},
                {"text": "back", "emoji": "⬅️", "color": "#E0E0E0"},
            ],
            "actions": [
                {"text": "run", "emoji": "🏃‍♂️", "color": "#C8E6C9"},
                {"text": "walk", "emoji": "🚶‍♀️", "color": "#C8E6C9"},
                {"text": "sit", "emoji": "🪑", "color": "#C8E6C9"},
                {"text": "play", "emoji": "🎮", "color": "#C8E6C9"},
                {"text": "read", "emoji": "📖", "color": "#C8E6C9"},
                {"text": "back", "emoji": "⬅️", "color": "#E0E0E0"},
            ],
            
        }
