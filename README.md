# webcam-antispoofing - AfterFall team SP1:

### using python 3.9.5

### install create python env bash command interminal:
```bash
brew install python@3.9  

python3.9 -m venv myenv

source myenv/bin/activate  # On macOS/Linux myenv\Scripts\activate  # On Windows

pip install -r requirements.txt

pip list # check all the library
```

# if haing issue dlib library use this command 
```bash
brew install cmake

brew install boost

brew install boost-python3

brew install jpeg
```

### Then reinstall dlib

```bash
pip uninstall dlib

pip install dlib
```
# run this program

## clone this repo
```bash
gh repo clone OwenYooYoo/webcam-antispoofing
```
```bash
cd webcam-antispoofing
```
```bash
pip install -r requirements.txt
```
# save faces data

```bash
python SaveNewFaces.py

```
# utilize the model 

```bash
python SaveNewFaces.py

```

ref:

https://github.com/ageitgey/face_recognition/blob/master/examples/facerec_from_webcam.py

https://github.com/ageitgey/face_recognition/blob/master/examples/blink_detection.py
