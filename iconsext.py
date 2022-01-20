#!/usr/bin/env python3

import logging
import icotool
import sys
from pprint import pprint
import gi
import io
import array
import os
from pathlib import Path
import argparse


gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GdkPixbuf, GLib, Gio, Gdk
from PIL import BmpImagePlugin, PngImagePlugin, Image
import struct

windowlog = logging.getLogger('icotool')
#r.addHandler(logging.StreamHandler())
windowlog.setLevel(logging.DEBUG)

running_folder = os.path.dirname(os.path.abspath(__file__))
share_dir = running_folder
libexec_dir = running_folder

SKIP = -1
SKIP_ALL = -2
OVERWRITE = -4
OVERWRITE_ALL = -5

#pprint(icons.extract_all())

def image2pixbuf(im):
    data = im.tobytes()
    data = GLib.Bytes.new(data)
    has_alpha = im.mode=="RGBA"
    width, height = im.size
    rowstride = width * (3+int(has_alpha))
    pix = GdkPixbuf.Pixbuf.new_from_bytes(
            data, # Image data in 8-bit/sample packed format inside a GLib.Bytes
            GdkPixbuf.Colorspace.RGB, 
            has_alpha, # Whether the data has an opacity channel 
            8, # Number of bits per sample Max 8
            width, 
            height, 
            rowstride
          )
    return pix

