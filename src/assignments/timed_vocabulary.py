import os
import time
import json
import nltk
import hashlib
import selenium.webdriver
from nltk.corpus import wordnet
from googletrans import Translator
from selenium.webdriver.common.by import By


def encode_file_name(file_name: str) -> str:
    """
    Encode a file name using SHA-256.

    :param file_name: The file name to encode.
    :return: The encoded file name.
    """

    return hashlib.md5(file_name.encode()).hexdigest()


def save_file(file: bytes, data: dict) -> None:
    """
    Save data to a file.

    :param file: The file object.
    :param data: The data to save as a dictionary.
    :return: None
    """

    file.seek(0)
    json.dump(data, file, indent=4)
    file.truncate()


def antonym_extractor(phrase: str) -> list[str]:
    """
    Extract antonyms for a given phrase using NLTK WordNet.

    :param phrase: The phrase for which to find antonyms.
    :return: A list of antonyms as strings.
    """

    antonyms: list[str] = []
    
    for syn in wordnet.synsets(phrase):
        for l in syn.lemmas():
            if l.antonyms():
                antonyms.append(l.antonyms()[0].name())
    
    return antonyms


def synonym_extractor(phrase: str) -> list[str]:
    """
    Extract synonyms for a given phrase using NLTK WordNet.

    :param phrase: The phrase for which to find synonyms.
    :return: A list of synonyms as strings.
    """

    synonyms: list[str] = []

    for syn in wordnet.synsets(phrase):
        for l in syn.lemmas():
            synonyms.append(l.name())

    return synonyms


def check_true(driver: selenium.webdriver) -> bool:
    """
    Check if the current question is marked as true (correct).

    :param driver: The Selenium WebDriver object.
    :return: True if the question is marked as true, False if marked as false, or None if the question has expired or
             has an invalid security label.
    """

    ui_title = driver.find_element(By.XPATH, f"// h3[@class='showScore ui-title']")

    if 'freak' in str(ui_title.text).lower():
        return True
    
    if 'This question has expired due to inactivity or it has an invalid security label.' == str(ui_title.text):
        return None
    
    response: str = str(ui_title.text).split('\n')[1]
    score: int = int(str(driver.find_element(By.XPATH, f"// p[@id='laststreak']").text).split(': ')[1])

    if (response.endswith((str(score + 1) + '.')) and 'current streak is' in response.lower()):
        return True
    else:
        return False


def check_timout(driver: selenium.webdriver, word: str, definition: str, data: dict) -> bool:
    """
    Check if a question has timed out or if its definition matches the expected one.

    :param driver: The Selenium WebDriver object.
    :param word: The word associated with the question.
    :param definition: The expected definition of the word.
    :param data: A dictionary containing definitions and their correctness status.
    :return: True if the question has timed out or if its definition does not match the expected one, False otherwise.
    """

    ui_title = driver.find_element(By.XPATH, f"// h3[@class='showScore ui-title']")

    if word in str(ui_title.text) and definition in str(ui_title.text):
        if 'not' in str(ui_title.text) and data.get(definition) == False:
            return True
        elif 'not' not in str(ui_title.text) and data.get(definition) == True:
            return True
        else:
            return False
    else:
        return True


def wait_reload(driver: selenium.webdriver, word1: str, word2: str, vocab_element: str, definition_element: str) -> None:
    """
    Wait for the page to reload with new words.

    :param word1: The first word to wait for.
    :param word2: The second word to wait for.
    :param vocab_element: The ID of the vocabulary element.
    :param definition_element: The ID of the definition element.
    :return: None
    """

    while True:
        if word1 == str(driver.find_element(By.ID, vocab_element).text).split('\n')[0] and word2 == str(driver.find_element(By.ID, definition_element).text):
            time.sleep(.5)
        else:
            time.sleep(1)
            break


