import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import requests
import json
import os
from datetime import datetime
from html import unescape
import urllib.parse
import re

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------
DATA_FILE = "vocabulary.json"
FONT_FAMILY = "New Times Roman"
FONT_SIZE = 11
RETRO_BG = "#c0c0c0"
RETRO_FG = "#000000"
RETRO_SELECT = "#000000"
RETRO_HIGHLIGHT = "#ffffff"
RETRO_BUTTON = "#e0e0e0"
RETRO_ACTIVE = "#d0d0d0"

# ---------------------------------------------------------------------
# DICTIONARY LOOKUP (Multiple sources for reliability)
# ---------------------------------------------------------------------
def fetch_definition(word):
    """
    Fetch the first basic meaning of a word or phrase using multiple APIs.
    Tries primary API first, then falls back to secondary sources.
    Returns a string with the definition or an error message.
    """
    # Clean input
    word = word.strip().lower()
    if not word:
        return "Please enter a word or phrase."

    # Try multiple API endpoints
    definitions = []

    # API 1: DictionaryAPI.dev (primary)
    url1 = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}"
    try:
        response = requests.get(url1, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list):
                entry = data[0]
                meanings = entry.get("meanings", [])
                if meanings:
                    first_meaning = meanings[0]
                    part_of_speech = first_meaning.get("partOfSpeech", "unknown")
                    definitions = first_meaning.get("definitions", [])
                    if definitions:
                        definition_text = definitions[0].get("definition", "No definition found.")
                        definition_text = unescape(definition_text)
                        return f"({part_of_speech}) {definition_text}"
    except:
        pass  # Fall through to next API

    # API 2: Wiktionary API (alternative)
    url2 = f"https://en.wiktionary.org/api/rest_v1/page/definition/{urllib.parse.quote(word)}"
    try:
        response = requests.get(url2, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and "en" in data:
                en_data = data["en"]
                if en_data and len(en_data) > 0:
                    # Get the first definition from the first part of speech
                    for pos, definitions in en_data.items():
                        if definitions and len(definitions) > 0:
                            first_def = definitions[0]
                            if "definition" in first_def:
                                return f"({pos}) {first_def['definition']}"
    except:
        pass  # Fall through to next method

    url3 = f"https://api.urbandictionary.com/v0/define?term={urllib.parse.quote(word)}"
    try:
        response = requests.get(url3, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and "list" in data and len(data["list"]) > 0:
                first_entry = data["list"][0]
                definition = first_entry.get("definition", "")
                # Clean up the definition (remove brackets and extra formatting)
                definition = re.sub(r'\[.*?\]', '', definition)
                definition = definition.strip()
                if definition:
                    return f"(slang) {definition}"
    except:
        pass  # Fall through to error

    # If all APIs fail, return a helpful error message
    return "Definition not found. Please check your internet connection or try a different word."

# ---------------------------------------------------------------------
# VOCABULARY MANAGER
# ---------------------------------------------------------------------
class VocabularyManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Vocab.")
        self.root.geometry("720x550")
        self.root.configure(bg=RETRO_BG)
       
        # Load existing data
        self.vocab = self.load_data()

        # Build UI
        self.create_widgets()
        self.update_listbox()

        # Bind close event to save data
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # -----------------------------------------------------------------
    # DATA PERSISTENCE
    # -----------------------------------------------------------------
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.vocab, f, indent=2, ensure_ascii=False)
        except IOError:
            messagebox.showerror("Error", "Could not save vocabulary data.")

    # -----------------------------------------------------------------
    # UI CREATION
    # -----------------------------------------------------------------
    def create_widgets(self):
        # Main frame (retro 3D border effect)
        main_frame = tk.Frame(self.root, bg=RETRO_BG, relief="raised", bd=3)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # --- Title ---
        title = tk.Label(
            main_frame,
            text="═══ VOCABULARY BUILDER ═══",
            font=(FONT_FAMILY, FONT_SIZE + 4, "bold"),
            bg=RETRO_BG,
            fg=RETRO_FG,
            relief="flat"
        )
        title.pack(pady=(5, 10))

        # --- Entry row ---
        entry_frame = tk.Frame(main_frame, bg=RETRO_BG)
        entry_frame.pack(pady=5, padx=10, fill="x")

        tk.Label(
            entry_frame,
            text="> ENTER WORD:",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=RETRO_BG,
            fg=RETRO_FG
        ).pack(side="left", padx=(0, 8))

        self.word_var = tk.StringVar()
        self.entry = tk.Entry(
            entry_frame,
            textvariable=self.word_var,
            font=(FONT_FAMILY, FONT_SIZE),
            bg=RETRO_HIGHLIGHT,
            fg=RETRO_FG,
            relief="sunken",
            bd=2,
            insertbackground=RETRO_FG
        )
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self.lookup_and_add())

        # --- Buttons ---
        btn_frame = tk.Frame(main_frame, bg=RETRO_BG)
        btn_frame.pack(pady=10)

        self.lookup_btn = tk.Button(
            btn_frame,
            text="[ LOOKUP & ADD ]",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=RETRO_BUTTON,
            fg="blue",
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=3,
            command=self.lookup_and_add
        )
        self.lookup_btn.pack(side="left", padx=5)

        self.delete_btn = tk.Button(
            btn_frame,
            text="[ DELETE SELECTED ]",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=RETRO_BUTTON,
            fg="magenta",
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=3,
            command=self.delete_selected
        )
        self.delete_btn.pack(side="left", padx=5)

        self.clear_btn = tk.Button(
            btn_frame,
            text="[ CLEAR ALL ]",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=RETRO_BUTTON,
            fg="red",
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=3,
            command=self.clear_all
        )
        self.clear_btn.pack(side="left", padx=5)

        # --- Listbox with scrollbar ---
        list_frame = tk.Frame(main_frame, bg=RETRO_BG)
        list_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            font=(FONT_FAMILY, FONT_SIZE),
            bg=RETRO_HIGHLIGHT,
            fg=RETRO_FG,
            selectbackground=RETRO_SELECT,
            selectforeground=RETRO_HIGHLIGHT,
            relief="sunken",
            bd=2,
            height=15
        )
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Bind double-click to show definition in a popup
        self.listbox.bind("<Double-Button-1>", self.show_definition_popup)

        # --- Status bar ---
        self.status = tk.Label(
            main_frame,
            text="Ready. Enter a word and press LOOKUP.",
            font=(FONT_FAMILY, FONT_SIZE - 1),
            bg=RETRO_BG,
            fg=RETRO_FG,
            relief="sunken",
            bd=1,
            anchor="w"
        )
        self.status.pack(pady=(10, 5), padx=10, fill="x")

        # Set focus to entry
        self.entry.focus_set()

    # -----------------------------------------------------------------
    # CORE FUNCTIONALITY
    # -----------------------------------------------------------------
    def lookup_and_add(self):
        word = self.word_var.get().strip()
        if not word:
            self.status.config(text="Please enter a word or phrase.")
            return

        # Check if already in vocabulary
        if word in self.vocab:
            self.status.config(text=f"'{word}' already exists in vocabulary.")
            messagebox.showinfo("Already Exists", f"'{word}' is already in your vocabulary.")
            self.word_var.set("")
            self.entry.focus_set()
            return

        # Fetch definition
        self.status.config(text=f"Looking up '{word}'...")
        self.root.update_idletasks()

        definition = fetch_definition(word)

        # Store
        self.vocab[word] = definition
        self.save_data()
        self.update_listbox()

        # Clear entry, update status, select the new item
        self.word_var.set("")
        self.status.config(text=f"Added: '{word}' -> {definition}")
        self.entry.focus_set()

        # Select the newly added item in the listbox
        items = self.listbox.get(0, tk.END)
        for i, item in enumerate(items):
            if item.startswith(word + " -"):
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(i)
                self.listbox.see(i)
                break

    def delete_selected(self):
        selected = self.listbox.curselection()
        if not selected:
            self.status.config(text="No item selected.")
            return

        index = selected[0]
        item_text = self.listbox.get(index)
        # Extract the word part (before " - ")
        word = item_text.split(" - ")[0].strip()

        if word in self.vocab:
            del self.vocab[word]
            self.save_data()
            self.update_listbox()
            self.status.config(text=f"Deleted: '{word}'")
        else:
            self.status.config(text="Error: word not found in data.")

    def clear_all(self):
        if not self.vocab:
            self.status.config(text="Vocabulary is already empty.")
            return

        if messagebox.askyesno("Clear All", "Are you sure you want to delete ALL vocabulary entries?"):
            self.vocab.clear()
            self.save_data()
            self.update_listbox()
            self.status.config(text="All entries cleared.")

    def show_definition_popup(self, event):
        selected = self.listbox.curselection()
        if not selected:
            return
        index = selected[0]
        item_text = self.listbox.get(index)
        word = item_text.split(" - ")[0].strip()

        definition = self.vocab.get(word, "Definition not available.")

        # Show in a popup window
        popup = tk.Toplevel(self.root)
        popup.title(f"Definition: {word}")
        popup.configure(bg=RETRO_BG)
        popup.geometry("500x200")
        popup.resizable(False, False)

        # Make it modal-ish
        popup.transient(self.root)
        popup.grab_set()

        label = tk.Label(
            popup,
            text=f"WORD: {word}",
            font=(FONT_FAMILY, FONT_SIZE + 2, "bold"),
            bg=RETRO_BG,
            fg=RETRO_FG
        )
        label.pack(pady=(15, 5))

        text_widget = scrolledtext.ScrolledText(
            popup,
            font=(FONT_FAMILY, FONT_SIZE),
            bg=RETRO_HIGHLIGHT,
            fg=RETRO_FG,
            relief="sunken",
            bd=2,
            wrap=tk.WORD,
            height=6
        )
        text_widget.pack(padx=15, pady=5, fill="both", expand=True)
        text_widget.insert(tk.END, definition)
        text_widget.config(state="disabled")

        close_btn = tk.Button(
            popup,
            text="[ CLOSE ]",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=RETRO_BUTTON,
            fg=RETRO_FG,
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=3,
            command=popup.destroy
        )
        close_btn.pack(pady=10)

        # Center popup relative to main window
        popup.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (popup.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")

    # -----------------------------------------------------------------
    # UI UPDATE HELPERS
    # -----------------------------------------------------------------
    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for word, definition in sorted(self.vocab.items()):
            # Truncate definition for display (keep it clean)
            display_def = definition[:60] + "..." if len(definition) > 60 else definition
            self.listbox.insert(tk.END, f"{word} - {display_def}")

    def on_close(self):
        self.save_data()
        self.root.destroy()

# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = VocabularyManager(root)
    root.mainloop()