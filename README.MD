# Icons Extractor

## Description

Icons Extractor is a GTK based Linux tool to select and extract icons from ICO,
ICL, DLL and EXE Windows files. Both Portable Executable (PE) and New 
Executable (NE) Windows files are supported.

You can save the extracted icons to PNG files , or copy the image of a single
icon into the clipboard.

![Icons Extractor Screenshot ICL](screenshots/screenshot1.png?raw=true "Icons Extractor Screenshot ICL")
![Icons Extractor Screenshot DLL](screenshots/screenshot2.png?raw=true "Icons Extractor Screenshot DLL")

To use simply run `python3 iconsext.py`. 

## License

GNU General Public License

## Using Icons Extractor
This utility is a python script and relies on the icotool python library
(included) and a few other python libraries. 
Use `pip install -r requirements.txt` to install the required libraries.

Once you run this script the "Select Icon File(s)" dialog will appear. Using
this window enter or select the file or folders that you wish to scan. To search
all files in any subfolders check the "Search Subfolders" check button. 

You have 2 main search options:

* Select a single file. For example: `/home/user/Downloads/shell32.dll` or `/home/user2/Download/SIMPSONSA.ICL`
    * You can either select the file by clicking the "*Select File*" button or by typing in the filename
* Selecting Multiple Files. For example search for icons in all files in `/home/user/Downloads/`.
    * You can selected the folder that you want to search by either clicking the "*Select Folder*" button or by typing in the folder name.
    * By checking the "*Search Subfolders*" check button all subfolders off of that folder will be scanned as well

Warning: :warning: Searching for icons in an entire drive might take a while. :warning:

After selecting the file or folder you can begin the search by clicking the "*OK*" button. IconsExtractor will then search for all ICO, ICL, DLL and EXE files and extract any and all icons and display them in the main window.


## Saving icons to PNG file(s)

To save the found icons into PNG files:

* Select the icons you wish to save. Pressing <kbd>Ctrl</kbd> + <kbd>a</kbd> will select all icons.
* Clicking the "*Extract*" button (or right clicking and selecting "*Extract*") will open a folder selection window, pressing "*Select*" will extract all the selected icons to that folder.

## Copy a single icon to the Clipboard

You can copy an icon to the clipboard in one of two ways:

* Selecting an icon and pressing <kbd>Ctrl</kbd> + <kbd>c</kbd>
* Selecting an icon, right clicking and selecting "*Copy*"

:warning: When selecting multiple icons, one the first icon will be placed on to your clip board.

## Command line arguments

When you run Icons Extractor from the command line you can pass three arguments:

* `-d`/`--debug`: this enables debugging messages to the console
* `-s`/`--search_subfolders`: if a path argument is supplied
* `path/to/some/file/or/folder.txt` a path to a file or folder which will automatically be searched for icons.

## Where to get icons

You can find icons all over the web. Some favorites are:

* Icon Factory: https://freeware.iconfactory.com/icons
* ICL Files: https://zapatopi.net/icon/ and http://cd.textfiles.com/desktopworks/ICON_LIB/
* Windows (shell32.dll has a lot of icons)


