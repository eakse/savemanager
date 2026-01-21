from eakse.common import get_files_from_path


path = "/home/eakse/Applications/cataclysm-tlg-1.0/"

normals = get_files_from_path(path, extension="normal.png")
print (normals)

for file in normals:
    print(file) 