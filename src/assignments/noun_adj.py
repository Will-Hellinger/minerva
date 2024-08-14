import time
import selenium.webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def prediction(noun_adj_chart: dict, words: list = None) -> bool:
    """
    Predict if a given list of words forms a valid combination based on available endings.

    :param noun_adj_chart: A dictionary containing noun and adjective endings.
    :param words: A list of words to predict.
    :return: True if a valid combination is predicted, otherwise False.
    """

    if len(words) != 2 or words is None:
        return False
    
    endings: list[str] = []

    for word in words:
        all_endings: list[str] = []

        for end in noun_adj_chart:
            if word.endswith(end):
                all_endings.append(end)

        if len(all_endings) >= 1:
            endings.append(max(all_endings, key=len))
    
    if len(endings) <= 1:
        return False

    if endings[0] in noun_adj_chart.get(endings[1]) or endings[1] in noun_adj_chart.get(endings[0]):
        return True
    
    return False


def solver(driver: selenium.webdriver, noun_adj_chart: dict) -> None:
    """`
    Perform a series of actions, including solving word combinations and managing responses.

    :param driver: The Selenium WebDriver object.
    :param noun_adj_chart: A dictionary containing noun and adjective endings.
    :return: None
    """
    
    nouns: list[str] = []

    for a in range(10):
        nouns.append((driver.find_element(By.NAME, f'input{str(a+1)}').text).split('\n')[0])
    
    for a in range(len(nouns)):
        if 'noun' not in str(driver.title).lower():
            break

        try:
            if a != 0:
                driver.execute_script("arguments[0].scrollIntoView();", driver.find_element(By.XPATH, f'// label[@for="no{a}"]'))
            else:
                driver.find_element(By.TAG_NAME, 'html').send_keys(Keys.HOME)
                driver.execute_script("arguments[0].scrollIntoView();", driver.find_element(By.XPATH, f'// label[@for="no1"]'))
        except:
            print(f'unable to scroll to element {a}')

        if 'noun' not in str(driver.title).lower():
            break

        words: list[str] = nouns[a].split(' ')
        output: bool = prediction(words, noun_adj_chart)

        choice: str = 'no'

        if output == True:
            choice = 'yes'
        
        for b in range(2):
            try:
                driver.find_element(By.XPATH, f'// label[@for="{choice}{a+1}"]').click()
                break
            except:
                print(f'unable to press {choice}{a+1}')
            
            if a == 0:
                driver.find_element(By.TAG_NAME, 'html').click()

    selections: tuple[str] = ('agreeSubmit', 'agreeMore')

    for selection in selections:
        while True:
            if 'noun' not in str(driver.title).lower():
                break

            try:    
                driver.find_element(By.ID, selection).click()
                break
            except:
                print(f'unable to press get {selection}')
                time.sleep(2)

    time.sleep(5)

    response_text: str = str(driver.find_element(By.XPATH, f"// h3[@class='showScore ui-bar ui-bar-c ui-title']").text).split('\n')[0]
    correct_amount: int = int(str(response_text.split(' out of ')[0]).replace('You answered ', ''))

    try:
        print(f'{response_text}')
    except:
        print('unable to get score')