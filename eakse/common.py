import inspect
import os
import subprocess, platform
import cchardet as chardet


def clear_terminal():
    if platform.system()=="Windows":
        subprocess.Popen("cls", shell=True).communicate() #I like to use this instead of subprocess.call since for multi-word commands you can just type it out, granted this is just cls and subprocess.call should work fine 
    else: #Linux and Mac
        print("\033c", end="")


def dump_args(func):
    """
    Decorator to print function call details.
    This includes parameters names and effective values.
    """

    def wrapper(*args, **kwargs):
        # if 'SHOW_DEBUG' not in settings or settings['SHOW_DEBUG']:
        func_args = inspect.signature(func).bind(*args, **kwargs).arguments
        func_args_str = ", ".join(map("{0[0]} = {0[1]!r}".format, func_args.items()))
        print(f"{func.__module__}.{func.__qualname__} ( {func_args_str} )")
        return func(*args, **kwargs)

    return wrapper


@dump_args
def get_files_from_path(path: str='.', extension: str=None) -> list:
    """Traverse a path including subfolders to generate a list of filenames

    Args:
        path (str, optional): Path to start in. Defaults to '.'.
        extension (str, optional): File extension. (Simply does str.endswith()). Defaults to None.

    Returns:
        list: List of matching filenames.
    """
    # see the answer on the link below for a ridiculously 
    # complete answer for this. I tend to use this one.
    # note that it also goes into subdirs of the path
    # https://stackoverflow.com/a/41447012/9267296
    result = []
    for subdir, dirs, files in os.walk(path):
        for filename in files:
            filepath = subdir + os.sep + filename
            if extension == None:
                result.append(filepath)
            elif filename.lower().endswith(extension.lower()):
                result.append(filepath)
    return result


def get_encoding(filename):
    with open(filename, "rb") as infile:
        msg = infile.read()
    result = chardet.detect(msg)
    # print(result)
    return result['encoding']


