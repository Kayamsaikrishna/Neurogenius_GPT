import os

def print_directory_structure(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Calculate the depth level for indentation
        level = dirpath.replace(root_dir, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(dirpath)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in filenames:
            print(f"{subindent}{f}")

# Fixed folder path (update the string as needed)
folder = r"C:\Users\kayam_drhfn9o\neurogenius\NeuroGenius_App"
print(f"Directory structure for: {folder}\n")
print_directory_structure(folder)
