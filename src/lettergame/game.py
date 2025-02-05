#!/usr/bin/env python3

# External package(s): termcolor

import os, random, traceback
import readline as _ # importing readline allows for arrow-up/-down in input()
from typing import Any
from enum import StrEnum
from hashlib import sha1
from builtins import print as std_print
from argparse import ArgumentParser, RawDescriptionHelpFormatter, Namespace

from termcolor import colored

## TERMINAL HELPERS

class Color(StrEnum):
    '''Available terminal message colors.'''
    PROMPT = 'light_magenta'
    INFO = 'light_cyan'
    GOOD = 'light_green'
    MEH  = 'light_yellow'
    BAD  = 'light_red'

# Overwrite standard print function with color support
def print(msg: Any, color: Color = Color.INFO, **print_args) -> None:
    '''Output colored text to the terminal.'''
    std_print(colored(str(msg), color=color.value), **print_args) # type: ignore

## LOGIC

ALPHABET: str = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

class GameException(Exception):
    pass

class Guess():
    '''Represents a single guessed word. Exposes the fields `word` (the guess) and `matching` (the number of matching letters).'''

    def __init__(self, game: 'Game', guess: str) -> None:
        '''
        Takes the game instance (for data like the target size) and the guessed word.
        Assumes the word to be a valid guess (use `Guess.invalid(...)` to check a guess beforehand).
        '''
        self.game: 'Game' = game
        self.word: str = guess.upper()
        self.matching: int = self.game.size - len(set(self.game.word).difference(set(self.word)))

    def correct(self) -> bool:
        '''Check if the guess is correct.'''
        return self.word == self.game.word

    @staticmethod
    def invalid(word_size: int, guess: str) -> None | str:
        '''If the guess is invalid, returns a message stating the reason. If it is valid, None is returned.'''
        if any(letter not in ALPHABET for letter in guess.upper()):
            return 'Guess may only contain A-Z/a-z letters'
        if len(guess) != word_size:
            return f"Guess must be { word_size } letters long"
        if len(guess) != len(set(guess)):
            return 'Guess cannot have repeating letters'
        return None

    def color_word(self) -> str:
        '''Colors each letter of a word by its mark.'''
        return ''.join([ Guess.color_letter(self.game, letter) for letter in self.word ])

    @staticmethod
    def color_letter(game: 'Game', letter: str) -> str:
        '''Colors a letter by its mark (green = marked correct, red = marked incorrect, yellow = unmarked).'''
        color: Color = Color.GOOD if letter in game.marked_pos else (Color.BAD if letter in game.marked_neg else Color.MEH)
        return colored(letter, color.value)

    def color_matching(self, smart: bool = False) -> str:
        '''
        Colors the number of matching letters (red = 0 matches, green = all matches, yellow = inbetween).
        If `smart` is set, it will also be colored green if all letters in the guess have already been marked.
        '''
        color: Color = Color.GOOD if self.matching == self.game.size else Color.MEH
        # Check if all letters have already been marked, if so, color it as good (will also match the case where all are incorrect)
        if smart and all(letter in self.game.marked_pos or letter in self.game.marked_neg for letter in self.word):
            color = Color.GOOD
        # If 0 matches is considered bad and we have 0 matches, color it as bad (will handle 'all are incorrect' case above)
        if not smart and self.matching == 0:
            color = Color.BAD
        return colored(self.matching, color.value)

