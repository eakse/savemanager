import json
from eakse.common import *


clear_terminal()


modpath = "C:\###Games\CataDDA\\bn\current\mods"
basepath = "C:\###Games\CataDDA\\bn\current\data"


def process_list(filelist, key, value):
    result = []
    count = 0
    for filename in filelist:
        print(filename)
        encoding = get_encoding(filename)
        with open(filename, encoding=encoding) as infile:
            current = json.load(infile)
        for item in current:
            try:
                if key in item and item[key] == value:
                    count += 1
                    print(f"\033[F{count:0>8}")
                    result.append(item)
            except Exception as e:
                pass
                # print(f'------------------------------\nError in filename {filename}:\n{e}')
    return result


alljson = get_files_from_path(path=modpath, extension=".json")
alljson.append(get_files_from_path(path=basepath, extension=".json"))


allguns = process_list(alljson, "type", "GUN")


print(len(allguns))
