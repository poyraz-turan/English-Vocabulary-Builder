# English-Vocabulary-Builder
A simple desktop application built with Python and Tkinter that helps you build your English vocabulary. Enter a word or phrase, and the program automatically retrieves its definition from online dictionary services and stores it.

! THIS IS THE FUN VERSION !
I used a strange API that gave strange results, didn't work for some words but they were funny. Results were funny so i wanted to keep it

✨ Features
Search for English words and phrases
Automatically fetch definitions from multiple online dictionary sources. 

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

-Future Improvements possible

Favorites (will do it)
Audio
Quiz mode (might be fun and effective but i want to make it simple.)
Dark mode (will do a button switch)
Import/Export vocabulary (its basic json file read you can just replace the json file program created)
Search within saved words





python English_practise_word.py
