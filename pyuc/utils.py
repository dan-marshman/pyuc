import os


def check_path_exists(path, file_type, required_file=False):
    """
    Check that the file exists, or provide an error if it doesn't.

    :param path string: Path to the file.
    :param file_type string: The purpose of the file.
    """

    if not os.path.exists(path):
        print("The file used for ", file_type, "does not exist. The provided path is:")
        print(path)

        if required_file:
            print("This is a required file - exiting.")
            exit()
        else:
            return False
    else:
        return True
