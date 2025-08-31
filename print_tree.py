import os
import sys

# ضبط الترميز للكتابة في Windows
sys.stdout.reconfigure(encoding='utf-8')

def print_tree(startpath, prefix=""):
    items = sorted(os.listdir(startpath))
    for index, item in enumerate(items):
        path = os.path.join(startpath, item)
        connector = "├── " if index < len(items) - 1 else "└── "
        print(prefix + connector + item)
        if os.path.isdir(path):
            extension = "│   " if index < len(items) - 1 else "    "
            print_tree(path, prefix + extension)

project_path = r"D:\BOT\realestate_system"
print_tree(project_path)
