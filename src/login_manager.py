import os
import base64
import argparse
import cryptography.fernet


def generate_key(master_password: str) -> bytes:
    """
    Generates a key from the master password.

    :param master_password: Master password to generate the key.
    :return: Key generated from the master password.
    """

    return base64.urlsafe_b64encode(master_password.encode().ljust(32))


def encrypt_data(data: str, key: bytes) -> bytes:
    """
    Encrypts the data using the key.

    :param data: Data to encrypt.
    :param key: Key to use for encryption.
    :return: Encrypted data.
    """

    fernet = cryptography.fernet.Fernet(key)
    encrypted_data = fernet.encrypt(data.encode())

    return encrypted_data


def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
    """
    Decrypts the data using the key.

    :param encrypted_data: Encrypted data to decrypt.
    :param key: Key to use for decryption.
    :return: Decrypted data.
    """

    fernet = cryptography.fernet.Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data).decode()
    return decrypted_data


def save_credentials(username: str, password: str, key: bytes, filepath: str = 'secrets.enc') -> None:
    """
    Saves the credentials to a file.

    :param username: Username to save.
    :param password: Password to save.
    :param key: Key to use for encryption.
    :param filepath: Path to save the credentials.
    :return: None
    """

    encrypted_username = encrypt_data(username, key)
    encrypted_password = encrypt_data(password, key)

    if not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))

    with open(filepath, 'wb') as file:
        file.write(encrypted_username + b'\n' + encrypted_password)


def load_credentials(key: bytes, filepath: str = 'secrets.enc') -> tuple[str, str]:
    """
    Loads the credentials from a file.

    :param key: Key to use for decryption.
    :param filepath: Path to load the credentials.
    :return: Tuple containing the username and password.
    """

    with open(filepath, 'rb') as file:
        encrypted_username, encrypted_password = file.read().splitlines()
        username = decrypt_data(encrypted_username, key)
        password = decrypt_data(encrypted_password, key)

    return username, password


def credentials_exist(filepath: str = 'secrets.enc') -> bool:
    """
    Checks if the credentials file exists.

    :param filepath: Path to the credentials file.
    :return: True if the file exists, False otherwise.
    """

    return os.path.exists(filepath)


def delete_credentials(filepath: str = 'secrets.enc') -> None:
    """
    Deletes the credentials file.

    :param filepath: Path to the credentials file.
    :return: None
    """

    if os.path.exists(filepath):
        os.remove(filepath)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Your favorite Latin Client's Login Manager")

    parser.add_argument('-u', '--username', help='Username for the application', type=str)
    parser.add_argument('-p', '--password', help='Password for the application', type=str)
    parser.add_argument('-m', '--master', help='Master Password for the application', type=str)
    parser.add_argument('-s', '--save', help='Save the credentials', action='store_true')

    args = parser.parse_args()

    if args.username is None and args.password is None and args.master is None:
        print('Username, password, and master password are required.')
        exit(1)

    key = generate_key(args.master)

    if args.save:
        save_credentials(args.username, args.password, key, f'.{os.sep}secrets.enc')
        print('Credentials saved successfully!')
    else:
        try:
            username, password = load_credentials(key)
            print(f'Username: {username}\nPassword: {password}')
        except cryptography.fernet.InvalidToken:
            print('Invalid master password.')