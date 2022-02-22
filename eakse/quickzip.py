import os
import subprocess

path_7zip = r"C:/Program Files/7-Zip/7z.exe"
path_working = r"C:/###VS Projects/###TMP"
outfile_name = "compressed.zip"
os.chdir(path_working)

def zipthis()
ret = subprocess.check_output([path_7zip, "a", "-tzip", outfile_name])