def solver(driver: selenium.webdriver, data_path: str, run_prediction: bool, translator: Translator | None) -> None:
    """
    Automatically solve timed morphology questions on a web page.

    :param driver: The Selenium WebDriver object.
    :param data_path: The path to the data folder.
    :param run_prediction: Whether to run prediction.
    :param translator: The Google Translate API object.
    :return: None
    """

    vocab_element: str = 'timedVocab_lemma'
    definition_element: str = 'timedVocab_def'
    false_element: str = 'timed_vocab_answer_false'
    true_element: str = 'timed_vocab_answer_true'
    timer_element: str = 'timed_vocab_timer'

    word: str = str(driver.find_element(By.XPATH, f"// p[@id='{vocab_element}']").text).split('\n')[0]
    definition: str = str(driver.find_element(By.XPATH, f"// p[@id='{definition_element}']").text)
    predicted_guess: bool | None = None

    file_name: str = encode_file_name(str(word))

    if not data_path.endswith(os.sep):
        data_path += os.sep
    
    file_path: str = f'{data_path}{file_name}.json'

    if not os.path.exists(file_path):
        print(f'{word} not found, creating entry.', end='\r')
        with open(file_path, 'w') as temp_file:
            temp_file.write('{\n}')
    
    if translator is None:
        run_prediction = False
    
    with open(file_path, encoding='utf-8', mode='r+') as file:
        data = json.load(file)
        items = list(data.keys())

        if definition in items:
            print('Found in dictionary: ...', end='\r')

            if data[definition] == True:
                driver.find_element(By.XPATH, f"// label[@for='{true_element}']").click()
            elif data[definition] == False:
                driver.find_element(By.XPATH, f"// label[@for='{false_element}']").click()
            wait_reload(driver, word, definition, vocab_element, definition_element)

            if check_true(driver) == True:
                print(f'Found in dictionary: {word} - {definition} - {data[definition]}: Correct')
            elif check_true(driver) == False and check_timout(driver, word, definition, data) == True:
                print(f'Assuming timeout on word {word}')
            elif check_true(driver) == False and check_timout(driver, word, definition, data) == False:
                print(f'Found in dictionary: {word} - {definition} - {data[definition]}: Incorrect, switching now...')
                data[definition] = not data[definition]
                save_file(file, data)
            elif check_true(driver) == None:
                print('Inactivity or invalid security label')
                
        elif definition not in items:
            print(f'no entry for {definition} within {word}', end='\r')

            if run_prediction == True:
                translated_word: str = (translator.translate(word, src='la', dest='en').text)
                translated_word_synonyms: list[str] = synonym_extractor(translated_word)
                #just to make sure it's added
                translated_word_synonyms.append(translated_word)
                translated_word_antonyms = antonym_extractor(translated_word)

                data_antonyms: list[list[str]] = []
                data_synonyms: list[list[str]] = []

                for item in data:
                    if data[item] == False:
                        data_antonyms = antonym_extractor(item)
                        data_antonyms.append(item)
                    elif data[item] == True:
                        data_synonyms = synonym_extractor(item)
                        data_synonyms.append(item)
                    
                if definition in translated_word_synonyms or definition in data_synonyms:
                    predicted_guess = True
                elif definition in translated_word_antonyms or definition in data_antonyms:
                    predicted_guess = False
            
            if predicted_guess == True:
                driver.find_element(By.XPATH, f"// label[@for='{true_element}']").click()
            else:
                driver.find_element(By.XPATH, f"// label[@for='{false_element}']").click()

            wait_reload(driver, word, definition, vocab_element, definition_element)

            if check_true(driver) == True and predicted_guess != None:
                data[definition] = predicted_guess
                print(f'Predicted Guess - {predicted_guess}: {word} - {definition}: Correct')
            elif check_true(driver) == True and predicted_guess == None:
                data[definition] = False
                print(f'Guess - False: {word} - {definition}: Correct')
            elif check_true(driver) == False and predicted_guess != None:
                data[definition] = not predicted_guess
                print(f'Predicted Guess - {predicted_guess}: {word} - {definition}: Incorrect')
            elif check_true(driver) == False and predicted_guess == None:
                data[definition] = True
                print(f'Guess - False: {word} - {definition}: Inorrect')
            elif check_true(driver) == None:
                print('Inactivity or invalid security label')

            save_file(file, data)