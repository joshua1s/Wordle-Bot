
import time
import sys
from attr import has

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

def enterWord(driver, word):
    html = driver.find_element(By.TAG_NAME, 'html')
    html.send_keys(word)
    html.send_keys(Keys.ENTER)

    time.sleep(2)

def getRowEvaluation(driver, gameRow, knownWord, wordContains, wordDoesNotContain):

    # Get the tiles in the row from the site
    row = driver.execute_script('return arguments[0].shadowRoot.children', gameRow)[1]
    tiles = row.find_elements(By.TAG_NAME, 'game-tile')
    evals = []

    for i in range(0, 5):

        letter = tiles[i].get_attribute('letter')
        eval = tiles[i].get_attribute('evaluation')
        evals.append(eval)

        if eval == 'correct':
            knownWord[i] = letter
        elif eval == 'present':
            if letter not in wordContains:
                wordContains.append(letter)
        elif letter not in wordDoesNotContain:
            wordDoesNotContain.append(letter)

    # Sometimes we will guess a word with duplicate letters (ex. 'knoll')
    # If the letter is correct in the answer, the other letter will be marked as incorrect
    for char in wordDoesNotContain:
        if char in knownWord or char in wordContains:
            wordDoesNotContain.remove(char)

    return evals, knownWord, wordContains, wordDoesNotContain

# Simulate checking a guess in the wordle
def getTestEvaluation(answer, guess, knownWord, wordContains, wordDoesNotContain):

    eval = []
    for i in range(0, 5):

        if guess[i] in answer:
            if guess[i] == answer[i]:
                eval.append('correct')
                knownWord[i] = guess[i]
            else:
                eval.append('present')

                if guess[i] not in wordContains:
                    wordContains.append(guess[i])
        else:
            eval.append('absent')

            if guess[i] not in wordDoesNotContain:
                wordDoesNotContain.append(guess[i])  
    
    return eval, knownWord, wordContains, wordDoesNotContain
  
def trimAnswers(answers, knownWord, guesses, wordContains, wordDoesNotContain):

    newAnswersList = []

    for word in answers:

        hasWrongLetters = False

        if hasWrongLetters:
            continue

        # Check if there are any letters we know are wrong
        for char in wordDoesNotContain:
            if char in word:
                hasWrongLetters = True
                break

        if hasWrongLetters:
            continue
        
        # Is word missing correct letters?
        for char in wordContains:
            if char not in word:
                hasWrongLetters = True
                break
 
        if hasWrongLetters:
            continue

        # Check if the word has any known letters in the right spot
        for i in range(0, 5):
            if knownWord[i] != '_' and knownWord[i] != word[i]:
                hasWrongLetters = True
    
        if hasWrongLetters:
            continue

        for i in range(0, len(guesses)):

            # Check if word was guessed last
            if word == ''.join(guesses[i][0]):
                hasWrongLetters = True
                break

            # Check past evaluations to see if the word has correct letters but in the wrong spot
            for j in range(0, 5):
                if word[j] == guesses[i][0][j] and guesses[i][1][j] == 'present':
                    hasWrongLetters = True
                    break

        if not hasWrongLetters:
            newAnswersList.append(word)

    return newAnswersList

# Choose our next guess by the amount it will reduce possible answers
def chooseGuess(answers, knownWord, wordContains, wordDoesNotContain):

    bestGuess = ''
    leastAnswersLeft = sys.maxsize

    for ans in answers:

        notContainsCopy = wordDoesNotContain.copy()

        # Simulate all of the letters being wrong if we guess it
        for char in ans:
            if char not in knownWord and char not in wordContains:
                notContainsCopy.append(char)

        newAnswers = trimAnswers(answers, knownWord, '', wordContains, notContainsCopy)
        newAnswersLen = len(newAnswers)

        if newAnswersLen < leastAnswersLeft:
            bestGuess = ans
            leastAnswersLeft = newAnswersLen

    return bestGuess

