# wordle_jumper

Calculate optimal guessing strats for Wordle (https://www.powerlanguage.co.uk/wordle/).

Input your own guesses and find out what the best next move is.

Uses multiprocessing and caching to quickly select the most informative of ~13k possible guesses.

Command line interface. Written in Python, requires [colorama](https://pypi.org/project/colorama/).