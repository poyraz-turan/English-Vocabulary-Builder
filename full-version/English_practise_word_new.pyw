import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import requests
import json
import os
from datetime import datetime
from html import unescape
import urllib.parse
import re
from bs4 import BeautifulSoup
import random

#Added Favorites, fully functional.
#Added Flashcards that is fully functional and works at extra window.

DATA_FILE = "vocabulary.json"
FAVORITES_FILE = "favorites.json"
FONT_FAMILY = "New Times Roman"
FONT_SIZE = 11
RETRO_BG = "#c0c0c0"
RETRO_FG = "#000000"
RETRO_SELECT = "#000000"
RETRO_HIGHLIGHT = "#ffffff"
RETRO_BUTTON = "#e0e0e0"
RETRO_ACTIVE = "#d0d0d0"

def fetch_definition(word):
    word = word.strip().lower()
    if not word:
        return "Please enter a word or phrase."

    try:
        url = f"https://dictionary.cambridge.org/dictionary/english/{urllib.parse.quote(word)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            definitions = []
            
            definition_elements = soup.find_all('div', class_='def')
            if not definition_elements:
                definition_elements = soup.find_all('div', class_='ddef_d')
            if not definition_elements:
                definition_elements = soup.find_all('span', class_='def')
            if not definition_elements:
                definition_elements = soup.find_all('div', class_='def-body')
            
            for element in definition_elements[:3]:
                text = element.get_text().strip()
                text = ' '.join(text.split())
                if text and len(text) > 10:
                    definitions.append(text)
            
            if definitions:
                return f"(Cambridge) {definitions[0]}"
            else:
                pos_elements = soup.find_all('span', class_='pos')
                if pos_elements:
                    pos = pos_elements[0].get_text().strip()
                    def_elements = soup.find_all('span', class_='def')
                    if def_elements:
                        return f"({pos}) {def_elements[0].get_text().strip()}"
                
                return try_merriam_webster(word)
                
        elif response.status_code == 404:
            return try_merriam_webster(word)
        else:
            return f"Error accessing Cambridge Dictionary (Status: {response.status_code})."
            
    except requests.exceptions.Timeout:
        return "Request timed out. Trying alternative dictionary..."
    except requests.exceptions.ConnectionError:
        return "Network error. Trying alternative dictionary..."
    except Exception as e:
        return f"Error: {str(e)}. Trying alternative..."

def try_merriam_webster(word):
    try:
        url = f"https://www.merriam-webster.com/dictionary/{urllib.parse.quote(word)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            definitions = []
            
            def_elements = soup.find_all('span', class_='dt')
            if not def_elements:
                def_elements = soup.find_all('div', class_='definition')
            if not def_elements:
                def_elements = soup.find_all('p', class_='definition')
            
            for element in def_elements[:3]:
                text = element.get_text().strip()
                text = ' '.join(text.split())
                if text and len(text) > 10:
                    definitions.append(text)
            
            if definitions:
                return f"(Merriam-Webster) {definitions[0]}"
            else:
                pos_elements = soup.find_all('span', class_='fl')
                if pos_elements:
                    pos = pos_elements[0].get_text().strip()
                    for element in soup.find_all(['p', 'div', 'span']):
                        text = element.get_text().strip()
                        if text and len(text) > 20 and not text.startswith('http'):
                            return f"({pos}) {text[:200]}"
                
                return try_wordnik(word)
        
        return try_wordnik(word)
        
    except:
        return try_wordnik(word)

