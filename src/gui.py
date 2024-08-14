import time
import PySimpleGUI as sg
import selenium.webdriver
from googletrans import Translator

import file_manager
import login_manager
import lthslatin_manager

import assignments.synopsis
import assignments.noun_adj
import assignments.composition
import assignments.timed_vocabulary


def generate_config_layout(config: dict) -> list[list]:
    """
    Function to generate the layout for the configuration window.

    :param config: Dictionary containing the configuration settings.
    :return: List of lists representing the layout for the configuration window.
    """

    layout: list[list] = [[sg.Text('Configuration Settings', font=('Helvetica', 16))]]
    important_keys = config.get('important-keys', {})

    for key, value in config.items():
        prefs: dict = important_keys.get(key, None)

        match key:
            case 'important-keys':
                continue
            case 'theme':
                if prefs is not None:
                    if not prefs.get('show'):
                        continue
                    
                    if not prefs.get('editable', True):
                        layout.append([sg.Text(f'{key}:'), sg.Combo(sg.theme_list(), default_value=value, key=f'-{key}-', disabled=True)])
                    else:
                        layout.append([sg.Text(f'{key}:'), sg.Combo(sg.theme_list(), default_value=value, key=f'-{key}-'), sg.Text('Restart Required')])
                else:
                    layout.append([sg.Text(f'{key}:'), sg.Combo(sg.theme_list(), default_value=value, key=f'-{key}-'), sg.Text('Restart Required')])
                continue
            case _:
                if prefs is not None:
                    if not prefs.get('show'):
                        continue
                    
                    if not prefs.get('editable', True):
                        layout.append([sg.Text(f'{key}:'), sg.Input(value, key=f'-{key}-', disabled=True)])
                    else:
                        layout.append([sg.Text(f'{key}:'), sg.Input(value, key=f'-{key}-')])
                else:
                    layout.append([sg.Text(f'{key}:'), sg.Input(value, key=f'-{key}-')])
    
    layout.append([sg.Button('Next')])

    return layout


def initialization_window(config: dict = {}, credentials_path: str = None, icon_path: str | None = None) -> dict:
    """
    Function to manage the initialization window.

    :param config: Dictionary containing the configuration settings.
    :param credentials_path: Path to the credentials file.
    :return: Updated configuration settings.
    """

    app_name: str = config.get('app-name', 'minerva')
    theme: str = config.get('theme', None)

    if theme is not None:
        sg.theme(theme)
    
    if credentials_path is None:
        print('No credentials path provided!')
        return config
    
    firstpage = [
        [sg.Text(f'Welcome to {app_name}!', font=('Helvetica', 16))],
        [sg.Text("I've detected that this is your first time using the application!")],
        [sg.Text('Please take a look at the configuration settings on the next page and set your preferences.')],
        [sg.Button('Next')]
    ]

    # Second Layout
    configpage = generate_config_layout(config)

    passwordpage = [
        [sg.Text('In order to maintain the security of your credentials, please enter your credentials below and a master password to lock them.')],
        [sg.Text('Note: The master password cannot be recovered if lost, and will be required every time you start the application.')],
        [sg.Text('Username:', size=(20, 1)), sg.Input(key='-USERNAME-')],
        [sg.Text('Password:', size=(20, 1)), sg.Input(password_char='*', key='-PASSWORD1-')],
        [sg.Text('Confirm Password:', size=(20, 1)), sg.Input(password_char='*', key='-PASSWORD2-')],
        [sg.Text('Master Password:', size=(20, 1)), sg.Input(password_char='*', key='-MASTER-PWD1-')],
        [sg.Text('Confirm Master Password:', size=(20, 1)), sg.Input(password_char='*', key='-MASTER-PWD2-')],
        [sg.Button('Submit')]
    ]

    # Create Window
    if icon_path is None:
        window = sg.Window(f'{app_name} Setup', firstpage, finalize=True)
    else:
        window = sg.Window(f'{app_name} Setup', firstpage, finalize=True, icon=icon_path)

    current_layout = 1

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            return None

        if event == 'Next':
            match current_layout:
                case 1:
                    window.close()
                    window = sg.Window(f'{app_name} Setup', configpage, finalize=True)
                    current_layout += 1
                case 2:
                    for key in config.keys():
                        if values.get(f'-{key}-', None) is None:
                            continue

                        config[key] = values[f'-{key}-']

                    window.close()
                    window = sg.Window(f'{app_name} Setup', passwordpage, finalize=True)
            
        if event == 'Submit':
            username = values['-USERNAME-']
            password1 = values['-PASSWORD1-']
            password2 = values['-PASSWORD2-']
            master_password1 = values['-MASTER-PWD1-']
            master_password2 = values['-MASTER-PWD2-']

            if password1 != password2:
                sg.popup('Passwords do not match!')
                continue

            if master_password1 != master_password2:
                sg.popup('Master Passwords do not match!')
                continue

            key = login_manager.generate_key(master_password1)
            login_manager.save_credentials(username, password1, key, credentials_path)
            sg.popup('Credentials Saved Securely!')

            username, password1, password2, master_password1, master_password2 = None, None, None, None, None # Just to be safe

            break
    
    window.close()

    return config


