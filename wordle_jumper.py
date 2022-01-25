import multiprocessing as mp
import re
import colorama
import time


ALL_ANSWERS = set()
ALL_GUESSES = set()

with open("answers.txt") as answers, open("guesses.txt") as guesses:
    ALL_ANSWERS = {line.rstrip() for line in answers.readlines()}
    ALL_GUESSES = {line.rstrip() for line in guesses.readlines()}

class ColorFormat:
    GREEN = '\033[37;42m'
    YELLOW = '\033[30;43m'
    GRAY = '\033[37;100m'
    END = '\033[0m'

class Pattern:
    def __init__(self, guess, number):
        self.greens = dict()
        self.yellows = dict()
        self.grays = set()

        for i in range(5):
            letter = guess[i]
            color = number[i]
            match color:
                case '2':
                    self.add_green(i, letter)
                case '1':
                    self.add_yellow(i, letter)
                case '0':
                    self.add_gray(letter)

    def __hash__(self):
        return hash((frozenset(self.greens),
                     frozenset(self.yellows),
                     frozenset(self.grays)))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return "Pattern" + str(self.__dict__)

    @classmethod
    def from_word_pair(cls, guess, answer):
        answer = list(answer)
        guess_copy = guess
        guess = list(guess)

        number = [None]*5

        for i in range(5):
            if guess[i] == answer[i]:
                number[i] = '2'
                answer[i] = None
                guess[i] = None
        for i in range(5):
            if guess[i] != None and guess[i] in answer:
                number[i] = '1'
                answer[answer.index(guess[i])] = None
            elif not number[i]:
                number[i] = '0'
        number = ''.join(number)
        return Pattern(guess_copy, number)

    def print(self, word):
        output = ""
        for i in range(5):
            if i in self.greens:
                output += ColorFormat.GREEN
            elif i in self.yellows:
                output += ColorFormat.YELLOW
            else:
                output += ColorFormat.GRAY
            output += word[i]
        output += ColorFormat.END
        print(output)
        return
    
    def add_green(self, index, letter):
        self.greens[index] = letter

    def add_yellow(self, index, letter):
        self.yellows[index] = letter

    def add_gray(self, letter):
        self.grays.add(letter)

    def matches(self, candidate):
        candidate = list(candidate)
        for index in self.greens:
            if self.greens[index] != candidate[index]:
                return False
            else:
                candidate[index] = None
        for index in self.yellows:
            yellow_letter = self.yellows[index]
            if (candidate[index] == yellow_letter or
                    yellow_letter not in candidate):
                return False
            else:
                candidate[candidate.index(yellow_letter)] = None
        for letter in self.grays:
            if letter in candidate:
                return False
                
        return True

    def filter(self, candidates):
        valid = set()
        for candidate in candidates:
            if pattern.matches(candidate):
                valid.add(candidate)
        return valid

def count_valid_candidates(pattern, candidates, cache):
    num_valid = 0
    if pattern in cache:
        return cache[pattern]
    else:
        for candidate in candidates:
            if pattern.matches(candidate):
                num_valid += 1
        cache[pattern] = num_valid
        return num_valid

def evaluate_guess(guess, candidate_answers):
    score = 0
    cache = dict()
    for answer in candidate_answers:
        pattern = Pattern.from_word_pair(guess, answer)
        score += count_valid_candidates(pattern, candidate_answers, cache)
    return score
        
def best_guess(n=1, candidate_guesses=ALL_GUESSES, candidate_answers=ALL_ANSWERS):
    pool = mp.Pool()
    guess_to_score = dict()
    for guess in candidate_guesses:
        score = pool.apply_async(evaluate_guess, args = (guess, candidate_answers))
        guess_to_score[guess] = score.get()
    pool.close()
    pool.join()

    return sorted(guess_to_score, key=guess_to_score.get)[:n]

def guessInput(guessNumber):
    guess = str()
    valid = False
    while not valid:
        guess = input("Guess {}: ".format(guessNumber)).lower()
        if re.fullmatch(r'[a-z]{5}', guess):
            valid = True
        else:
            print("Guess must be five letters.")
    return guess
    
def colorInput():
    colorCode = str()
    valid = False
    while not valid:
        colorCode = input("How is it colored? (0 for gray, 1 for yellow, 2 for green): ")
        if re.fullmatch(r'[0-2]{5}', colorCode):
            valid = True
        else:
            print("Please input 5 digits (0 for gray, 1 for yellow, 2 for green):")
    return colorCode

if __name__ == "__main__":

    colorama.init()

    should_restart = True
    while should_restart:
        should_restart = False
        
        candidate_answers = ALL_ANSWERS
        candidate_guesses = ALL_GUESSES

        print("The best first guess is roate. What did you guess?")

        for i in range(6):
            guess = guessInput(i+1)
            color = colorInput()

            pattern = Pattern(guess, color)
            if(color == "22222"):
                pattern.print(guess)
                print("yay we did it! :)")
                quit()

            candidate_answers = pattern.filter(candidate_answers)
            pattern.print(guess)

            numCandidates = len(candidate_answers)
            pluralize = "" if numCandidates == 1 else "s"
            percent = numCandidates/len(ALL_ANSWERS)
            print("Narrowed it down to {} possible word{}--{:.0%} of the total.".format(numCandidates, pluralize, percent))
            if numCandidates == 0:
                print("Something must have gone wrong. Try again.")
                should_restart = True
                break

            if numCandidates == 1:
                print("The answer must be {}.".format(next(iter(candidate_answers))))
            else:
                print("Computing optimal guesses.")
                start_time = time.perf_counter()
                suggestions = best_guess(5, candidate_answers=candidate_answers)
                elapsed = time.perf_counter() - start_time
                print("Done in {:.3f} seconds.".format(elapsed))

                print("Best guesses (lower number = more informative on average):")
                suggestion_scores = [evaluate_guess(x, candidate_answers) for x in suggestions]
                print(["{} ({})".format(suggestions[i], suggestion_scores[i]) for i in range(len(suggestions))])