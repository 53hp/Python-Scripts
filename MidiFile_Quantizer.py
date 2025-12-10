import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from mido import MidiFile, MidiTrack, Message
import os

class MidiNoteQuantizer:
    def __init__(self, root):
        self.root = root
        self.root.title("MIDI Note Quantizer")
        self.root.geometry("600x650")
        self.root.configure(bg='#2b2b2b')
        
        # All 12 notes
        self.all_notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Note to MIDI number mapping (C = 0, C# = 1, etc.)
        self.note_to_num = {note: i for i, note in enumerate(self.all_notes)}
        
        # Storage for selected notes
        self.note_vars = []
        
        self.create_widgets()
    
    def create_widgets(self):
        # Title
        title_label = tk.Label(self.root, 
                              text="MIDI Note Quantizer",
                              font=('Helvetica', 24, 'bold'),
                              bg='#2b2b2b',
                              fg='#ffffff')
        title_label.pack(pady=20)
        
        # Info box
        info_frame = tk.Frame(self.root, bg='#3d3d3d', relief=tk.RAISED, borderwidth=2)
        info_frame.pack(padx=20, pady=10, fill=tk.X)
        
        info_label = tk.Label(info_frame,
                             text="Use button below to get started",
                             font=('Helvetica', 10),
                             bg='#3d3d3d',
                             fg='#cccccc',
                             pady=5)
        info_label.pack()
        
        # Scale selection frame
        scale_frame = tk.Frame(self.root, bg='#3d3d3d', relief=tk.RAISED, borderwidth=2)
        scale_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        scale_label = tk.Label(scale_frame,
                              text="Select 3 Notes for Your Scale:",
                              font=('Helvetica', 12, 'bold'),
                              bg='#3d3d3d',
                              fg='#ffffff',
                              pady=10)
        scale_label.pack()
        
        # Preset buttons frame
        preset_frame = tk.Frame(scale_frame, bg='#3d3d3d')
        preset_frame.pack(pady=(5, 10))
        
        preset_label = tk.Label(preset_frame,
                               text="Quick Presets:",
                               font=('Helvetica', 10),
                               bg='#3d3d3d',
                               fg='#cccccc')
        preset_label.grid(row=0, column=0, columnspan=6, pady=(0, 5))
        
        # Major triads (top 10)
        major_label = tk.Label(preset_frame,
                              text="Major:",
                              font=('Helvetica', 9, 'bold'),
                              bg='#3d3d3d',
                              fg='#ffffff')
        major_label.grid(row=1, column=0, padx=(10, 5), sticky='e')
        
        major_presets = [
            ("C", ['C', 'E', 'G']),
            ("D", ['D', 'F#', 'A']),
            ("E", ['E', 'G#', 'B']),
            ("G", ['G', 'B', 'D']),
            ("A", ['A', 'C#', 'E']),
            ("F", ['F', 'A', 'C']),
            ("Bb", ['A#', 'D', 'F']),
            ("Eb", ['D#', 'G', 'A#']),
            ("Ab", ['G#', 'C', 'D#']),
            ("Db", ['C#', 'F', 'G#'])
        ]
        
        for i, (name, notes) in enumerate(major_presets):
            btn = tk.Button(preset_frame,
                           text=name,
                           command=lambda n=notes: self.set_notes(n),
                           bg='#4a90e2',
                           fg='black',
                           font=('Helvetica', 8, 'bold'),
                           width=4,
                           relief=tk.RAISED,
                           borderwidth=2)
            btn.grid(row=1, column=i+1, padx=2, pady=2)
        
        # Minor triads (top 10)
        minor_label = tk.Label(preset_frame,
                              text="Minor:",
                              font=('Helvetica', 9, 'bold'),
                              bg='#3d3d3d',
                              fg='#ffffff')
        minor_label.grid(row=2, column=0, padx=(10, 5), sticky='e')
        
        minor_presets = [
            ("Am", ['A', 'C', 'E']),
            ("Dm", ['D', 'F', 'A']),
            ("Em", ['E', 'G', 'B']),
            ("Cm", ['C', 'D#', 'G']),
            ("F#m", ['F#', 'A', 'C#']),
            ("Bm", ['B', 'D', 'F#']),
            ("Gm", ['G', 'A#', 'D']),
            ("C#m", ['C#', 'E', 'G#']),
            ("G#m", ['G#', 'B', 'D#']),
            ("D#m", ['D#', 'F#', 'A#'])
        ]
        
        for i, (name, notes) in enumerate(minor_presets):
            btn = tk.Button(preset_frame,
                           text=name,
                           command=lambda n=notes: self.set_notes(n),
                           bg='#9b59b6',
                           fg='black',
                           font=('Helvetica', 8, 'bold'),
                           width=4,
                           relief=tk.RAISED,
                           borderwidth=2)
            btn.grid(row=2, column=i+1, padx=2, pady=2)
        
        # Dropdown menus for manual selection
        dropdowns_frame = tk.Frame(scale_frame, bg='#3d3d3d')
        dropdowns_frame.pack(pady=10)
        
        for i in range(3):
            note_var = tk.StringVar(value=self.all_notes[0])
            self.note_vars.append(note_var)
            
            label = tk.Label(dropdowns_frame,
                           text=f"Note {i+1}:",
                           bg='#3d3d3d',
                           fg='#ffffff',
                           font=('Helvetica', 10))
            label.grid(row=i, column=0, padx=10, pady=5, sticky='e')
            
            dropdown = ttk.Combobox(dropdowns_frame,
                                   textvariable=note_var,
                                   values=self.all_notes,
                                   state='readonly',
                                   width=10,
                                   font=('Helvetica', 10))
            dropdown.grid(row=i, column=1, padx=10, pady=5)
        
        # Process button
        process_btn = tk.Button(self.root,
                               text="Select Folder & Process MIDI Files",
                               command=self.process_folder,
                               bg='#4CAF50',
                               fg='white',
                               font=('Helvetica', 12, 'bold'),
                               pady=10,
                               relief=tk.RAISED,
                               borderwidth=3)
        process_btn.pack(pady=20)
        
        # Output text area
        output_frame = tk.Frame(self.root, bg='#2b2b2b')
        output_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        output_label = tk.Label(output_frame,
                               text="Output Log:",
                               font=('Helvetica', 10, 'bold'),
                               bg='#2b2b2b',
                               fg='#ffffff')
        output_label.pack(anchor='w')
        
        self.output_text = tk.Text(output_frame,
                                  height=15,
                                  bg='#1e1e1e',
                                  fg='#00ff00',
                                  font=('Courier', 9),
                                  relief=tk.SUNKEN,
                                  borderwidth=2)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(self.output_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.output_text.yview)
        
        self.log("Ready! Select your scale notes and choose a folder to process.")
    
    def log(self, message):
        """Add message to output text area"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update()
    
    def set_notes(self, notes):
        """Set the dropdown values from a preset"""
        for i, note in enumerate(notes):
            self.note_vars[i].set(note)
    
    def get_closest_note(self, midi_note, allowed_notes):
        """Find the closest allowed note to the given MIDI note"""
        note_in_octave = midi_note % 12
        octave = midi_note // 12
        
        # Find closest allowed note
        closest = min(allowed_notes, key=lambda x: abs(x - note_in_octave))
        
        # Return MIDI note in same octave
        return octave * 12 + closest
    
    def process_midi_file(self, filepath, allowed_notes, output_dir, selected_notes):
        """Process a single MIDI file"""
        try:
            mid = MidiFile(filepath)
            filename = os.path.basename(filepath)
            
            # Create notes suffix for filename (replace # with s)
            notes_suffix = "".join(selected_notes).replace('#', 's')
            
            # Split filename into name and extension
            name_without_ext = os.path.splitext(filename)[0]
            extension = os.path.splitext(filename)[1]
            
            # Create new filename with notes suffix
            new_filename = f"{name_without_ext}_{notes_suffix}{extension}"
            
            changes_per_track = {}
            total_changes = 0
            
            for track_idx, track in enumerate(mid.tracks):
                changes_per_track[track_idx] = 0
                
                for msg in track:
                    # Only process note_on and note_off messages
                    if msg.type in ['note_on', 'note_off']:
                        # Skip drum channel (channel 9, which is 10 in 1-indexed)
                        if msg.channel == 9:
                            continue
                        
                        original_note = msg.note
                        quantized_note = self.get_closest_note(original_note, allowed_notes)
                        
                        if original_note != quantized_note:
                            msg.note = quantized_note
                            changes_per_track[track_idx] += 1
                            total_changes += 1
            
            # Save processed file with new name
            output_path = os.path.join(output_dir, new_filename)
            mid.save(output_path)
            
            return total_changes, changes_per_track
            
        except Exception as e:
            filename = os.path.basename(filepath)
            self.log(f"Error processing {filename}: {str(e)}")
            return 0, {}
    
    def process_folder(self):
        """Select folder and process all MIDI files"""
        # Get selected notes
        selected_notes = [var.get() for var in self.note_vars]
        allowed_notes = [self.note_to_num[note] for note in selected_notes]
        
        self.log(f"\nSelected scale: {', '.join(selected_notes)}")
        
        # Select input folder
        input_folder = filedialog.askdirectory(title="Select Folder with MIDI Files")
        if not input_folder:
            return
        
        # Create output folder with note names
        notes_string = "".join(selected_notes)  # e.g., "CEG" or "AC#E"
        output_folder = os.path.join(input_folder, f"Quantized_{notes_string}")
        os.makedirs(output_folder, exist_ok=True)
        
        self.log(f"Input folder: {input_folder}")
        self.log(f"Output folder: {output_folder}")
        self.log("\nScanning for MIDI files (including subfolders)...\n")
        
        # Find all MIDI files recursively using os.walk
        midi_files = []
        for root, dirs, files in os.walk(input_folder):
            for file in files:
                if file.endswith(('.mid', '.midi')):
                    full_path = os.path.join(root, file)
                    midi_files.append(full_path)
        
        if not midi_files:
            self.log("No MIDI files found in selected folder or subfolders!")
            messagebox.showwarning("No Files", "No MIDI files found in the selected folder.")
            return
        
        # Show folder structure summary
        folders_with_midi = set()
        for filepath in midi_files:
            relative_folder = os.path.relpath(os.path.dirname(filepath), input_folder)
            if relative_folder != '.':
                folders_with_midi.add(relative_folder)
        
        self.log(f"Found {len(midi_files)} MIDI files")
        if folders_with_midi:
            self.log(f"Spread across {len(folders_with_midi)} folders")
            if len(folders_with_midi) <= 5:
                for folder in sorted(folders_with_midi):
                    self.log(f"  📁 {folder}")
            else:
                for folder in sorted(folders_with_midi)[:5]:
                    self.log(f"  📁 {folder}")
                self.log(f"  ... and {len(folders_with_midi) - 5} more folders")
        self.log("")
        
        # Process each file
        total_files = len(midi_files)
        for idx, filepath in enumerate(midi_files, 1):
            # Get relative path for better logging
            relative_path = os.path.relpath(filepath, input_folder)
            self.log(f"[{idx}/{total_files}] Processing: {relative_path}")
            
            # Preserve folder structure in output
            relative_dir = os.path.dirname(relative_path)
            output_subfolder = os.path.join(output_folder, relative_dir)
            os.makedirs(output_subfolder, exist_ok=True)
            
            changes, track_changes = self.process_midi_file(filepath, allowed_notes, output_subfolder, selected_notes)
            
            if changes > 0:
                self.log(f"  ✓ Changed {changes} notes")
            else:
                self.log(f"  ✓ No changes needed")
        
        self.log(f"\n✓ Complete! Processed {total_files} files.")
        self.log(f"✓ Output saved to: {output_folder}\n")
        
        messagebox.showinfo("Success", 
                           f"Processed {total_files} MIDI files!\n\nOutput saved to:\n{output_folder}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiNoteQuantizer(root)
    root.mainloop()
