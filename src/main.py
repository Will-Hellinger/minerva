import os
import gui
import argparse
import file_manager


def main(config: dict, data_path, credentials_path) -> None:
    username, password = gui.login_window(config, credentials_path)

    if username is None or password is None:
        print('No credentials provided, exiting...')
        return


if __name__ == '__main__':
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description='Your favorite Latin Client')

    parser.add_argument('-c', '--config', help='Path to the configuration file', type=str)
    parser.add_argument('-d', '--data', help='Path to the data folder', type=str)
    parser.add_argument('-s', '--secrets', help='Path to the credentials file', type=str)
    parser.add_argument('-u', '--username', help='Username for the application', type=str)
    parser.add_argument('-p', '--password', help='Password for the application', type=str)

    args: argparse.Namespace = parser.parse_args()

    config_path: str = f'{file_manager.get_documents_folder()}{os.sep}minerva{os.sep}config.json'
    default_config_path: str = f'.{os.sep}default{os.sep}config.json'
    data_path: str = f'{file_manager.get_documents_folder()}{os.sep}minerva'
    credentials_path: str = f'{data_path}{os.sep}secrets.enc'

    default_config: dict | None = file_manager.read_json(default_config_path)

    if os.path.exists(config_path):
        user_config: dict = file_manager.read_json(config_path)
        default_config.update(user_config)
    else:
        print('No user configuration file found, continuing with default configuration.')
        new_config: dict = gui.initialization_window(default_config, credentials_path)
        file_manager.save_json(config_path, new_config)
        default_config.update(new_config)

    if default_config is None:
        print('No default configuration file found, continuing with no configuration.')
        default_config = {}

    main(default_config, data_path, credentials_path)