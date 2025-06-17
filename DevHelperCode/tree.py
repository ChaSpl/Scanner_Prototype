import os

def print_tree(root, prefix=""):
    for item in os.listdir(root):
        path = os.path.join(root, item)
        print(f"{prefix}{item}")
        if os.path.isdir(path):
            print_tree(path, prefix + "│   ")

print_tree(".")