class Game():
    '''A single game session. Start the game (over) by calling `<game>.play()`.'''

    def __init__(self, word_size: int, dict_file: str, word: str | None = None, assist_eval: bool = True) -> None:
        '''
        Configure the game's parameters:
        - `word_size`: Target word size
        - `dict_file`: File to load words from (should contain one word per line)
        - `word`: Use a fixed word as the target (has to match `word_size`)
        - `assist_eval`: Enable automatic marking of letters based on some obvious cases
        '''
        self.size: int = word_size
        self.words: list[str] = Game.load_valid_words(dict_file, self.size)
        if len(self.words) < 10:
            raise GameException(f"Not enough { self.size }-letter words available to play")
        # Initialize per-game variables
        self._reset(word=word)
        # The assistant automatically evaluates which letters are (in)correct (without cheating)
        self.enable_assist: bool = assist_eval

    def play(self) -> None:
        '''Play the game in the terminal.'''
        print(
            f"{ len(self.words) } { self.size }-letter words available, chose { Game.hash_word(self.word) }", Color.GOOD
        )
        print('When prompted, enter a guess or a string of letters prefixed with +/-/~ to mark them as correct/incorrect/unknown')
        print('Example: +abc would mark a, b, and c as correct letters and highlight them in the alphabet header\n')
        while not self.play_round():
            print('')
        print(
            f"Congratulations! You guessed { self.word } in { len(self.guesses) } { 'try' if len(self.guesses) == 1 else 'tries' }!",
             Color.GOOD
        )
        self._reset()

    def play_round(self) -> bool:
        '''Play a single round, where the user guesses and the guess is evaluated. Returns True if the user won in this round.'''
        # Evaluate the previous guesses and mark letters accordingly, then print the marks and previous guesses
        self._eval_guesses()
        self._print_header()
        # Prompt for a guess
        # If None is returned, the user typed a command instead, so we return and start the next round
        if not (guess := self._prompt_guess()):
            return False
        # Add to guesses and check if the user won
        self.guesses.append(guess)
        if guess.correct():
            return True
        # Print the amount of matches (calls are split for coloring reasons)
        print(f"You guessed { guess.color_matching(smart=False) }", end='')
        print(f" letter{ 's' * (guess.matching != 1) } correctly", end='')
        print(f"{ ' (in incorrect order)' * (not guess.correct() and guess.matching == self.size) }", Color.MEH)
        return False

    def _reset(self, word: str | None = None) -> None:
        '''Reset the per-game data.'''
        self.word: str = word or random.choice(self.words)
        self.guesses: list[Guess] = []
        # Letters marked as correct (pos) or incorrect (neg)
        self.marked_pos: set[str] = set()
        self.marked_neg: set[str] = set()
        self._user_marked_pos: set[str] = set()
        self._user_marked_neg: set[str] = set()

    def _prompt_guess(self) -> Guess | None:
        '''Prompt the user for a guess or execute a command. Return None if the guess was invalid or a command.'''
        raw: str = input(colored('Guess? > ', Color.PROMPT.value)).upper()
        if raw == '_REVEAL':
            print(f"The word is { self.word }", Color.MEH)
            return None
        if len(raw) > 0 and (prefix := raw[0]) in [ '+', '-', '~' ]:
            for letter in raw[1:]:
                if prefix == '~':
                    self._mark_unk(letter, by_user=True)
                if prefix == '+':
                    self._mark_pos(letter, by_user=True)
                if prefix == '-':
                    self._mark_neg(letter, by_user=True)
            return None
        if (reason := Guess.invalid(self.size, raw)):
            print(reason, Color.BAD)
            return None
        return Guess(self, raw)

    def _eval_guesses(self) -> None:
        '''If the assist is enabled, auto-mark letters for some obvious cases.'''
        # Reset marks to only those explicitly set by the user (to allow for complex undos), then re-evaluate guesses
        self.marked_pos = self._user_marked_pos.copy()
        self.marked_neg = self._user_marked_neg.copy()
        # Early abort if assist is disabled
        if not self.enable_assist:
            return
        # Propagate mark updates until marks aren't changing anymore
        changed: bool = True
        while changed:
            prev_pos: set[str] = self.marked_pos.copy()
            prev_neg: set[str] = self.marked_neg.copy()
            for guess in self.guesses:
                letters: set[str] = set(guess.word)
                # No matching letters: mark all incorrect
                if guess.matching == 0:
                    [ self._mark_neg(letter) for letter in letters ]
                # All letters not marked as incorrect match: mark them correct
                not_incorrect: set[str] = letters.difference(self.marked_neg)
                if len(not_incorrect) == guess.matching:
                    [ self._mark_pos(letter) for letter in not_incorrect ]
                # All matching letters found: mark others incorrect
                correct: set[str] = letters.intersection(self.marked_pos)
                if len(correct) == guess.matching:
                    [ self._mark_neg(letter) for letter in letters.difference(correct) ]
            changed = (prev_pos != self.marked_pos) or (prev_neg != self.marked_neg)
        # If we found all correct letters, mark all others as incorrect
        if len(self.marked_pos) == self.size:
            for letter in ALPHABET:
                if letter not in self.marked_pos:
                    self._mark_neg(letter)

    def _print_header(self) -> None:
        '''Print the marked/highlighted alphabet and previous guesses.'''
        # Highlighted alphabet
        for letter in ALPHABET:
            std_print(f"{ Guess.color_letter(self, letter) } ", end='')
        print(f"({ colored(len(ALPHABET) - len(self.marked_pos) - len(self.marked_neg), Color.MEH.value) }", end='')
        if self.marked_neg:
            print(f" { len(self.marked_neg) }", Color.BAD, end='')
        if self.marked_pos:
            print(f" { len(self.marked_pos) }", Color.GOOD, end='')
        print(')', end='')
        print(f" { ' '.join(sorted(self.marked_pos)) }\n", Color.GOOD)
        # Highlighted previous guesses
        if self.guesses:
            DELIMITER: str = '   '
            WORDS_PER_LINE: int = 80 // (self.size + 1 + len(str(self.size)) + len(DELIMITER))
            for index, guess in enumerate(self.guesses):
                std_print(f"{ guess.color_word() } { guess.color_matching(smart=True) }{ DELIMITER }", end='')
                if (index + 1) % WORDS_PER_LINE == 0 and (index + 1) != len(self.guesses):
                    print('')
            print('\n')

    def _mark_pos(self, letter: str, by_user: bool = False) -> None:
        '''Mark a letter as correct.'''
        (self._user_marked_pos if by_user else self.marked_pos).add(letter)
        (self._user_marked_neg if by_user else self.marked_neg).discard(letter)

    def _mark_neg(self, letter: str, by_user: bool = False) -> None:
        '''Mark a letter as incorrect.'''
        (self._user_marked_pos if by_user else self.marked_pos).discard(letter)
        (self._user_marked_neg if by_user else self.marked_neg).add(letter)

    def _mark_unk(self, letter: str, by_user: bool = False) -> None:
        '''Mark a letter as unknown.'''
        (self._user_marked_pos if by_user else self.marked_pos).discard(letter)
        (self._user_marked_neg if by_user else self.marked_neg).discard(letter)

    @staticmethod
    def load_valid_words(dictionary_path: str, word_size: int) -> list[str]:
        '''Load unique valid words from a dictionary file. The file should contain a single word on each line.'''
        with open(dictionary_path) as dictfile:
            return list({
                word for word in map(lambda w: w.upper(), dictfile.read().split('\n'))
                if not Guess.invalid(word_size, word)
            })

    @staticmethod
    def hash_word(word: str) -> str:
        '''Calculate the SHA-1 hash of a word and shorten it to 8 characters.'''
        return str(sha1(word.encode('utf-8')).hexdigest())[:8]