class IconsExtractor:

    def __init__(self, iconfile=False, search_subfolders=False):

        if iconfile:
            windowlog.debug(f"Initializing with {iconfile}")
        else:
            windowlog.debug("Initializing")
        
        self.filename=iconfile 
        self.totalicons = 0
        self.totalsize = 0
        self.search_subfolders = False
        self.overwrite_all = False
        self.skipall = False

        # Define signal mappings for builder
        self.handlers = {
        "Quit" : self.cancel,
        "onDestroy": Gtk.main_quit,
        "select_file": self.open_file,
        "select_folder": self.open_folder,
        "open_dialog": self.select_file,
        "close_select_file": self.close_select_file,
        "search_button_clicked_cb" : self.open_items,
        "search_subfolders_toggled_cb" : self.subfolders_toggle,
        "extract_button_activate_cb" : self.extract,
        "icon_selected" : self.icon_selected,
        "extract_window_quit_activate_cb" : Gtk.main_quit,
        "extract_window_show_activate_cb" : self.show_extract_folder,
        "extract_window_show_quit_activate_cb" : self.show_extract_folder_quit,
        "extract_window_close_activate_cb" : self.close_extract_window,
        "about_window": self.about_window,
        "right_click_menu" : self.right_click,
        "right_click_extract" : self.extract,
        "right_click_copy" : self.right_click_copy,
        }

        
        # GTK Initialization
        self.builder = builder = Gtk.Builder()
        self.builder.add_from_file(libexec_dir+"/iconsext.ui")
        self.window = self.builder.get_object("main_window")
        self.builder.connect_signals(self.handlers)
        self.file_chooser = self.builder.get_object("file_chooser")
        self.filefilter = self.builder.get_object("Icon Files")
        self.icon_list = self.builder.get_object("icon_view")
        self.icon_view = self.builder.get_object("select_icons")
        self.icon_view.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.status_bar = self.builder.get_object("status_bar")
        self.context_id = self.status_bar.get_context_id("status_bar")
        self.search_window = self.builder.get_object("search_window")
        self.right_click_menu = self.builder.get_object('popup_menu')
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        
        accel = Gtk.AccelGroup()
        accel.connect(Gdk.keyval_from_name('c'), Gdk.ModifierType.CONTROL_MASK, 0, self.right_click_copy)
        self.window.add_accel_group(accel)

        if search_subfolders:
            self.builder.get_object("search_subfolders").set_active(True)
        
        if self.filename:
            self.builder.get_object("file_path").set_text(self.filename)
            self.open_items()
        
        else:
            self.select_file()
            
        self.window.show_all()

    def subfolders_toggle(self, toggle):
        if self.search_subfolders:
            self.search_subfolders = False
        else:
            self.search_subfolders = True
        windowlog.debug(f"Subfolders toggle set to: {self.search_subfolders}")
        
    def icon_selected(self, icon=None):
        total = len(self.builder.get_object('select_icons').get_selected_items())
        if total == 1:
            self.update_status_bar(f"{total} Icon Selected")
        else:

            self.update_status_bar(f"{total} Icons Selected")

    def cancel(self, button):
        Gtk.main_quit()

    def onDestroy(self, *args):
        Gtk.main_quit()

    def onDestroy(self, *args):
        Gtk.main_quit()

    def get_icons(self, icon_file):

        try:
            icons = icotool.IcoTool(icon_file)
        except:
            return
        icon_data = icons.extract_all()

        for icon in icon_data:
            try:
                img = Image.open(io.BytesIO(icon['ICON']))
            except ValueError:
                windowlog.debug(f"Unable to open icon {icon['filename']}")
                continue

            pixbuf = image2pixbuf(img)
            windowlog.debug(f"{icon['filename']} Width/Height:{img.size}")
            
            l = icon['filename'].rfind("_", 0, icon['filename'].rfind("_"))
            file_without_extention = icon['filename'][:icon['filename'].rfind(".")]
            
            if 'index' not in icon:
                index = None
                name = f"{icon['filename'][:l]} ({icon['ID']})"
            else:
                index = icon['index']
                name = f"{Path(icon['original_filename']).name} ({icon['index']},{icon['ID']})"
            
            self.totalicons += 1
            self.totalsize += len(icon['ICON'])
            self.icon_list.append([pixbuf, name,icon['ID'] ,index, 0.5, file_without_extention])

    def update_status_bar(self, message=""):
        self.status_bar.pop(self.context_id)
        self.status_bar.push(self.context_id, message)
    
    def select_file(self, button=None):
        windowlog.debug("Opening file select window")
        if self.filename:
            self.builder.get_object("file_path").set_text(str(self.path_file.resolve()))

        self.search_window.set_transient_for(self.window)
        self.search_window.show()
        #self.search_window.run()

    def close_select_file(self, button):
        windowlog.debug("Closing file select window")
        self.search_window.hide()

    def open_file(self, button=None):
        windowlog.debug("Select File Button Pressed or first dialog")
        dialog = Gtk.FileChooserDialog(
            title="Please choose a file",
            action=Gtk.FileChooserAction.OPEN,
        )

        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            "Select",
            Gtk.ResponseType.OK)

        file_filter = Gtk.FileFilter()
        file_filter.set_name("ICO/ICL/DLL/EXE")
        file_filter.add_pattern("*.ICO")
        file_filter.add_pattern("*.ico")
        file_filter.add_pattern("*.dll")
        file_filter.add_pattern("*.DLL")
        file_filter.add_pattern("*.ICL")
        file_filter.add_pattern("*.icl")
        file_filter.add_pattern("*.exe")
        file_filter.add_pattern("*.EXE")
        dialog.add_filter(file_filter)
        file_filter = Gtk.FileFilter()
        file_filter.set_name("All Files")
        file_filter.add_pattern("*")
        dialog.add_filter(file_filter)
        # not only local files can be selected in the file selector
        dialog.set_local_only(False)
        # dialog always on top of the textview window
        dialog.set_modal(True)
        # connect the dialog with the callback function open_response_cb()
        dialog.connect("response", self.open_response)
        #always set open to start in home folder instead of recent
        if self.filename:
            dialog.set_current_folder(str(self.path_file.parents[0]))
        else:
            dialog.set_current_folder(str(Path.home()))
        # show the dialog
        dialog.show()  

    def open_folder(self, button):
        windowlog.debug("Select File Button Pressed")
        dialog = Gtk.FileChooserDialog(
            title="Please choose a folder",
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )

        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            "Select",
            Gtk.ResponseType.OK)

        # not only local files can be selected in the file selector
        dialog.set_local_only(False)
        # dialog always on top of the textview window
        dialog.set_modal(True)
        # connect the dialog with the callback function open_response_cb()
        dialog.connect("response", self.open_response)
        #always set open to start in home folder instead of recent
        if self.filename:
            dialog.set_current_folder(str(self.path_file.parents[0]))
        else:
            dialog.set_current_folder(str(Path.home()))
        # show the dialog
        dialog.show()

    # callback function for the dialog open_dialog
    def open_response(self, dialog, response_id):
        windowlog.debug("Open file response")
        open_dialog = dialog
        # if response is "ACCEPT" (the button "Open" has been clicked)
        if response_id == Gtk.ResponseType.OK:

            windowlog.debug("Response OK")
            selected_file = open_dialog.get_filename()
            windowlog.debug(f"File selected: {selected_file}")
            self.path_file = Path(selected_file)
            self.filename = selected_file
            try:
                self.builder.get_object("file_path").set_text(str(self.path_file.resolve()))
            except:
                windowlog.error(f"Error opening {selected_file}")
            # set the content as the text into the buffer
            self.file_name = open_dialog.get_filename()

        # if response is "CANCEL" (the button "Cancel" has been clicked)
        elif response_id == Gtk.ResponseType.CANCEL:
            windowlog.debug("File open cancelled")
        # destroy the FileChooserDialog
        dialog.destroy()

    def open_items(self, button=None):
        self.search_window.hide()

        self.totalicons = 0
        self.totalsize = 0
        totalfiles = 0
        self.icon_list.clear()
        all_files = list()

        self.filename = self.builder.get_object("file_path").get_text()

        windowlog.debug(f"Opening:{self.filename}")
        self.path_file = Path(self.filename)

        if not self.path_file.exists():
            windowlog.error(f"Error opening {self.filename}")
            return
        if self.path_file.is_file():
            windowlog.debug(f"{self.filename} is a file, processing")
            all_files.append(str(self.path_file.resolve()))

        elif self.path_file.is_dir():
            windowlog.debug(f"{self.filename} is a folder, processing")
            
            glob_string = "**/*"
            
            if not self.search_subfolders:
                glob_string = "*"
            
            for l in self.path_file.glob(glob_string):
                if not l.is_dir():
                    all_files.append(str(l))
            
            windowlog.debug(f'{len(all_files)} files found, searching for icons')

        for file_path in all_files:
            self.get_icons(file_path)
            totalfiles +=1

        
        if self.path_file.is_file():
            self.update_status_bar(f"File {self.path_file.name} loaded ({self.totalicons} Icons, {self.totalsize:,} bytes)")
            self.window.set_title(f"Icon Extractor - {self.path_file.name}")
        else:
            self.update_status_bar(f"Folder loaded ({totalfiles} Files, {self.totalicons} Icons, {self.totalsize:,} bytes)")
            self.window.set_title(f"Icon Extractor - {self.path_file}")


    def get_selected(self):
        selected_icons = list()
        liststore = self.builder.get_object("icon_view")
        selected_items = self.builder.get_object('select_icons').get_selected_items()
        #windowlog.debug(f"Getting {len(selected_items)} selected icons")
        for treeview in selected_items:
            treeiter = liststore.get_iter(treeview)
            filename = liststore.get_value(treeiter, 5)
            image = liststore.get_value(treeiter, 0)
            selected_icons.append((filename,image))
        return selected_icons
            
        
    def extract(self, button):
        selected_items = self.get_selected()
        extract_radio = self.builder.get_object("extract_selected")

        if len(selected_items) == 0:
            windowlog.debug("No files selected to extract. Showing error message.")
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="You must select at least one icon to extract",
            )
            dialog.format_secondary_text(
                "Tip: Use CTRL-A to select all icons!"
            )
            dialog.run()
            windowlog.debug("Error Message Closed")

            dialog.destroy()
            return

        dialog = Gtk.FileChooserDialog(
            title="Choose a folder for extraction",
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )

        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            "Select",
            Gtk.ResponseType.OK)
        dialog.set_transient_for(self.window)

        dialog.set_local_only(False)
        dialog.set_modal(True)
        response_id = dialog.run()

        if response_id == Gtk.ResponseType.OK:
            self.selected_folder = dialog.get_filename()
            windowlog.debug(f"Extract to folder name: {self.selected_folder}")
            dialog.destroy()
            
        elif response_id == Gtk.ResponseType.CANCEL:
            windowlog.debug("File open cancelled")
            dialog.destroy()
            return
        else:
            windowlog.debug("File chooser dialog closed")
            dialog.destroy()
            return
        
        windowlog.debug(f"Extracting {len(selected_items)} icons")
        
        extract_window = self.builder.get_object("extract_window")
        self.builder.get_object("extract_window_from_label").set_label(f"Extracting files from \"{self.path_file.name}\"")
        extract_text = "Extracting {} to {}"
        pulse_bar = self.builder.get_object("extract_window_progress_bar")

        button_quit = self.builder.get_object("extract_window_quit")
        button_show = self.builder.get_object("extract_window_show")
        button_show_quit = self.builder.get_object("extract_window_show_quit")
        button_close = self.builder.get_object("extract_window_close")
        button_quit.set_sensitive(False)
        button_show.set_sensitive(False)
        button_show_quit.set_sensitive(False)
        button_close.set_sensitive(False)
        extract_to_label = self.builder.get_object("extract_window_to_label")
        extract_to_label.set_label("")
        pulse_bar.set_fraction(0.0)
        
        total = 0
        total_selected = len(selected_items)
        total_files = 1

        extract_window.show_all()


        for selected in selected_items:
            filename = selected[0]
            pixbuf = selected[1]
            overwrite = False

            extract_path = Path(self.selected_folder) / f"{filename}.png"
            extract_text = extract_text.format(filename, self.selected_folder)
            extract_to_label.set_label(extract_text)
            pulse_bar.set_fraction(total_selected/total_files)
            if extract_path.exists() and not (self.skipall or self.overwrite_all):

                windowlog.debug(f"File {str(extract_path)} exists, asking user")
                what_to_do = self.file_exists(str(extract_path))
                
                if what_to_do == SKIP_ALL:
                    self.skipall = True
                elif what_to_do == SKIP:
                    windowlog.debug(f"Skipping {str(extract_path)} file already exists")
                    continue
                elif what_to_do == OVERWRITE:
                    overwrite = True
                elif what_to_do == OVERWRITE_ALL:
                    self.overwrite_all = True

            if extract_path.exists() and self.skipall:
                windowlog.debug(f"Skipping {str(extract_path)} file already exists")
                continue 

            if overwrite or self.overwrite_all:
                windowlog.debug(f"Extracting {filename} to {extract_path}")
                pixbuf.savev(str(extract_path),"png",[], [])
                extract_window.show_all()
                total_files += 1
            
            if not extract_path.exists():
                windowlog.debug(f"Extracting {filename} to {extract_path}")
                pixbuf.savev(str(extract_path),"png",[], [])
                extract_window.show_all()
                total_files += 1

        self.update_status_bar(f"{total_files} Icons Extracted")
        extract_to_label.set_label("Extraction completed successfully")
        button_quit.set_sensitive(True)
        button_show.set_sensitive(True)
        button_show_quit.set_sensitive(True)
        button_close.set_sensitive(True)
        extract_window.show_all()
        self.extract_window = extract_window
        
    
    def show_extract_folder(self, button):
        if not self.selected_folder:
            return
        windowlog.debug("Opening extract folder {}".format(self.selected_folder))
        member_gfile = Gio.File.new_for_path(self.selected_folder)
        uri = member_gfile.get_uri()
        timestamp = Gtk.get_current_event_time()
        Gtk.show_uri_on_window(None, uri, timestamp)
        self.close_extract_window(None)
    
    def show_extract_folder_quit(self, button):
        self.show_extract_folder(None)
        Gtk.main_quit()

    def close_extract_window(self, button):
        windowlog.debug("Closing extract window")
        self.extract_window.hide()


    def about_window(self, widget):
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="About",
        )
        dialog.format_secondary_text(
            "Icons Extractor by Philip Young. Copyright 2021."
        )
        dialog.run()
        windowlog.debug("INFO dialog closed")

        dialog.destroy()

    def file_exists(self, filename):

        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            title="Overwrite Existing Icon?",
            message_type=Gtk.MessageType.QUESTION,
        )

        # dialog always on top of the textview window
        dialog.set_modal(True)

        #dialog = Gtk.MessageDialog(self.window, Gtk.DialogFlags.MODAL, Gtk.MessageType.QUESTION, Gtk.ButtonsType.NONE)
        dialog.set_markup(
                f"<b>{filename} already exists on disk!</b>\n\n"
                "Do you want to overwrite."
            )
        dialog.add_button("Skip", Gtk.ResponseType.CLOSE)
        dialog.add_button("Skip All", Gtk.ResponseType.NO)
        dialog.add_button("Overwrite", Gtk.ResponseType.YES)
        dialog.add_button("Overwrite All", Gtk.ResponseType.APPLY)

        dialog.set_title("Overwrite Existing Icon?")
        res = dialog.run()
        dialog.destroy()
        if res in (Gtk.ResponseType.CLOSE, Gtk.ResponseType.DELETE_EVENT):
            windowlog.debug("Skipping one file")
            return SKIP
        elif res == Gtk.ResponseType.NO:
            windowlog.debug("Skipping All")
            return SKIP_ALL
        elif res == Gtk.ResponseType.YES:
            windowlog.debug("Overwriting one file")
            return OVERWRITE
        elif res == Gtk.ResponseType.APPLY:
            windowlog.debug("Overwriting All")
            return OVERWRITE_ALL

    def right_click(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            windowlog.debug("Showing right click menu")
            self.right_click_menu.popup(None, None, None, None, event.button, event.time)

    def right_click_copy(self, *args):
        if len(self.get_selected()) > 0:
            filename = self.get_selected()[-1][0]
            pixbuf = self.get_selected()[-1][1]
            windowlog.debug(f"Copying {filename} to clipboard")
            self.clipboard.set_image(pixbuf)

  

windowlog.setLevel(logging.WARNING)

desc = 'Icons Extractor: Gnome tool to extract Icons from Windows ICO, ICL, DLL and EXE files.'
arg_parser = argparse.ArgumentParser(description=desc)
arg_parser.add_argument('-d', '--debug', help="Print debugging statements", action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.WARNING)
arg_parser.add_argument("filename", help="Windows file or folder to extract Icons from", nargs="?", default=None)
arg_parser.add_argument("-s", "--search_subfolders", help="Search subfolders if filename is a folder", default=False, action="store_true")
args = arg_parser.parse_args()

windowlog.setLevel(args.loglevel)

ico = IconsExtractor(iconfile=args.filename, search_subfolders=args.search_subfolders)
Gtk.main()