def login_window(config: dict = {}, credentials_path: str = None, icon_path: str | None = None) -> tuple[str, str]:
    """
    Function to manage the login credentials
    
    :param config: Dictionary containing the configuration settings.
    :param credentials_path: Path to the credentials file.
    :return: Tuple containing the username and password.
    """

    app_name: str = config.get('app-name', 'minerva')
    theme: str = config.get('theme', None)

    if not login_manager.credentials_exist(credentials_path):
        sg.popup('No credentials found! Please run through setup again')
        return None, None

    if theme is not None:
        sg.theme(theme)

    layout_master_password = [
        [sg.Text('Enter Master Password:', size=(20, 1))],
        [sg.Input(password_char='*', key='-MASTER-PWD-')],
        [sg.Button('Submit'), sg.Button('Forgot Password')]
    ]

    if icon_path is None:
        window = sg.Window(f'{app_name} Login Manager', layout_master_password)
    else:
        window = sg.Window(f'{app_name} Login Manager', layout_master_password, icon=icon_path)

    username, password = None, None
    master_password = None

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            break

        if event == 'Submit':
            master_password = str(values['-MASTER-PWD-'])
            key: bytes = login_manager.generate_key(master_password)

            if login_manager.credentials_exist(credentials_path):
                try:
                    username, password = login_manager.load_credentials(key, credentials_path)
                    break
                except Exception as e:
                    sg.popup('Error loading credentials!', e)
            else:
                sg.popup('No credentials found!')
        
        if event == 'Forgot Password':
            sg.popup('Removing credentials...')
            login_manager.delete_credentials(credentials_path)
            window.close()

    window.close()
    
    return username, password


def control_window(webdriver: selenium.webdriver, config: dict, icon_path: str | None, available_modes: list[str], synopsis_conjugation_types: dict | None, synopsis_charts: dict | None, synopsis_blocks: tuple[str] | None, noun_adjective_chart: dict | None, composition_dictionary: dict | None, composition_cache_path: str | None, composition_use_synonyms: bool | None, nltk_working: bool | None, timed_vocab_dict_path: str | None) -> None:
    """
    Function to manage the control window.

    :param webdriver: The Selenium WebDriver object.
    :param config: Dictionary containing the configuration settings.
    :param icon_path: Path to the icon file.
    :param available_modes: List of available modes.
    :param synopsis_conjugation_types: Dictionary containing the synopsis conjugation types.
    :param synopsis_charts: Dictionary containing the synopsis charts.
    :param synopsis_blocks: Tuple containing the synopsis blocks.
    :param noun_adjective_chart: Dictionary containing the noun and adjective endings.
    :param nltk_working: Boolean indicating if the NLTK dependencies are working.
    :param timed_vocab_dict_path: Path to the cleaned timed vocabulary dictionary.
    :return: None
    """

    app_name: str = config.get('app-name', 'minerva')
    theme: str = config.get('theme', None)

    if theme is not None:
        sg.theme(theme)

    user: str | None = lthslatin_manager.get_user(webdriver)
    mode: str | None = None
    assignment: str | None = None

    layout = [
        [sg.Text(f'{app_name}', font=('Helvetica', 16))],
        [sg.Text(f'User: {user}', key='-USER-'), sg.Text(f'Mode: {mode}', key='-MODE-')],
        [sg.Button('Solve'), sg.Checkbox('Continuous', key='-CONTINUOUS-')],
        [sg.Button('Exit')]
    ]

    if icon_path is None:
        window = sg.Window(f'{app_name}', layout)
    else:
        window = sg.Window(f'{app_name}', layout, icon=icon_path)

    run_prediction: bool = True
    translator: Translator | None = None
    use_google_trans: bool = False

    try:
        translation_delay = lthslatin_manager.get_translation_delay()
        max_timed_vocab_delay = config.get('assignment-configs').get('timed-vocabulary').get('max-googletrans-delay', 3)
        use_google_trans = config.get('assignment-configs').get('timed-vocabulary').get('use-googletrans', False)

        if translation_delay is None or translation_delay > max_timed_vocab_delay:
            run_prediction = False
            print('Translation service not working or too slow, disabling prediction...')
        else:
            translator = Translator()
    except:
        run_prediction = False
    
    if use_google_trans is False:
        run_prediction = False

    while True:
        event, values = window.read(timeout=100)
        
        if event == sg.WINDOW_CLOSED or event == 'Exit':
            window.close()
            break

        mode, assignment = lthslatin_manager.find_mode(webdriver, mode, available_modes, config.get('user', None))

        window['-MODE-'].update(f'Mode: {mode}')
        
        if event == 'Solve' or values['-CONTINUOUS-']:
            try:
                match mode:
                    case 'synopsis':
                        if synopsis_conjugation_types is None or synopsis_charts is None or synopsis_blocks is None:
                            raise Exception('Synopsis data not loaded!')
                        
                        assignments.synopsis.solve(webdriver, synopsis_blocks, synopsis_charts, synopsis_conjugation_types)
                    case 'noun-adj':
                        if noun_adjective_chart is None:
                            raise Exception('Noun-Adj data not loaded!')
                        
                        assignments.noun_adj.solver(webdriver, noun_adjective_chart)
                    case 'composition':
                        if composition_dictionary is None or composition_cache_path is None or composition_use_synonyms is None:
                            raise Exception('Composition data not loaded!')
                        
                        use_google_trans = config.get('assignment-configs').get('composition').get('use-googletrans', False)
                        if use_google_trans is False:
                            run_prediction = False
                        
                        assignments.composition.solve(webdriver, run_prediction, translator, composition_dictionary, composition_use_synonyms, composition_cache_path)
                    case 'timed vocabulary':
                        if nltk_working is None or nltk_working is False or timed_vocab_dict_path is None:
                            raise Exception('Timed Vocabulary data not loaded!')
                        
                        use_google_trans = config.get('assignment-configs').get('timed-vocabulary').get('use-googletrans', False)
                        if use_google_trans is False:
                            run_prediction = False
                        
                        assignments.timed_vocabulary.solver(webdriver, timed_vocab_dict_path, run_prediction, translator)
            except Exception as error:
                print(f'Error: {error}')

    return None