## SCRIPT ENTRY

EPILOG: str = '''
rules:
- the computer chooses an N-letter word which contains no repeated characters
- each round, you guess a word that follows those same rules
- the computer tells you how many letters of your guess are also in the correct word (order is ignored)
- guess the correct word to win
'''

DEFAULT_WORD_SIZE: int = 5
DEFAULT_DICT_FILE: str = os.path.expanduser('~/.config/lettergame/words.txt')

def main() -> None:
    # Parse args
    args: ArgumentParser = ArgumentParser(
        epilog = EPILOG,
        formatter_class = RawDescriptionHelpFormatter,
        description = 'play a word guessing game!'
    )
    args.add_argument(
        '--word-length', '-n', type=int, metavar='<N>', default=DEFAULT_WORD_SIZE,
        help=f"length of the word you need to guess (default: { DEFAULT_WORD_SIZE })"
    )
    args.add_argument(
        '--dict-file', '-f', type=str, metavar='<path>', default=DEFAULT_DICT_FILE,
        help=f"path of a dictionary file (containing one word per line) (default: { DEFAULT_DICT_FILE })"
    )
    args.add_argument(
        '--load-hash', '-l', type=str, dest='hash', metavar='<hash>',
        help='load the word of a previous session by providing its word hash (does not restore guessed words)'
    )
    args.add_argument(
        '--difficult', '-d', action='store_false', dest='assist',
        help='no automatic assist in evaluating the clues (disables automatic coloring of letters)'
    )
    config: Namespace = args.parse_args()
    # Prepare and run game
    try:
        word: str | None = None
        # Load word from hash if requested
        if config.hash:
            for _word in Game.load_valid_words(config.dict_file, config.word_length):
                if Game.hash_word(_word) == config.hash:
                    word = _word
                    break
            else:
                raise GameException(f"No { config.word_length }-letter word matching the hash has been found")
            print('Loaded word from hash', Color.GOOD)
        # Start game
        Game(config.word_length, config.dict_file, word=word, assist_eval=config.assist).play()
    except KeyboardInterrupt:
        pass
    except GameException as e:
        print(e, Color.BAD)
    except:
        print(traceback.format_exc(), Color.BAD)

if __name__ == '__main__':
    main()
