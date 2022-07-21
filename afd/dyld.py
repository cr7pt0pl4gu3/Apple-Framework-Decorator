from binaryninja import *
import ssdeep
import ast
from pathlib import Path


def dyld_ssdeep(bv):
    directory = get_directory_name_input("Choose extracted dyld shared cache folder")
    path_to_hash = {}
    for path in Path(directory).rglob('*'):
        try:
            hash_ = ssdeep.hash(path.read_bytes())
            path_to_hash[path.name] = hash_
        except IsADirectoryError:
            pass
    file = get_save_filename_input("File to save hashes to:", "txt", "hashes.txt")
    with open(file, "w") as f:
        f.write(str(path_to_hash))


def compare_ssdeep_hashes(bv):
    f_name_one = get_open_filename_input("First hashes file:", "*.txt")
    with open(f_name_one, "r") as f:
        s = f.read()
        path_to_hash_one = ast.literal_eval(s)
    f_name_two = get_open_filename_input("Second hashes file:", "*.txt")
    with open(f_name_two, "r") as f:
        s = f.read()
        path_to_hash_two = ast.literal_eval(s)
    path_to_hash_one_set = set(path_to_hash_one)
    path_to_hash_two_set = set(path_to_hash_two)
    for name in path_to_hash_one_set.intersection(path_to_hash_two_set):
        res = ssdeep.compare(path_to_hash_one[name], path_to_hash_two[name])
        if res != 100:
            print(f"{name} similarity = {res}%")
    for name in path_to_hash_one_set.difference(path_to_hash_two_set):
        print(f"{name} is unique for {f_name_one.split('/')[1]}")
    for name in path_to_hash_two_set.difference(path_to_hash_one_set):
        print(f"{name} is unique for {f_name_two.split('/')[1]}")
