import tkinter as tk
from tkinter import filedialog, messagebox
import os
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

def merge_drum_tracks(track5_msgs, track6_msgs):
    """
    Merge two drum tracks, giving priority to track6 when notes overlap.
    """
    # Convert messages to list with absolute time for easier comparison
    def get_abs_times(messages):
        abs_time = 0
        abs_msgs = []
        for msg in messages:
            abs_time += msg.time
            abs_msgs.append((abs_time, msg.copy(time=0)))
        return abs_msgs
    
    track5_abs = get_abs_times(track5_msgs)
    track6_abs = get_abs_times(track6_msgs)
    
    # Find overlapping notes in track5 that should be removed
    # (notes that occur at same time with same note number in track6)
    track6_note_times = {}
    for abs_time, msg in track6_abs:
        if msg.type == 'note_on' and msg.velocity > 0:
            key = (abs_time, msg.note)
            track6_note_times[key] = True
    
    # Filter track5 to remove overlapping notes
    filtered_track5 = []
    for abs_time, msg in track5_abs:
        if msg.type == 'note_on' and msg.velocity > 0:
            key = (abs_time, msg.note)
            if key not in track6_note_times:
                filtered_track5.append((abs_time, msg))
        else:
            filtered_track5.append((abs_time, msg))
    
    # Combine both tracks
    combined = filtered_track5 + track6_abs
    
    # Sort by absolute time
    combined.sort(key=lambda x: x[0])
    
    # Convert back to delta times
    result = []
    last_time = 0
    for abs_time, msg in combined:
        delta = abs_time - last_time
        msg.time = delta
        result.append(msg)
        last_time = abs_time
    
    return result

def combine_midi_files(folder_path, bpm, delete_individual=False):
    """
    Combine 6 MIDI files into one Type 1 MIDI file.
    """
    # First, read one of the source files to get the ticks_per_beat
    first_file = MidiFile(os.path.join(folder_path, "1.mid"))
    ticks_per_beat = first_file.ticks_per_beat
    
    # Create new MIDI file (Type 1) with same timing resolution
    output_midi = MidiFile(type=1, ticks_per_beat=ticks_per_beat)
    
    # Create tempo track (Track 0)
    tempo_track = MidiTrack()
    output_midi.tracks.append(tempo_track)
    
    # Set tempo (BPM)
    tempo = bpm2tempo(bpm)
    tempo_track.append(MetaMessage('set_tempo', tempo=tempo, time=0))
    tempo_track.append(MetaMessage('end_of_track', time=0))
    
    # Keep track of files to delete
    files_to_delete = []
    
    # Load and process files 1-4 (Channels 1-4)
    for i in range(1, 5):
        filename = os.path.join(folder_path, f"{i}.mid")
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File {i}.mid not found in folder")
        
        files_to_delete.append(filename)
        midi_file = MidiFile(filename)
        new_track = MidiTrack()
        output_midi.tracks.append(new_track)
        
        # Add track name
        new_track.append(MetaMessage('track_name', name=f'CH{i}', time=0))
        
        # Copy all messages and set to appropriate channel
        for track in midi_file.tracks:
            for msg in track:
                if msg.is_meta:
                    if msg.type != 'end_of_track' and msg.type != 'set_tempo' and msg.type != 'track_name':
                        new_track.append(msg.copy())
                else:
                    # Set channel (0-indexed, so channel 1 = 0)
                    new_msg = msg.copy(channel=i-1)
                    new_track.append(new_msg)
        
        new_track.append(MetaMessage('end_of_track', time=0))
    
    # Load files 5 and 6 (both Channel 10 - drums)
    track5_msgs = []
    track6_msgs = []
    
    for i, msg_list in [(5, track5_msgs), (6, track6_msgs)]:
        filename = os.path.join(folder_path, f"{i}.mid")
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File {i}.mid not found in folder")
        
        files_to_delete.append(filename)
        midi_file = MidiFile(filename)
        for track in midi_file.tracks:
            for msg in track:
                if not msg.is_meta or (msg.type != 'end_of_track' and msg.type != 'set_tempo'):
                    if msg.is_meta:
                        msg_list.append(msg.copy())
                    else:
                        # Set to channel 10 (9 in 0-indexed)
                        msg_list.append(msg.copy(channel=9))
    
    # Merge drum tracks with priority to track 6
    merged_drums = merge_drum_tracks(track5_msgs, track6_msgs)
    
    # Create the merged drum track
    drum_track = MidiTrack()
    output_midi.tracks.append(drum_track)
    
    # Add track name for drums
    drum_track.append(MetaMessage('track_name', name='CH10', time=0))
    
    for msg in merged_drums:
        drum_track.append(msg)
    drum_track.append(MetaMessage('end_of_track', time=0))
    
    # Delete individual files if requested
    if delete_individual:
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not delete {file_path}: {e}")
    
    return output_midi

class MidiCombinerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MIDI File Combiner")
        self.root.geometry("500x280")
        
        # Folder selection
        tk.Label(root, text="Select Folder with MIDI Files (1.mid - 6.mid):").pack(pady=10)
        
        folder_frame = tk.Frame(root)
        folder_frame.pack(pady=5)
        
        self.folder_path = tk.StringVar()
        tk.Entry(folder_frame, textvariable=self.folder_path, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(folder_frame, text="Browse", command=self.browse_folder).pack(side=tk.LEFT)
        
        # Name input
        name_frame = tk.Frame(root)
        name_frame.pack(pady=10)
        
        tk.Label(name_frame, text="File Name (8 char):").pack(side=tk.LEFT, padx=5)
        self.name_var = tk.StringVar()
        name_entry = tk.Entry(name_frame, textvariable=self.name_var, width=10)
        name_entry.pack(side=tk.LEFT)
        
        # Add character limit
        def limit_chars(*args):
            value = self.name_var.get()
            if len(value) > 8:
                self.name_var.set(value[:8])
        self.name_var.trace('w', limit_chars)
        
        # BPM input
        bpm_frame = tk.Frame(root)
        bpm_frame.pack(pady=10)
        
        tk.Label(bpm_frame, text="BPM:").pack(side=tk.LEFT, padx=5)
        self.bpm_var = tk.StringVar(value="120")
        tk.Entry(bpm_frame, textvariable=self.bpm_var, width=10).pack(side=tk.LEFT)
        
        # Delete individual files checkbox
        self.delete_var = tk.BooleanVar(value=True)
        tk.Checkbutton(root, text="Delete individual files after combining", 
                      variable=self.delete_var).pack(pady=5)
        
        # Combine button with dark text
        tk.Button(root, text="Combine MIDI Files", command=self.combine_files, 
                 bg="#4CAF50", fg="black", font=("Arial", 12, "bold")).pack(pady=20)
        
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
    
    def combine_files(self):
        folder = self.folder_path.get()
        if not folder:
            messagebox.showerror("Error", "Please select a folder")
            return
        
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a file name")
            return
        
        # Clean filename (remove invalid characters)
        name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        
        try:
            bpm = float(self.bpm_var.get())
            if bpm <= 0:
                raise ValueError("BPM must be positive")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid BPM")
            return
        
        try:
            # Combine the files
            output_midi = combine_midi_files(folder, bpm, delete_individual=self.delete_var.get())
            
            # Create filename with name and BPM
            bpm_int = int(bpm)
            output_filename = f"{name}_{bpm_int}.mid"
            output_path = os.path.join(folder, output_filename)
            
            output_midi.save(output_path)
            
            delete_msg = "\n\nIndividual files deleted." if self.delete_var.get() else ""
            
            messagebox.showinfo("Success", 
                              f"MIDI files combined successfully!\nSaved as: {output_filename}\n\n"
                              f"Track 1: Channel 1\nTrack 2: Channel 2\n"
                              f"Track 3: Channel 3\nTrack 4: Channel 4\n"
                              f"Track 5: Channel 10 (Drums - merged with priority)\n"
                              f"BPM: {bpm}{delete_msg}")
        
        except FileNotFoundError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiCombinerGUI(root)
    root.mainloop()
