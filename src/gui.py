import time
import login_manager
import PySimpleGUI as sg


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


def control_window(config: dict = {}, icon_path: str | None = None) -> None:
    """
    Function to manage the control window.

    :param config: Dictionary containing the configuration settings.
    :return: None
    """

    app_name: str = config.get('app-name', 'minerva')
    theme: str = config.get('theme', None)

    if theme is not None:
        sg.theme(theme)

    layout = [
        [sg.Text(f'Welcome to {app_name}!', font=('Helvetica', 16))],
        [sg.Button('Settings'), sg.Button('Exit')]
    ]

    if icon_path is None:
        window = sg.Window(f'{app_name}', layout)
    else:
        window = sg.Window(f'{app_name}', layout, icon=icon_path)

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED or event == 'Exit':
            break

        if event == 'Settings':
            window.close()
            break

    window.close()

    return None