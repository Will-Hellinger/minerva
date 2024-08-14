import re
import os
import glob
import json
import pyinflect
import unicodedata
import selenium.webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def generate_charts(conjugation_charts_path : str | None) -> dict:
    """
    Generate the Latin and English conjugation charts from the JSON files.

    :param conjugation_charts_path: Path to the directory containing the JSON files.
    :return: A dictionary containing the Latin and English conjugation charts.
    """

    if conjugation_charts_path is None:
        raise ValueError("The path to the conjugation charts is required.")
    
    print('generating synposis charts')

    if not conjugation_charts_path.endswith(os.sep):
        conjugation_charts_path += os.sep

    folders : dict = {
        "english-conjugation-charts" : "english",
        "latin-conjugation-charts" : "latin"
    }

    conjugation_charts: dict = {
        'latin': {},
        'english': {}
    }

    for folder in folders:
        file_names: list[str] = []
        files: list = glob.glob(f"{conjugation_charts_path}{folder}{os.sep}*.json")
        
        for file in files:
            file_name: str = os.path.basename(file).replace('.json', '')
            file_names.append(file_name)

            with open(file, 'r') as f:
                data: dict = json.load(f)

                conjugation_charts[folders.get(folder)][file_name] = data
        
        print(f'{folders.get(folder)} charts: {file_names}')

    print('synopsis charts generated')

    return conjugation_charts


def strip_accents(text: str) -> str:
    """
    Remove accents from a given text.

    :param text: The text to remove accents from.
    :return: The text without accents as a string.
    """

    return str(''.join(char for char in unicodedata.normalize('NFKD', text) if unicodedata.category(char) != 'Mn')).lower()


def showHiddenDropdowns(driver: selenium.webdriver) -> None:
    """
    Show hidden dropdown elements on the web page.

    :param driver: The Selenium WebDriver object.
    :return: None
    """

    nontoucheddropDowns = driver.find_elements(By.XPATH, f"// div[@class='ui-collapsible-content ui-body-inherit ui-collapsible-content-collapsed']")
    toucheddropDowns = driver.find_elements(By.XPATH, f"// div[@class='ui-collapsible-heading ui-collapsible-content-collapsed']")
    dropDowns = nontoucheddropDowns + toucheddropDowns

    for dropdown in dropDowns:
        newClass = 'ui-collapsible-heading'
        driver.execute_script(f"arguments[0].setAttribute('class','{newClass}')", dropdown)


def hideShownDropdowns(driver: selenium.webdriver) -> None:
    """
    Hide shown dropdown elements on the web page.

    :param driver: The Selenium WebDriver object.
    :return: None
    """

    toucheddropDowns = driver.find_elements(By.XPATH, f"// div[@class='ui-collapsible-content ui-body-inherit']")
    nontoucheddropDowns = driver.find_elements(By.XPATH, f"// div[@class='ui-collapsible-heading']")
    dropDowns = nontoucheddropDowns + toucheddropDowns

    for dropdown in dropDowns:
        newClass = 'ui-collapsible-heading ui-collapsible-content-collapsed'
        driver.execute_script(f"arguments[0].setAttribute('class','{newClass}')", dropdown)


def find_word(element_list: list) -> str:
    """
    Find the first non-empty text element in a list of web page elements.

    :param element_list: A list of web page elements.
    :return: The text content of the first non-empty element in the list, or an empty string if none is found.
    """

    for element in element_list:
        if str(element.text) != '':
            return str(element.text)

    return ''


