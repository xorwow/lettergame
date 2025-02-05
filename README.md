# lettergame

*Play a word-guessing game!*

## Rules

- The computer chooses an N-letter word from a dictionary file.
    - The word has no repeated letters.
- Each round, you guess a word following those same rules.
    - The computer tells you how many letters of your guess are also in the correct word.
    - It ignores the position of the letters, i.e. NOTES and STONE will have the same result.
- When you guess the correct word, you win!
- You should only be guessing real words, so it isn't too easy.

An example:

```text
The computer secretly chooses the word 'EARTH'.
You guess 'GIRTH' -- 3 letters are correct (R, T, H).
You guess 'BIRTH' -- 3 letters are correct (R, T, H).
It is now probable that GI and BI are both incorrect (but not definite!).
To be sure, you guess 'BINGO' -- 0 letters are correct, so you know it must be R, T, and H.
You guess 'HEART' -- 5 letters are correct, but the order is not.
You guess 'EARTH' -- you win.
```

## Installation

### Using a [virtual environment](https://docs.python.org/3/library/venv.html)

```sh
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate
# Install pip package
pip install lettergame
```

Note that the virtual environment must be active when using the command.

### Using [pipx](https://github.com/pypa/pipx)

```sh
# Install pipx
pip install pipx
# Install pip package globally using pipx
pipx install lettergame
```

### Using a manual link

```sh
# Clone this repository
git clone https://github.com/xorwow/lettergame
# Link to the game file from your BIN
ln -s lettergame/src/lettergame/game.py ~/.local/bin/lettergame
```

## Usage

First, install a dictionary file (see below). Then, start a game by running `lettergame` in your terminal (must have color support).

### Dictionary file

To play the game, a dictionary file is required. It contains the words the computer can choose from. It is recommended to use non-plural nouns. You can find lists of common nouns online.

The game expects one word per line. The words can be any length. On start, the game loads all words that:
- Don't have any repeating characters.
- Fit the target word length.
- Only contain A-Z/a-z.

By default, the game look for this file in `~/.config/lettergame/words.txt`.

### Options

The following flags are available:
- `--word-length|-n <number>` specifies the target word size.
- `--dict-file|-f <path>` specifies a custom path to the dictionary file.
- `--load-hash|-l <hash>` forces the game to choose the target word of a previous game.
    - The shortened hash of the chosen word is shown at the beginning of the game.
    - This can be used to continue an interrupted game (although previous guesses are not loaded).
- `--difficult|-d` disables automatic marking of letters based on obvious clues (see below).

### Marking letters

The game shows you the alphabet and a list of previous guesses at the beginning of each round, with letters colored green, yellow, or red to keep track of which letters you have already ruled out or assume to be correct. Green means correct, red means incorrect, and yellow means unknown. This is meant as a memory aid, and will not influence the game's logic.

You can mark letters as correct/incorrect/unknown by entering `+<letters>`, `-<letters>`, or `~<letters>` in the guess prompt. For example, enter `+abc` to mark a, b, and c as correct. They will be shown in green in the alphabet and the list of previous guesses.

If `--difficult` mode is not enabled, the game will also automatically mark letters in some obvious cases for convenience:
- If a guess has no matches, all of its letters are marked as incorrect.
- If the number of matches is equal to the amount of letters in the guess which aren't already marked as incorrect, all other letters are marked as correct (ex.: `CASE` matches 3 letters and C is marked as incorrect -> A, S, and E must be correct).
- If the number of matches is equal to the amount of letters in the guess which are already marked as correct, all other letters are marked as incorrect.
- If all correct letters have been guessed, all other letters are marked as incorrect.

Note that falsely marking a letter as (in)correct may create additional false marks based on that assumption.

### Cheating

If you give up but still want to know the correct word, enter `_reveal` in the guess prompt.
