import os


def check_path_exists(path, file_type):
    """
    Check that the file exists, or provide an error if it doesn't.

    :param path string: Path to the file.
    :param file_type string: The purpose of the file.
    """

    if not os.path.exists(path):
        print("The file used for ", file_type, "does not exist. The provided path is:")
        print(path)
        exit()