def startGame(driver):

    game_app = driver.find_element(By.TAG_NAME, 'game-app')
    board = driver.execute_script("return arguments[0].shadowRoot.getElementById('board')", game_app)
    gameRows = board.find_elements(By.TAG_NAME, 'game-row')

    # All the possible wordle answers
    answers = []
    with open('answers.txt') as f:
        for line in f:
            answers.append(line.strip())

    firstGuess = 'farts'

    # Store the past guesses in a list along with their evaluations
    # Will use the evaluations when trimming answers
    guesses = [[list(firstGuess), ]]

    # Used to store the letters we know are in the correct spot
    knownWord = list('_____')

    wordContains = []
    wordDoesNotContain = []

    # Lets go
    enterWord(driver, firstGuess)

    for turn in range(0, 5):

        eval, knownWord, wordContains, wordDoesNotContain = getRowEvaluation(driver, gameRows[turn], knownWord, wordContains, wordDoesNotContain)
        guesses[turn].insert(1, eval)

        # Wordle solved
        if '_' not in knownWord:
            print('We won. The word was {}'.format(knownWord))
            return

        # Go through the known answers list and remove any wrong ones
        answers = trimAnswers(answers, knownWord, guesses, wordContains, wordDoesNotContain)

        guess = chooseGuess(answers, knownWord, wordContains, wordDoesNotContain)
        guesses.append([list(guess), ])

        print("Guessing word '{}', possible answers left: {}".format(guess, len(answers)))
        enterWord(driver, guess)

    if '_' not in knownWord:
        print('We won. The word was {}'.format(knownWord))
    else:
        print('Failed to find the word.')
    
def testGame(firstGuess, answer, answersCopy):

    # Don't alter the first one if we are doing multiple tests
    answers = answersCopy.copy()

    guess = firstGuess
    guesses = [[list(guess), ]]

    # Used to store the letters we know are in the correct spot
    knownWord = list('_____')

    wordContains = []
    wordDoesNotContain = []

    for turn in range(0, 5):

        eval, knownWord, wordContains, wordDoesNotContain = getTestEvaluation(answer, guess, knownWord, wordContains, wordDoesNotContain)
        guesses[turn].insert(1, eval)

        if '_' not in knownWord:
            print('We won. The word was {}'.format(knownWord))
            return turn

        # Go through the known answers list and remove any wrong ones
        answers = trimAnswers(answers, knownWord, guesses, wordContains, wordDoesNotContain)

        guess = chooseGuess(answers, knownWord, wordContains, wordDoesNotContain)
        guesses.append([list(guess), ])

        print("Guessing word '{}', possible answers left: {}".format(guess, len(answers)))

    eval, knownWord, wordContains, wordDoesNotContain = getTestEvaluation(answer, guess, knownWord, wordContains, wordDoesNotContain)

    if '_' not in knownWord:
        print('We won. The word was {}'.format(knownWord))
        return 5

    print("Failed to find the word {}".format(answer))

    return -1

if __name__ == '__main__':

    testing = True

    if testing:

        answers = []
        with open("answers.txt") as f:
            for line in f:
                answers.append(line.strip())

        #testGame('farts', 'boxer', answers)
        #exit()
        fails = open('fails.txt', 'w')

        # Why, python?
        totalResults = []
        for i in range(0, 6):
            totalResults.append(0)

        wins = 0
        total = 0
        for ans in answers:
            
            results = testGame('farts', ans, answers)

            if results > 0:
                wins += 1
                totalResults[results] += 1
            else:
                fails.write(ans + '\n')

            total += 1

        totalPercent = (wins / total) * 100

        print("Finished. {} wins and {} losses, total percentage: {}%".format(wins, total - wins, round(totalPercent, 2)))
        print("Average guess distribution: {}".format(totalResults))

        fails.close()

    else:

        driver = webdriver.Firefox()
        driver.get('https://www.powerlanguage.co.uk/wordle/')

        time.sleep(3)

        # Hide the popup when opening the site
        driver.find_element(By.TAG_NAME, 'html').click()
        
        time.sleep(1)

        startGame(driver)

        time.sleep(10)
        driver.close()
