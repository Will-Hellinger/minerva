import os
import base64
from cryptography.fernet import Fernet


def generate_key(master_password: str) -> bytes:
    return base64.urlsafe_b64encode(master_password.encode().ljust(32))


def encrypt_data(data: str, key: bytes) -> bytes:
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data


def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data).decode()
    return decrypted_data


def save_credentials(username: str, password: str, key: bytes, filepath: str = 'secrets.enc') -> None:
    encrypted_username = encrypt_data(username, key)
    encrypted_password = encrypt_data(password, key)

    if not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))

    with open(filepath, 'wb') as file:
        file.write(encrypted_username + b'\n' + encrypted_password)


def load_credentials(key: bytes, filepath: str = 'secrets.enc') -> tuple[str, str]:
    with open(filepath, 'rb') as file:
        encrypted_username, encrypted_password = file.read().splitlines()
        username = decrypt_data(encrypted_username, key)
        password = decrypt_data(encrypted_password, key)
    return username, password


def credentials_exist(filepath: str = 'secrets.enc') -> bool:
    return os.path.exists(filepath)