def find_details(driver: selenium.webdriver, blocks: tuple, conjugation_types: dict) -> dict:
    """
    Find and extract details about Latin words and their conjugations on a web page.

    :param driver: The Selenium WebDriver object.
    :param blocks: Tuple containing the block names.
    :param conjugation_chart: Dictionary containing the Latin conjugation chart.
    :return: A dictionary containing details about Latin and English words, conjugation chart, and tense.
    """

    conjugation_keys: list[str] = list(conjugation_types.keys())
    conjugation_values: list[list[str]] = list(conjugation_types.values())

    #Finds latin conjugation type
    chart: str = 'first' # temp
    chart_backup: list[int] = []
    chart_found: bool = False

    latin_words: list[str] = []

    for block in blocks:
        try:
            latin_words.append(find_word(driver.find_elements(By.XPATH, f"// span[@class='ui-body ui-body-{block} latin']")))
        except:
            latin_words.append(f'unable to get word {block}')

    for a in range(len(conjugation_values)):
        temp_chart_found: bool = True
        count: int = 0

        for b in range(len(conjugation_values[a])):
            if latin_words[b].endswith(conjugation_values[a][b]):
                count += 1
            elif not latin_words[b].endswith(conjugation_values[a][b]):
                temp_chart_found = False

        if temp_chart_found == True:
            chart = conjugation_keys[a]
            chart_found = True

        chart_backup.append(count)
    
    if not chart_found:
        chart = conjugation_keys[chart_backup.index(max(chart_backup))] #this is a fallback in case it cant find the chart regularly

    english_info: list[str] = find_word(driver.find_elements(By.XPATH, f"// li[@class='ui-block-e']")).split(' |')

    if len(english_info) == 1:
        english_word: str = english_info[0]
        tense: str | None = None
    else:
        english_word: str = english_info[0]
        tense: str | None = english_info[1]

    if tense is not None and tense.startswith(' '):
        tense = tense[1:]

    english_words: dict = {
                    "VB": english_word,                                         #VB - Verb, Base Form
                    "VBG" : pyinflect.getInflection(english_word, 'VBG')[0],    #VBD - Verb, Past Tense
                    "VBN" : pyinflect.getInflection(english_word, 'VBN')[0],    #VBG - Verb, Gerund or Present Participle
                    "VBZ" : pyinflect.getInflection(english_word, 'VBZ')[0],    #VBN - Verb, Past Participle
                    "VBD" : pyinflect.getInflection(english_word, 'VBD')[0]     #VBZ - Verb, 3rd Person Singular Present
                }

    output: dict = {
            "chart" : chart,
            "latin words" : latin_words,
            "english words" : english_words,
            "tense" : tense
            }

    return output


