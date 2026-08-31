# English-Vocabulary-Builder
A simple desktop application built with Python and Tkinter that helps you build your English vocabulary. Enter a word or phrase, and the program automatically retrieves its definition from online dictionary services and stores it.


✨ Features
Search for English words and phrases
Automatically fetch definitions from multiple online dictionary sources. (A possible problem is, i did try these API options and they worked for me. But before these, I tried dozens of other options. They did not work for me. So I used the best API options.)
Cambridge Dictionary
Merriam-Webster
Wordnik
Save your vocabulary locally in a .JSON file
🖱️ Double-click any word to view its full definition
Delete individual words
Clear the entire vocabulary list (with a button)
Built-in dictionary connection test (tests it with a few words entry. If It does return, successfully connected. I don't recommend you to do this unless you had issues. Because it takes a little time.)

I tried to do it retro Windows-style graphical interface themed. 

![Application Screenshot](screenshot.png)

Requirements
Python 3.9+
Internet connection (required for looking up new words.)
Required Python packages


Install the dependencies with:

pip install requests beautifulsoup4

Tkinter is included with most Python installations.

Installation

Clone the repository:

git clone https://github.com/yourusername/english-vocabulary-builder.git

Move into the project folder:

cd english-vocabulary-builder

Install the required packages:

pip install requests beautifulsoup4

Project Structure
.
├── English_practise_word.py
├── vocabulary.json      # created automatically
├── README.md
└── screenshot.png       # optional

Python
Tkinter
BeautifulSoup4
JSON save system.

This project is released under the MIT License.



Run the application:

python English_practise_word.py
