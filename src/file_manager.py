import os
import json
import platform
from pathlib import Path


def get_documents_folder() -> Path:
    """
    Returns the path to the user's Documents folder.

    :return: Path to the user's Documents folder.
    """

    system: str = platform.system()
    documents_path: Path = Path()

    match system:
        case 'Windows':
            # Windows: Use the 'USERPROFILE' environment variable
            documents_path = Path(os.getenv('USERPROFILE', ''), 'Documents')
        
        case 'Darwin':  # macOS
            # macOS: Use the 'HOME' environment variable
            documents_path = Path(os.getenv('HOME', ''), 'Documents')
        
        case 'Linux':
            # Linux: Use the 'HOME' environment variable
            documents_path = Path(os.getenv('HOME', ''), 'Documents')
        
        case _:
            raise NotImplementedError(f"Unsupported operating system: {system}")
    
    return documents_path


def read_json(file_path: Path) -> dict | None:
    """
    Reads a JSON file and returns its contents as a dictionary.

    :param file_path: Path to the JSON file.
    :return: Dictionary containing the JSON file's contents.
    """

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    
    return None


def save_json(file_path: Path, data: dict) -> None:
    """
    Saves a dictionary to a JSON file.

    :param file_path: Path to the JSON file.
    :param data: Dictionary to save to the JSON file.
    """

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)