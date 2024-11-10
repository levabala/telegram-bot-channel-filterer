import os
import doctest


# chatgpt (c)
def run_doctests_in_directory(directory):
    # Traverse all files in the given directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                print(f"Running doctest on {file_path}")
                try:
                    doctest.testfile(file_path, module_relative=False)
                except Exception as e:
                    print(f"Error running doctest on {file_path}: {e}")


if __name__ == "__main__":
    # Replace '.' with the path to your project directory if needed
    run_doctests_in_directory(".")
