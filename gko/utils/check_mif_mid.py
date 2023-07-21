import os
import logging
import pathlib
import subprocess
import shutil


path = os.environ['PATH']
new_dir = 'C:\\OSGeo4W64\\bin'
os.environ['PATH'] = f'{new_dir};{path}'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)
logger.addHandler(_ch)

directory = r'D:\Мусорка\Графика\zips'
out_directory = r'D:\Мусорка\Графика\error'
def rename(file: pathlib.Path, name: str) -> str:
    return os.path.join(str(file.parent), f"{name}{file.suffix}")

# Ожидаем, что в папке будут только два файла mif и mid
for filepath in pathlib.Path(directory).glob('**/*.mif'):
    parent = filepath.parent

    for file in parent.glob('*'):
        os.rename(file, rename(file, 'input'))

    # Define the command to execute in the command prompt
    command = f"C:\\OSGeo4W64\\bin\\ogr2ogr.exe -sql \"SELECT * FROM input\" -dialect sqlite -f \"ESRI Shapefile\" d:\\null {str(rename(filepath, 'input'))}"

    try:
        output, error  = subprocess.Popen(
            command, universal_newlines=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(timeout=60)
    except subprocess.TimeoutExpired:
        logger.error(f"{filepath} - timeout processing")

    for file in parent.glob('*'):
        os.rename(file, rename(file, filepath.stem))

    if error:
        logger.info(f"{filepath}: {error}")
        for file in parent.glob('*'):
            shutil.copy(file, out_directory)

    