def try_wordnik(word):
    try:
        url = f"https://api.wordnik.com/v4/word.json/{urllib.parse.quote(word)}/definitions"
        params = {
            'limit': 1,
            'includeRelated': False,
            'useCanonical': False,
            'includeTags': False
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                definition = data[0].get('text', '')
                part_of_speech = data[0].get('partOfSpeech', 'unknown')
                if definition:
                    return f"({part_of_speech}) {definition}"
        
        return try_dictionary_api(word)
        
    except:
        return try_dictionary_api(word)

def try_dictionary_api(word):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                entry = data[0]
                meanings = entry.get("meanings", [])
                
                if meanings:
                    first_meaning = meanings[0]
                    part_of_speech = first_meaning.get("partOfSpeech", "unknown")
                    definitions = first_meaning.get("definitions", [])
                    
                    if definitions:
                        definition_text = definitions[0].get("definition", "")
                        example = definitions[0].get("example", "")
                        
                        definition_text = unescape(definition_text)
                        
                        if example:
                            return f"({part_of_speech}) {definition_text} [e.g., {example}]"
                        else:
                            return f"({part_of_speech}) {definition_text}"
        
        return "Definition not found. Please try a different word or check your spelling."
        
    except:
        return "Definition not available. Please check your internet connection."

class FlashcardWindow:
    def __init__(self, parent, vocab, favorites):
        self.parent = parent
        self.vocab = vocab
        self.favorites = favorites
        self.current_word = None
        self.showing_definition = False
        self.words_list = list(vocab.keys())
        self.current_index = 0
        
        self.window = tk.Toplevel(parent)
        self.window.title("★ FLASHCARD MODE ★")
        self.window.geometry("600x450")
        self.window.configure(bg=RETRO_BG)
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_first_card()
        
    def create_widgets(self):
        main_frame = tk.Frame(self.window, bg=RETRO_BG, relief="raised", bd=3)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        title = tk.Label(
            main_frame,
            text="FLASHCARDS",
            font=(FONT_FAMILY, FONT_SIZE + 4, "bold"),
            bg=RETRO_BG,
            fg=RETRO_FG
        )
        title.pack(pady=(10, 5))
        
        progress_frame = tk.Frame(main_frame, bg=RETRO_BG)
        progress_frame.pack(pady=5)
        
        self.progress_label = tk.Label(
            progress_frame,
            text="",
            font=(FONT_FAMILY, FONT_SIZE - 1),
            bg=RETRO_BG,
            fg=RETRO_FG
        )
        self.progress_label.pack()
        
        self.card_frame = tk.Frame(
            main_frame,
            bg=RETRO_HIGHLIGHT,
            relief="raised",
            bd=3,
            height=150
        )
        self.card_frame.pack(pady=15, padx=20, fill="both", expand=True)
        self.card_frame.pack_propagate(False)
        
        self.card_label = tk.Label(
            self.card_frame,
            text="",
            font=(FONT_FAMILY, FONT_SIZE + 4, "bold"),
            bg=RETRO_HIGHLIGHT,
            fg=RETRO_FG,
            wraplength=500,
            justify="center"
        )
        self.card_label.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.hint_label = tk.Label(
            main_frame,
            text="Click 'SHOW DEFINITION' to reveal the answer",
            font=(FONT_FAMILY, FONT_SIZE - 1, "italic"),
            bg=RETRO_BG,
            fg=RETRO_FG
        )
        self.hint_label.pack(pady=5)
        
        btn_frame = tk.Frame(main_frame, bg=RETRO_BG)
        btn_frame.pack(pady=15)
        
        self.show_btn = tk.Button(
            btn_frame,
            text="[ SHOW DEFINITION ]",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=RETRO_BUTTON,
            fg="blue",
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=3,
            command=self.show_definition
        )
        self.show_btn.pack(side="left", padx=5)
        
        self.next_btn = tk.Button(
            btn_frame,
            text="[ NEXT WORD → ]",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=RETRO_BUTTON,
            fg="green",
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=3,
            command=self.next_card
        )
        self.next_btn.pack(side="left", padx=5)
        
        self.prev_btn = tk.Button(
            btn_frame,
            text="[ ← PREVIOUS ]",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=RETRO_BUTTON,
            fg="green",
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=3,
            command=self.prev_card
        )
        self.prev_btn.pack(side="left", padx=5)
        
        self.shuffle_btn = tk.Button(
            btn_frame,
            text="[ 🔀 SHUFFLE ]",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=RETRO_BUTTON,
            fg="orange",
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=3,
            command=self.shuffle_cards
        )
        self.shuffle_btn.pack(side="left", padx=5)
        
        bottom_frame = tk.Frame(main_frame, bg=RETRO_BG)
        bottom_frame.pack(pady=10, fill="x")
        
        self.fav_btn = tk.Button(
            bottom_frame,
            text="★ ADD TO FAVORITES",
            font=(FONT_FAMILY, FONT_SIZE - 1, "bold"),
            bg=RETRO_BUTTON,
            fg="white",
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=3,
            command=self.toggle_favorite
        )
        self.fav_btn.pack(side="left", padx=10)
        
        close_btn = tk.Button(
            bottom_frame,
            text="[ CLOSE FLASHCARDS ]",
            font=(FONT_FAMILY, FONT_SIZE - 1, "bold"),
            bg=RETRO_BUTTON,
            fg="red",
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=3,
            command=self.window.destroy
        )
        close_btn.pack(side="right", padx=10)
        
        if not self.words_list:
            self.card_label.config(text="No words in vocabulary!\nAdd some words first.")
            self.show_btn.config(state="disabled")
            self.next_btn.config(state="disabled")
            self.prev_btn.config(state="disabled")
            self.progress_label.config(text="Vocabulary is empty")
    
    def load_first_card(self):
        if self.words_list:
            self.current_index = 0
            self.show_card()
    
    def show_card(self):
        if not self.words_list:
            return
        
        self.current_word = self.words_list[self.current_index]
        self.showing_definition = False
        
        self.card_label.config(text=self.current_word.upper())
        self.progress_label.config(text=f"Word {self.current_index + 1} of {len(self.words_list)}")
        self.hint_label.config(text="Click 'SHOW DEFINITION' to reveal the answer")
        self.show_btn.config(text="[ SHOW DEFINITION ]", fg="blue")
        
        if self.current_word in self.favorites:
            self.fav_btn.config(text="★ REMOVE FROM FAVORITES", fg="gold")
        else:
            self.fav_btn.config(text="☆ ADD TO FAVORITES", fg="gold")
    
    def show_definition(self):
        if not self.current_word:
            return
        
        if not self.showing_definition:
            definition = self.vocab.get(self.current_word, "Definition not available.")
            self.card_label.config(text=definition, font=(FONT_FAMILY, FONT_SIZE + 1))
            self.showing_definition = True
            self.hint_label.config(text="Click 'NEXT' for another word or 'SHOW' to hide definition")
            self.show_btn.config(text="[ HIDE DEFINITION ]", fg="red")
        else:
            self.card_label.config(text=self.current_word.upper(), font=(FONT_FAMILY, FONT_SIZE + 4, "bold"))
            self.showing_definition = False
            self.hint_label.config(text="Click 'SHOW DEFINITION' to reveal the answer")
            self.show_btn.config(text="[ SHOW DEFINITION ]", fg="blue")
    
    def next_card(self):
        if not self.words_list:
            return
        
        self.current_index = (self.current_index + 1) % len(self.words_list)
        self.show_card()
    
    def prev_card(self):
        if not self.words_list:
            return
        
        self.current_index = (self.current_index - 1) % len(self.words_list)
        self.show_card()
    
    def shuffle_cards(self):
        if not self.words_list:
            return
        
        random.shuffle(self.words_list)
        self.current_index = 0
        self.show_card()
        self.hint_label.config(text="Cards shuffled! Starting from first card.")
    
    def toggle_favorite(self):
        if not self.current_word:
            return
        
        if self.current_word in self.favorites:
            del self.favorites[self.current_word]
            self.fav_btn.config(text="☆ ADD TO FAVORITES", fg="gold")
            messagebox.showinfo("Removed", f"☆ '{self.current_word}' removed from favorites!")
        else:
            self.favorites[self.current_word] = self.vocab[self.current_word]
            self.fav_btn.config(text="★ REMOVE FROM FAVORITES", fg="gold")
            messagebox.showinfo("Added", f"★ '{self.current_word}' added to favorites!")
        
        self.parent.save_data(FAVORITES_FILE, self.favorites)
        self.parent.update_listbox()

class VocabularyManager:
    def __init__(self, root):
        self.root = root
        self.root.title("RETRO VOCAB. BUILDER UPDATED")
        self.root.geometry("850x650")
        self.root.configure(bg=RETRO_BG)
       
        self.vocab = self.load_data(DATA_FILE)
        self.favorites = self.load_data(FAVORITES_FILE)
        self.current_view = "all"

        self.create_widgets()
        self.update_listbox()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_data(self, filename):
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_data(self, filename, data):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError:
            messagebox.showerror("Error", f"Could not save data to {filename}.")

    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg=RETRO_BG, relief="raised", bd=3)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        title = tk.Label(
            main_frame,
            text="═══ VOCABULARY BUILDER ═══",
            font=(FONT_FAMILY, FONT_SIZE + 4, "bold"),
            bg=RETRO_BG,
            fg=RETRO_FG,
            relief="flat"
        )
        title.pack(pady=(5, 10))

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

        self.flashcard_btn = tk.Button(
            btn_frame,
            text="[ ★ FLASHCARDS ]",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=RETRO_BUTTON,
            fg="orange",
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=3,
            command=self.open_flashcards
        )
        self.flashcard_btn.pack(side="left", padx=5)

        self.test_btn = tk.Button(
            btn_frame,
            text="[ TEST API ]",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=RETRO_BUTTON,
            fg="green",
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=3,
            command=self.test_connection
        )
        self.test_btn.pack(side="left", padx=5)

        view_frame = tk.Frame(main_frame, bg=RETRO_BG)
        view_frame.pack(pady=5)

        self.view_all_btn = tk.Button(
            view_frame,
            text="[ ALL WORDS ]",
            font=(FONT_FAMILY, FONT_SIZE - 1, "bold"),
            bg=RETRO_BUTTON,
            fg="black",
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=2,
            command=lambda: self.change_view("all")
        )
        self.view_all_btn.pack(side="left", padx=5)

        self.view_fav_btn = tk.Button(
            view_frame,
            text="[ ★ FAVORITES ]",
            font=(FONT_FAMILY, FONT_SIZE - 1, "bold"),
            bg=RETRO_SELECT,
            fg="white",
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=2,
            command=lambda: self.change_view("favorites")
        )
        self.view_fav_btn.pack(side="left", padx=5)

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

        self.listbox.bind("<Double-Button-1>", self.show_definition_popup)
        self.listbox.bind("<Button-3>", self.show_context_menu)

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="★ Add to Favorites", command=self.add_to_favorites)
        self.context_menu.add_command(label="☆ Remove from Favorites", command=self.remove_from_favorites)

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

        self.entry.focus_set()

    def open_flashcards(self):
        if not self.vocab:
            messagebox.showwarning("Empty Vocabulary", "You need to add some words first!\nUse 'LOOKUP & ADD' to build your vocabulary.")
            return
        flashcard_window = FlashcardWindow(self.root, self.vocab, self.favorites)

    def show_context_menu(self, event):
        try:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.listbox.nearest(event.y))
            self.context_menu.post(event.x_root, event.y_root)
        except:
            pass

    def get_selected_word(self):
        selected = self.listbox.curselection()
        if not selected:
            return None
        index = selected[0]
        item_text = self.listbox.get(index)
        word = item_text.split(" - ")[0].strip()
        if word.startswith("★"):
            word = word[2:].strip()
        return word

    def add_to_favorites(self):
        word = self.get_selected_word()
        if not word:
            self.status.config(text="No word selected.")
            return
        
        if word not in self.favorites and word in self.vocab:
            self.favorites[word] = self.vocab[word]
            self.save_data(FAVORITES_FILE, self.favorites)
            self.status.config(text=f"★ Added '{word}' to favorites!")
            self.update_listbox()
        elif word in self.favorites:
            self.status.config(text=f"'{word}' is already in favorites.")
        else:
            self.status.config(text=f"'{word}' not found in vocabulary.")

    def remove_from_favorites(self):
        word = self.get_selected_word()
        if not word:
            self.status.config(text="No word selected.")
            return
        
        if word in self.favorites:
            del self.favorites[word]
            self.save_data(FAVORITES_FILE, self.favorites)
            self.status.config(text=f"☆ Removed '{word}' from favorites.")
            self.update_listbox()
        else:
            self.status.config(text=f"'{word}' is not in favorites.")

    def change_view(self, view):
        self.current_view = view
        self.update_listbox()
        if view == "all":
            self.status.config(text="Showing all words.")
        else:
            self.status.config(text="Showing favorites only.")

    def test_connection(self):
        self.status.config(text="Testing dictionary services...")
        self.root.update_idletasks()
        
        test_words = ["book", "computer", "happy"]
        results = []
        
        for test_word in test_words:
            result = fetch_definition(test_word)
            if "not found" not in result.lower() and "error" not in result.lower() and "available" not in result.lower():
                results.append(f"✅ '{test_word}': {result[:50]}...")
            else:
                results.append(f"❌ '{test_word}': Failed - {result[:30]}")
        
        summary = "\n".join(results)
        
        if any("✅" in r for r in results):
            self.status.config(text="✅ Dictionary services working")
            messagebox.showinfo("Test Results", 
                f"Dictionary Test Results:\n\n{summary}")
        else:
            self.status.config(text="❌ All dictionary services failed")
            messagebox.showwarning("Test Results", 
                f"Dictionary Test Results:\n\n{summary}\n\n"
                "Please check your internet connection.")

    def lookup_and_add(self):
        word = self.word_var.get().strip()
        if not word:
            self.status.config(text="Please enter a word or phrase.")
            return

        if word in self.vocab:
            self.status.config(text=f"'{word}' already exists in vocabulary.")
            messagebox.showinfo("Already Exists", f"'{word}' is already in your vocabulary.")
            self.word_var.set("")
            self.entry.focus_set()
            return

        self.status.config(text=f"Looking up '{word}'...")
        self.root.update_idletasks()

        definition = fetch_definition(word)

        self.vocab[word] = definition
        self.save_data(DATA_FILE, self.vocab)
        self.update_listbox()

        self.word_var.set("")
        
        if len(definition) > 60:
            status_text = f"Added: '{word}' -> {definition[:60]}..."
        else:
            status_text = f"Added: '{word}' -> {definition}"
        self.status.config(text=status_text)
        
        self.entry.focus_set()

        items = self.listbox.get(0, tk.END)
        for i, item in enumerate(items):
            if item.startswith(word + " -") or item.startswith("★ " + word + " -"):
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
        word = item_text.split(" - ")[0].strip()
        if word.startswith("★"):
            word = word[2:].strip()

        if word in self.vocab:
            del self.vocab[word]
            self.save_data(DATA_FILE, self.vocab)
            if word in self.favorites:
                del self.favorites[word]
                self.save_data(FAVORITES_FILE, self.favorites)
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
            self.favorites.clear()
            self.save_data(DATA_FILE, self.vocab)
            self.save_data(FAVORITES_FILE, self.favorites)
            self.update_listbox()
            self.status.config(text="All entries cleared.")

    def show_definition_popup(self, event):
        selected = self.listbox.curselection()
        if not selected:
            return
        index = selected[0]
        item_text = self.listbox.get(index)
        word = item_text.split(" - ")[0].strip()
        if word.startswith("★"):
            word = word[2:].strip()

        definition = self.vocab.get(word, "Definition not available.")

        popup = tk.Toplevel(self.root)
        popup.title(f"Definition: {word}")
        popup.configure(bg=RETRO_BG)
        popup.geometry("600x300")
        popup.resizable(False, False)

        popup.transient(self.root)
        popup.grab_set()

        label_frame = tk.Frame(popup, bg=RETRO_BG)
        label_frame.pack(pady=(15, 5), fill="x")

        label = tk.Label(
            label_frame,
            text=f"WORD: {word}",
            font=(FONT_FAMILY, FONT_SIZE + 2, "bold"),
            bg=RETRO_BG,
            fg=RETRO_FG
        )
        label.pack(side="left", padx=(15, 10))

        fav_status = "★" if word in self.favorites else "☆"
        fav_label = tk.Label(
            label_frame,
            text=fav_status,
            font=(FONT_FAMILY, FONT_SIZE + 4, "bold"),
            bg=RETRO_BG,
            fg="gold"
        )
        fav_label.pack(side="left")

        text_widget = scrolledtext.ScrolledText(
            popup,
            font=(FONT_FAMILY, FONT_SIZE),
            bg=RETRO_HIGHLIGHT,
            fg=RETRO_FG,
            relief="sunken",
            bd=2,
            wrap=tk.WORD,
            height=8
        )
        text_widget.pack(padx=15, pady=5, fill="both", expand=True)
        text_widget.insert(tk.END, definition)
        text_widget.config(state="disabled")

        btn_frame = tk.Frame(popup, bg=RETRO_BG)
        btn_frame.pack(pady=10)

        close_btn = tk.Button(
            btn_frame,
            text="[ CLOSE ]",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=RETRO_BUTTON,
            fg=RETRO_FG,
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=3,
            command=popup.destroy
        )
        close_btn.pack(side="left", padx=5)

        if word in self.favorites:
            fav_btn_text = "☆ REMOVE FROM FAVORITES"
            fav_cmd = self.remove_from_favorites
        else:
            fav_btn_text = "★ ADD TO FAVORITES"
            fav_cmd = self.add_to_favorites

        fav_btn = tk.Button(
            btn_frame,
            text=fav_btn_text,
            font=(FONT_FAMILY, FONT_SIZE - 1, "bold"),
            bg=RETRO_BUTTON,
            fg="white",
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=3,
            command=lambda: [fav_cmd(), popup.destroy()]
        )
        fav_btn.pack(side="left", padx=5)

        popup.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (popup.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        
        if self.current_view == "all":
            items = sorted(self.vocab.items())
        else:
            items = sorted(self.favorites.items())
        
        for word, definition in items:
            display_def = definition[:60] + "..." if len(definition) > 60 else definition
            if word in self.favorites:
                self.listbox.insert(tk.END, f"★ {word} - {display_def}")
            else:
                self.listbox.insert(tk.END, f"  {word} - {display_def}")

    def on_close(self):
        self.save_data(DATA_FILE, self.vocab)
        self.save_data(FAVORITES_FILE, self.favorites)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VocabularyManager(root)
    root.mainloop()
