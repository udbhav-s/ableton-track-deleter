import xml.etree.ElementTree as ET
import gzip
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

track_structure = None
xml_root = None

def parse_live_set(als_file):
    with gzip.open(als_file, "rb") as f:
        live_xml = f.read()

    root = ET.fromstring(live_xml)
    tracks_element = root.find(".//Tracks")

    all_tracks = {}

    for track_element in tracks_element:
        track_id = track_element.get("Id")
        track_type = track_element.tag
        name_element = track_element.find(".//Name/EffectiveName")
        track_name = name_element.get("Value") if name_element is not None else "Unnamed Track"
        
        group_id_element = track_element.find("TrackGroupId")
        parent_group = group_id_element.get("Value") if group_id_element is not None else "-1"
        
        all_tracks[track_id] = {
            "name": track_name,
            "type": "Group" if track_type == "GroupTrack" else ("MIDI" if track_type == "MidiTrack" else "Audio"),
            "children": [],
            "parent_group": parent_group
        }

    # Second pass to add tracks to parent groups' children
    for track_id, track in all_tracks.items():
        parent_id = track["parent_group"]
        if parent_id != "-1" and parent_id in all_tracks:
            all_tracks[parent_id]["children"].append(track_id)

    return all_tracks, root

def populate_tree(tree, tracks, parent, track_id):
    track = tracks[track_id]
    item = tree.insert(parent, 'end', iid=track_id, text=f"{track['name']} ({track['type']})")
    for child_id in track['children']:
        populate_tree(tree, tracks, track_id, child_id)

def load_als_file(tree):
    global track_structure, xml_root

    file_path = filedialog.askopenfilename(filetypes=[("Ableton Live Set", "*.als")])
    if file_path:
        track_structure, xml_root = parse_live_set(file_path)
        tree.delete(*tree.get_children())
        for track_id, track in track_structure.items():
            if track["parent_group"] == "-1":
                populate_tree(tree, track_structure, '', track_id)

def get_all_child_ids(tracks, parent_id):
    child_ids = []
    for child_id in tracks[parent_id]['children']:
        child_ids.append(child_id)
        if tracks[child_id]['type'] == 'Group':
            child_ids.extend(get_all_child_ids(tracks, child_id))
    return child_ids

def delete_selected_tracks(tree):
    global track_structure, xml_root

    selected_items = tree.selection()
    if not selected_items:
        messagebox.showinfo("Info", "No tracks selected")
        return

    tracks_to_delete = []
    for item in selected_items:
        if track_structure[item]['type'] == 'Group':
            result = messagebox.askyesno("Confirm Deletion", 
                f"Deleting group '{track_structure[item]['name']}' will also delete all tracks inside. Proceed?")
            if result:
                tracks_to_delete.append(item)
                tracks_to_delete.extend(get_all_child_ids(track_structure, item))
        else:
            tracks_to_delete.append(item)

    if not tracks_to_delete:
        return
    
    # Remove tracks from XML
    tracks_element = xml_root.find(".//Tracks")
    for track_id in tracks_to_delete:
        track_to_remove = tracks_element.find(f"./*[@Id='{track_id}']")
        if track_to_remove is not None:
            tracks_element.remove(track_to_remove)

    # Remove tracks from track_structure
    for track_id in tracks_to_delete:
        parent_id = track_structure[track_id]['parent_group']
        if parent_id != "-1" and parent_id in track_structure:
            track_structure[parent_id]['children'].remove(track_id)
        del track_structure[track_id]

    # Remove items from TreeView
    for item in tracks_to_delete:
        tree.delete(item)

    messagebox.showinfo("Success", f"{len(tracks_to_delete)} track(s) deleted successfully")

class ProgressWindow:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Saving...")
        self.top.geometry("300x100")
        self.top.transient(parent)
        self.top.grab_set()

        self.progress = ttk.Progressbar(self.top, orient="horizontal", length=250, mode="indeterminate")
        self.progress.pack(pady=20)

        self.label = ttk.Label(self.top, text="Saving Live Set...")
        self.label.pack()

    def start(self):
        self.progress.start()

    def stop(self):
        self.progress.stop()
        self.top.destroy()

def save_live_set_thread(root, file_path, progress_window):
    global xml_root

    try:
        # Convert the XML to a string
        xml_string = ET.tostring(xml_root, encoding='UTF-8', xml_declaration=True)

        # Gzip the XML string
        with gzip.open(file_path, 'wb') as f:
            f.write(xml_string)

        root.after(0, lambda: messagebox.showinfo("Success", f"Live Set saved successfully to:\n{file_path}"))
    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Error", f"An error occurred while saving the Live Set:\n{str(e)}"))
    finally:
        root.after(0, progress_window.stop)

def save_live_set(root):
    global xml_root

    if xml_root is None:
        messagebox.showinfo("Info", "No Live Set loaded")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".als",
        filetypes=[("Ableton Live Set", "*.als")],
        title="Save Modified Ableton Live Set"
    )

    if not file_path:
        return  # User cancelled the save dialog

    progress_window = ProgressWindow(root)
    progress_window.start()

    thread = threading.Thread(target=save_live_set_thread, args=(root, file_path, progress_window))
    thread.start()

# Create the main window
root = tk.Tk()
root.title("Live Set Deleter")
root.geometry("800x600")

# Create a frame for the Treeview
frame = ttk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Create the Treeview
tree = ttk.Treeview(frame)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Add a scrollbar
scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
tree.configure(yscrollcommand=scrollbar.set)

button_frame = ttk.Frame(root)
button_frame.pack(pady=10)

load_button = ttk.Button(button_frame, text="Load Ableton Live Set", command=lambda: load_als_file(tree))
load_button.pack(side=tk.LEFT, padx=5)

delete_button = ttk.Button(button_frame, text="Delete Selected Tracks", command=lambda: delete_selected_tracks(tree))
delete_button.pack(side=tk.LEFT, padx=5)

save_button = ttk.Button(button_frame, text="Save Live Set", command=lambda: save_live_set(root))
save_button.pack(side=tk.LEFT, padx=5)

# Start the Tkinter event loop
root.mainloop()
