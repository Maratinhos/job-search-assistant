import os
import uuid
from pathlib import Path

STORAGE_DIR = "storage"


def save_text_to_file(text: str, subfolder: str) -> str:
    """
    Saves text content to a file with a unique name in a specified subfolder
    within the base storage directory.

    Args:
        text: The text content to save.
        subfolder: The name of the subfolder (e.g., 'resumes', 'vacancies').

    Returns:
        The relative path to the newly created file, or None on error.
    """
    try:
        # Create a unique filename
        filename = f"{uuid.uuid4()}.txt"

        # Construct the full path
        directory_path = Path(STORAGE_DIR) / subfolder

        # Create the directory if it doesn't exist
        directory_path.mkdir(parents=True, exist_ok=True)

        file_path = directory_path / filename

        # Write the text to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

        # Return the string representation of the path
        return str(file_path)
    except IOError as e:
        print(f"Error saving file: {e}")
        return None
