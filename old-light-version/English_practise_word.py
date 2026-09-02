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

# ---------------------------------------------------------------------
def fetch_definition(word):
  
    # Clean input
    word = word.strip().lower()
    if not word:
        return "Please enter a word or phrase."

    try:
        # Cambridge Dictionary URL
        url = f"https://dictionary.cambridge.org/dictionary/english/{urllib.parse.quote(word)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the definition
            # Cambridge Dictionary uses specific class names
            definitions = []
            
            # Try different class names that Cambridge uses
            definition_elements = soup.find_all('div', class_='def')
            if not definition_elements:
                definition_elements = soup.find_all('div', class_='ddef_d')
            if not definition_elements:
                definition_elements = soup.find_all('span', class_='def')
            if not definition_elements:
                definition_elements = soup.find_all('div', class_='def-body')
            
            for element in definition_elements[:3]:  # Get first 3 definitions
                # Get the text, clean it up
                text = element.get_text().strip()
                # Remove extra whitespace and newlines
                text = ' '.join(text.split())
                if text and len(text) > 10:  # Avoid empty or very short entries
                    definitions.append(text)
            
            # If we found definitions, return the first one
            if definitions:
                return f"(Cambridge) {definitions[0]}"
            else:
                # Try to find the word's part of speech and definition in a different way
                pos_elements = soup.find_all('span', class_='pos')
                if pos_elements:
                    pos = pos_elements[0].get_text().strip()
                    # Find definition near the part of speech
                    def_elements = soup.find_all('span', class_='def')
                    if def_elements:
                        return f"({pos}) {def_elements[0].get_text().strip()}"
                
                # If still nothing, try alternative dictionary
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
    """
    Try Merriam-Webster Dictionary as backup
    """
    try:
        url = f"https://www.merriam-webster.com/dictionary/{urllib.parse.quote(word)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find definitions in Merriam-Webster
            definitions = []
            
            # Try different class names
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
                # Try to get the word's part of speech
                pos_elements = soup.find_all('span', class_='fl')
                if pos_elements:
                    pos = pos_elements[0].get_text().strip()
                    # Try to find any definition text
                    for element in soup.find_all(['p', 'div', 'span']):
                        text = element.get_text().strip()
                        if text and len(text) > 20 and not text.startswith('http'):
                            return f"({pos}) {text[:200]}"
                
                return try_wordnik(word)
        
        return try_wordnik(word)
        
    except:
        return try_wordnik(word)

def try_wordnik(word):
    """
    Try Wordnik API (has a free tier)
    """
    try:
        # Wordnik free API (no key required for basic definitions)
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
        
        # If all fails, try a simple approach: use a free dictionary API
        return try_dictionary_api(word)
        
    except:
        return try_dictionary_api(word)

def try_dictionary_api(word):
    """
    Final fallback: Use the free dictionary API
    """
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

# ---------------------------------------------------------------------
# VOCABULARY MANAGER
# ---------------------------------------------------------------------
class VocabularyManager:
    def __init__(self, root):
        self.root = root
        self.root.title("RETRO VOCAB. BUILDER")
        self.root.geometry("750x600")
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

        self.test_btn = tk.Button(
            btn_frame,
            text="[ TEST DICTIONARY ]",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=RETRO_BUTTON,
            fg="green",
            activebackground=RETRO_ACTIVE,
            relief="raised",
            bd=3,
            command=self.test_connection
        )
        self.test_btn.pack(side="left", padx=5)

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
    # TEST CONNECTION
    # -----------------------------------------------------------------
    def test_connection(self):
        """Test if the dictionary services are working"""
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
        
        # Show the definition in status
        if len(definition) > 60:
            status_text = f"Added: '{word}' -> {definition[:60]}..."
        else:
            status_text = f"Added: '{word}' -> {definition}"
        self.status.config(text=status_text)
        
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
        popup.geometry("600x300")
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
            height=8
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
