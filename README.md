# Track Deleter Utility for Ableton Live

![image](https://github.com/user-attachments/assets/0952d468-3003-45be-9580-4e17adb53ed7)

If a project file crashes Live when attempting to open it, you can narrow the cause of the crash down by dragging individual tracks over from Live's browser view into an empty project until you encounter the ones that cause the crash. You can then use this utility to get rid of those tracks and export a new project file excluding those tracks.  

### Usage
[Python](https://www.python.org/) must be installed. Download the script and run it by double clicking and choosing the Python editor or through the command line with: 
```bash
python script.py
```

### Is it safe? 
The program creates a new project file, leaving the original live set unmodified. Regardless, it can still be a good idea to create a backup of your set before attempting recovery on it. 
