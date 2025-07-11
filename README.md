# Overlay Thing for Windows using Pygame
- Makes overlays
- They stay on top
- They can be moved around and snap and show data and can be used
- Many windows exist:
  - A clock
  - A notepad
  - A calculator
- Definitely Windows only
## Install
- To use, you should run these: (make sure you are in the correct folder and have python 3)
```powershell
> pip install requirements.txt
> python main.py
```
## Usage
- A main menu should appear. click the toggles to enable or disable the overlays.
- You can drag the overlays around and they will snap to the edges of the screen and to each other.

## Notes
- The clock shows HH:MM:SS time and the date in DD/MM/YYYY format.
  - If you are american and want MM/DD/YYYY, nope. hack the app. go ahead
- The notepad allows you to type text notes. It saves automatically, even if the overlays app crashes. It will be stored in the current directory.
- This is why its important to be in the correct folder, as otherwise the notes files might not be found or could be saved in random folders.
- The calculator is a simple calculator that does python eval. It can do basic arithmetic and more complex expressions. sin, cos, and other math functions are available.
- The overlays are always on top, so you can use them while doing other things.