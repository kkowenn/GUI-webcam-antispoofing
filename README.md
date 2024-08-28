# webcam-antispoofing - after team:

### using python 3.9.5

### install create python env bash command interminal:

brew install python@3.9  

python3.9 -m venv myenv

source myenv/bin/activate  # On macOS/Linux myenv\Scripts\activate  # On Windows

pip install -r requirements.txt

pip list # check all the library


# if haing issue dlib library use this command 

brew install cmake

brew install boost

brew install boost-python3

brew install jpeg

### Then reinstall dlib

pip uninstall dlib

pip install dlib

