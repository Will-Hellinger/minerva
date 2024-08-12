import os
import time
import shutil
import requests
import argparse
import selenium.webdriver

import gui
import driver
import file_manager
import login_manager
import schoology_manager

import assignments.synopsis


def main(config: dict, data_path: str, credentials_path: str, icon_path: str, master_password: str) -> None:
    """
    Main function for the application.

    :param config: Dictionary containing the configuration settings.
    :param data_path: Path to the data folder.
    :param credentials_path: Path to the credentials file.
    :return: None
    """

    if not login_manager.credentials_exist(credentials_path):
        gui.initialization_window(config, credentials_path, icon_path)

    if master_password is not None:
        key: bytes = login_manager.generate_key(master_password)
        username, password = login_manager.load_credentials(key, credentials_path)
    else:
        username, password = gui.login_window(config, credentials_path, icon_path)

    if username is None or password is None:
        print('No credentials provided, exiting...')
        return
    
    if config.get('schoology-url', None) is not None and not config.get('schoology-url', None).endswith('/'):
        config['schoology-url'] = f"{config.get('schoology-url', None)}/"
    
    #This does all the work behind the scenes.

    print('Logging in...')
    session: requests.Session = schoology_manager.login(config.get('schoology-url', None), username, password.strip())

    username, password = None, None # Clear the username and password from memory

    print('Checking for Latin courses...')
    courses = schoology_manager.get_courses(session, config.get('schoology-url', None))
    sections = schoology_manager.find_latin_courses(courses)

    if len(sections) == 0:
        print('No Latin courses found, exiting...')
        return

    print('Injecting cookies...')
    webdriver: selenium.webdriver = driver.get_driver(config.get('browser', 'Chrome').title())

    webdriver.get(config.get('schoology-url', None))

    for cookie in session.cookies:
        webdriver.add_cookie({
            'name': cookie.name,
            'value': cookie.value,
            'path': cookie.path,
            'domain': cookie.domain
        })

    webdriver.get(config.get('LTHSLatin-schoology-url', None))

    time.sleep(5) #Implement proper load detection later

    webdriver.get(config.get('latin-url', None))

    assignment_configs: dict = config.get('assignment-configs', {})

    #synopsis setup
    synopsis_config: dict = assignment_configs.get('synopsis', {})

    cleaned_conjugation_charts_path: str = file_manager.clean_path(synopsis_config.get('conjugation-charts-path', None), data_path)
    cleaned_conjugation_types_chart_path: str = file_manager.clean_path(synopsis_config.get('conjugation-chart-types-path', None), data_path)
    synopsis_charts: dict = assignments.synopsis.generate_charts(cleaned_conjugation_charts_path)
    synopsis_blocks: tuple[str] = tuple(synopsis_config.get('blocks', []))

    while True:
        if not webdriver.service.process:
            print('Webdriver is not running')
            break


if __name__ == '__main__':
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description='Your favorite Latin Client')

    parser.add_argument('-c', '--config', help='Path to the configuration file', type=str)
    parser.add_argument('-d', '--data', help='Path to the data folder', type=str)
    parser.add_argument('-s', '--secrets', help='Path to the credentials file', type=str)
    parser.add_argument('-mp', '--master-password', help='Master Password to unlock', type=str)

    args: argparse.Namespace = parser.parse_args()

    first_launch: bool = False

    data_path: str = f'{file_manager.get_documents_folder()}{os.sep}minerva{os.sep}'
    default_path: str = f'.{os.sep}default{os.sep}'

    if not os.path.exists(data_path):
        first_launch = True
        os.makedirs(data_path)

    icon_path: str = f'{data_path}icon.ico'
    config_path: str = f'{data_path}config.json'
    default_config_path: str = f'{default_path}config.json'
    credentials_path: str = f'{data_path}secrets.enc'

    config: dict | None = file_manager.read_json(default_config_path)

    if os.path.exists(config_path):
        user_config: dict = file_manager.read_json(config_path)
        config.update(user_config)
    else:
        print('No user configuration file found, continuing with default configuration.')
        first_launch = True
    
    if first_launch:
        new_config: dict | None = gui.initialization_window(config, credentials_path)

        if new_config is None:
            print('No configuration provided, exiting...')
            exit(1)

        shutil.copytree(default_path, data_path)

        file_manager.save_json(config_path, new_config)
        config.update(new_config)

    if config is None:
        print('No default configuration file found, continuing with no configuration.')
        config = {}

    if not os.path.exists(icon_path):
        print('Downloading icon...')
    else:
        print('Checking for icon updates...')

    icon_url: str | None = config.get('icon-url', None)

    try:
        if icon_url is None:
            print('No icon URL provided, defaulting to preprogrammed icon.')
            icon = requests.get(f'https://lthslatin.org/favicon.ico')
        else:
            icon = requests.get(icon_url)

        with open(icon_path, 'wb') as file:
            file.write(icon.content)
        
        print('Icon downloaded successfully!')
    except requests.exceptions.ConnectionError:
        print('Unable to download icon, continuing...')
        

    main(config, data_path, credentials_path, icon_path, args.master_password)