def solve(driver: selenium.webdriver, blocks: tuple, charts: dict, conjugation_types: dict) -> None:
    """
    Solve the Latin conjugation problem.

    :param driver: The Selenium WebDriver object.
    :param blocks: Tuple containing the block names.
    :param charts: Dictionary containing the Latin and English conjugation charts.
    :return: None
    """

    hideShownDropdowns(driver)
    hideShownDropdowns(driver)
    
    current_mode_element = driver.find_element(By.XPATH, f"// div[@class='ui-page ui-page-theme-a ui-page-footer-fixed ui-page-active']")
    page_data: str = find_word(current_mode_element.find_elements(By.XPATH, f"// div[@class='ui-grid-a ui-responsive']")).replace('\nclick to expand contents', '')

    page_inputs: list[str] = []
    temp_input = current_mode_element.find_elements(By.TAG_NAME, f"input")

    for input in temp_input:
        page_inputs.append(str(input.get_attribute('id')))

    current_mode = page_data.split('\n')[0]
    details = find_details(driver, blocks, conjugation_types)

    if details.get('tense') is None:
        print('No tense found, skipping...')
        return None

    tense_cleaned: str = str(details.get("tense")).replace('1st ', 'first-').replace('2nd ', 'second-').replace('3rd ', 'third-')

    latin_dict: dict = charts.get('latin').get(details.get('chart'))

    print(charts.get('english'))
    print(tense_cleaned)

    english_dict: dict = charts.get('english').get(tense_cleaned)

    if current_mode == '' and 'storeScore' in page_data:
        return None
    
    if current_mode == 'PRESENT IMPERATIVE ACTIVE' or current_mode == 'PRESENT IMPERATIVE PASSIVE':
        current_mode = 'IMPERATIVES'

    page_data = str(page_data.replace(f'{current_mode}\n', ''))
    page_data = str(page_data.replace(f'future perfect', 'future-perfect'))
    page_data = page_data.split('\n')

    if current_mode == 'SUBJUNCTIVE':
        current_mode = 'SUBJUNCTIVES'

    latin_inputs: dict = {}
    english_inputs: dict = {}

    if current_mode != 'IMPERATIVES':
        mode: str | None = None

        for item in page_data:
            if item.upper() in ['ACTIVE', 'PASSIVE']:
                mode = item.upper()
            else:
                latin_inputs[f'{mode} {item.upper()}'] = None
                
                if current_mode != 'SUBJUNCTIVES':
                    english_inputs[f'{mode} {item.upper()}'] = None
    else:
        latin_inputs = {
                    "ACTIVE SINGULAR" : None,
                    "ACTIVE PLURAL" : None,
                    "PASSIVE SINGULAR" : None,
                    "PASSIVE PLURAL" : None
                    }
        
        english_inputs = {
                        "ACTIVE" : None,
                        "PASSIVE" : None
                        }
        #none of the temp values are required, just helps to visualize where the data will be sorted to

    temp_latin_inputs: list = []
    temp_english_inputs: list = []

    for i in range(len(page_inputs)):
        if 'english' not in driver.find_element(By.XPATH, f"// input[@id='{page_inputs[i]}']").get_attribute('class'):
            temp_latin_inputs.append(page_inputs[i])
        else:
            temp_english_inputs.append(page_inputs[i])

    latin_inputs_keys = list(latin_inputs.keys())
    english_inputs_keys = list(english_inputs.keys())

    for i in range(len(latin_inputs_keys)):
        latin_inputs[latin_inputs_keys[i]] = temp_latin_inputs[i]

    for i in range(len(english_inputs_keys)):
        english_inputs[english_inputs_keys[i]] = temp_english_inputs[i]

    hideShownDropdowns(driver)
    showHiddenDropdowns(driver)

    for item in latin_inputs:
        latin_input = driver.find_element(By.XPATH, f"// input[@id='{latin_inputs[item]}']")
        driver.execute_script("arguments[0].scrollIntoView();", latin_input)

        activeness: str = str(item).split(' ')[0]
        tense: str = str(item).split(' ')[1]

        data_theme: int = blocks.index(latin_input.get_attribute('data-theme'))

        word: str = details.get('latin words')[data_theme]
        word_ending: str = conjugation_types.get(details.get('chart'))[data_theme]

        new_ending = latin_dict.get(current_mode.upper()[:-1]).get(activeness).get(tense)

        if current_mode in ['INDICATIVES', 'SUBJUNCTIVES']:
            new_ending = new_ending[details.get('tense')]

        ignore_words: tuple = ('dic', 'dac', 'fic', 'fuc') #little rhyme lol
        endless_word: str = re.sub(f'{strip_accents(word_ending)}$', '', strip_accents(word))

        if new_ending == "" and endless_word not in ignore_words:
            new_ending = word_ending[0]

        answer: str = re.sub(f'{strip_accents(word_ending)}$', new_ending, strip_accents(word))

        if 'rgb(255, 0, 0)' in str(latin_input.get_attribute('style')):
            latin_input.clear()

        if 'rgb(0, 128, 0)' not in str(latin_input.get_attribute('style')):
            latin_input.send_keys(answer)
            latin_input.send_keys(Keys.RETURN)
    
    hideShownDropdowns(driver)
    showHiddenDropdowns(driver)

    for item in english_inputs:
        english_input = driver.find_element(By.XPATH, f"// input[@id='{english_inputs[item]}']")
        driver.execute_script("arguments[0].scrollIntoView();", english_input)

        activeness: str = str(item).split(' ')[0]

        answer: str = english_dict.get(current_mode.upper()[:-1]).get(activeness)

        if current_mode.upper() != 'IMPERATIVES':
            tense = str(item).split(' ')[1]
            answer = answer[tense]
        
        verbs: dict = details.get('english words')
        replacement_verb: tuple = ('*VB*', '*VBG*', '*VBN*', '*VBZ*', '*VBD*')

        for verb in replacement_verb:
            answer = answer.replace(verb, verbs.get(verb.replace('*', '')))

        if 'rgb(255, 0, 0)' in str(english_input.get_attribute('style')):
            english_input.clear()

        if 'rgb(0, 128, 0)' not in str(english_input.get_attribute('style')):
            english_input.send_keys(answer)
            english_input.send_keys(Keys.RETURN)
