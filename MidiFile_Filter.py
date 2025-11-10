#!/usr/bin/env python3
"""
MIDI Filter - Top 5 Tracks by Event Count (Thonny Version)
- Type 0: Converts to Type 1 by separating channels, then keeps top 5
- Type 1: Keeps top 5 tracks with most events
- Standardizes all tracks to use channels 0,1,2,3,9
- Detects bass (notes below C3) and moves to channel 1 (device ch 2)
- Removes empty/sparse tracks automatically
- Saves to separate folders based on original type
"""

import os
import tkinter as tk
from tkinter import filedialog, scrolledtext
from pathlib import Path
import mido

class MIDIFilterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MIDI Filter - Type 0 & Type 1 - Top 5 Tracks")
        self.root.geometry("700x600")
        self.root.configure(bg='#2b2b2b')
        
        # Settings
        self.max_tracks = 5
        self.min_events = 50
        
        # Main container
        main_frame = tk.Frame(root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title = tk.Label(main_frame, 
                        text="MIDI Filter - Top 5 Tracks",
                        font=('Helvetica', 18, 'bold'),
                        bg='#2b2b2b',
                        fg='#ffffff')
        title.pack(pady=(0, 10))
        
        subtitle = tk.Label(main_frame,
                           text="Type 0: Converts by channel | Type 1: Keeps top 5 tracks",
                           font=('Helvetica', 12),
                           bg='#2b2b2b',
                           fg='#cccccc')
        subtitle.pack(pady=(0, 20))
        
        # Info box - REDUCED SIZE
        info_frame = tk.Frame(main_frame, 
                             bg='#3d3d3d',
                             relief=tk.SUNKEN,
                             borderwidth=3)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_label = tk.Label(info_frame,
                             text="📁 Select MIDI Folder\n\nUse button below to get started",
                             font=('Helvetica', 14),
                             bg='#3d3d3d',
                             fg='#ffffff',
                             pady=25)
        info_label.pack(fill=tk.X)
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg='#2b2b2b')
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Select folder button - BLACK TEXT
        self.folder_btn = tk.Button(button_frame,
                                    text="📂 Select Folder",
                                    command=self.select_folder,
                                    font=('Helvetica', 12, 'bold'),
                                    bg='#4a90e2',
                                    fg='black',  # Changed to black
                                    activebackground='#357abd',
                                    activeforeground='black',  # Changed to black
                                    relief=tk.FLAT,
                                    padx=20,
                                    pady=10,
                                    cursor='hand2')
        self.folder_btn.pack(side=tk.LEFT, padx=5)
        
        # Clear button
        self.clear_btn = tk.Button(button_frame,
                                   text="🗑️ Clear",
                                   command=self.clear_output,
                                   font=('Helvetica', 12, 'bold'),
                                   bg='#666666',
                                   fg='black',
                                   activebackground='#555555',
                                   activeforeground='black',
                                   relief=tk.FLAT,
                                   padx=20,
                                   pady=10,
                                   cursor='hand2')
        self.clear_btn.pack(side=tk.RIGHT, padx=5)
        
        # Output text area
        output_label = tk.Label(main_frame,
                               text="Output:",
                               font=('Helvetica', 10, 'bold'),
                               bg='#2b2b2b',
                               fg='#ffffff',
                               anchor='w')
        output_label.pack(fill=tk.X, pady=(0, 5))
        
        self.output_text = scrolledtext.ScrolledText(main_frame,
                                                     height=10,
                                                     font=('Courier', 10),
                                                     bg='#1e1e1e',
                                                     fg='#00ff00',
                                                     insertbackground='white',
                                                     relief=tk.FLAT,
                                                     borderwidth=2)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        self.log("Ready! Select a folder containing MIDI files to begin.")
    
    def log(self, message):
        """Add message to output text area"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update()
    
    def clear_output(self):
        """Clear the output text area"""
        self.output_text.delete(1.0, tk.END)
        self.log("Ready! Select a folder containing MIDI files to begin.")
    
    def select_folder(self):
        """Open folder selection dialog"""
        folder = filedialog.askdirectory(title="Select Folder Containing MIDI Files")
        if folder:
            self.process_folder(folder)
    
    def process_folder(self, folder_path):
        """Process all MIDI files in a folder"""
        self.log("\n" + "="*60)
        self.log(f"Processing folder: {folder_path}")
        
        path = Path(folder_path)
        midi_files = list(path.glob("*.mid")) + list(path.glob("*.midi"))
        
        if midi_files:
            self.process_files(midi_files)
        else:
            self.log("❌ No MIDI files found in folder!")
    
    def count_track_events(self, track):
        """Count the number of MIDI events in a track (excluding meta messages)"""
        count = 0
        for msg in track:
            # Count note events and control changes, skip meta messages
            if not msg.is_meta:
                count += 1
        return count
    
    def get_track_channel(self, track):
        """Get the primary channel number for a track (for sorting)"""
        # Find the first message with a channel
        for msg in track:
            if hasattr(msg, 'channel'):
                return msg.channel
        return 999  # Meta tracks or tracks without channels go last
    
    def standardize_channels(self, tracks):
        """
        Standardize channel assignment to 0,1,2,3,9
        - Channel 9 reserved for drums (most common convention)
        - Channels 0,1,2,3 for melodic instruments
        """
        # Available channels: 0, 1, 2, 3, 9
        melodic_channels = [0, 1, 2, 3]
        drum_channel = 9
        
        # First, detect drums (channel 9 or percussion sounds)
        drum_tracks = []
        melodic_tracks = []
        
        for t in tracks:
            original_channel = t['channel']
            
            # Check if it's a drum track (originally on channel 9)
            if original_channel == 9:
                drum_tracks.append(t)
            else:
                melodic_tracks.append(t)
        
        # Process drum tracks - assign to channel 9
        for t in drum_tracks:
            old_ch = t['channel']
            if old_ch != 9:
                # Remap all messages in track to channel 9
                for msg in t['track']:
                    if hasattr(msg, 'channel'):
                        msg.channel = 9
                t['old_channel'] = old_ch
                t['channel'] = 9
        
        # Process melodic tracks - assign to channels 0,1,2,3
        next_melodic_idx = 0
        for t in melodic_tracks:
            old_ch = t['channel']
            
            # Assign to next available melodic channel
            if old_ch not in melodic_channels or old_ch == 999:  # Need to remap
                new_ch = melodic_channels[next_melodic_idx % len(melodic_channels)]
                
                # Remap all messages in track to new channel
                for msg in t['track']:
                    if hasattr(msg, 'channel'):
                        msg.channel = new_ch
                
                t['old_channel'] = old_ch
                t['channel'] = new_ch
                next_melodic_idx += 1
            else:
                # Already on a valid melodic channel, but advance counter
                # to avoid overlapping with existing channels
                next_melodic_idx += 1
        
        return drum_tracks + melodic_tracks
    
    def detect_bass_track(self, tracks):
        """
        Detect bass track (notes primarily below C3 = note 48) and move to channel 1
        """
        # Analyze each track for bass-range notes
        bass_track = None
        bass_track_idx = None
        max_bass_notes = 0
        
        for idx, t in enumerate(tracks):
            if t['channel'] == 9 or t['channel'] == 999:  # Skip drums and meta
                continue
            
            bass_count = 0
            total_notes = 0
            
            for msg in t['track']:
                if msg.type == 'note_on' and hasattr(msg, 'note'):
                    total_notes += 1
                    if msg.note < 48:  # Below C3
                        bass_count += 1
            
            # If more than 50% of notes are below C3, it's likely a bass track
            if total_notes > 0:
                bass_ratio = bass_count / total_notes
                if bass_ratio > 0.5 and bass_count > max_bass_notes:
                    max_bass_notes = bass_count
                    bass_track = t
                    bass_track_idx = idx
        
        # If bass track found, move it to channel 1
        if bass_track is not None and bass_track['channel'] != 1:
            old_ch = bass_track['channel']
            
            # Check if there's already a track on channel 1
            channel_1_track = None
            channel_1_idx = None
            for idx, t in enumerate(tracks):
                if t['channel'] == 1 and idx != bass_track_idx:
                    channel_1_track = t
                    channel_1_idx = idx
                    break
            
            # If channel 1 is occupied, swap the channels
            if channel_1_track is not None:
                # Swap channels
                for msg in bass_track['track']:
                    if hasattr(msg, 'channel'):
                        msg.channel = 1
                
                for msg in channel_1_track['track']:
                    if hasattr(msg, 'channel'):
                        msg.channel = old_ch
                
                # Update track info
                bass_track['moved_from'] = old_ch
                bass_track['channel'] = 1
                bass_track['is_bass'] = True
                
                channel_1_track['swapped_from'] = 1
                channel_1_track['channel'] = old_ch
            else:
                # Channel 1 is free, just move bass there
                for msg in bass_track['track']:
                    if hasattr(msg, 'channel'):
                        msg.channel = 1
                
                bass_track['moved_from'] = old_ch
                bass_track['channel'] = 1
                bass_track['is_bass'] = True
        
        return tracks
    
    def convert_type0_to_type1(self, mid):
        """
        Convert Type 0 MIDI file to Type 1 by separating channels into tracks
        """
        # Create new Type 1 MIDI file
        new_mid = mido.MidiFile(type=1)
        new_mid.ticks_per_beat = mid.ticks_per_beat
        
        # Type 0 has only one track, separate by channels
        original_track = mid.tracks[0]
        
        # Collect messages by channel
        channel_messages = [[] for _ in range(16)]  # 16 MIDI channels
        meta_messages = []
        
        # Convert to absolute time first
        current_time = 0
        for msg in original_track:
            current_time += msg.time
            
            # Meta messages go to all tracks
            if msg.is_meta:
                meta_messages.append((current_time, msg.copy()))
            else:
                # Regular messages get sorted by channel
                if hasattr(msg, 'channel'):
                    channel_messages[msg.channel].append((current_time, msg.copy(time=0)))
        
        # Create meta track (tempo, time signature, etc.)
        if meta_messages:
            meta_track = mido.MidiTrack()
            last_time = 0
            for abs_time, msg in meta_messages:
                # Convert back to delta time
                msg.time = abs_time - last_time
                meta_track.append(msg)
                last_time = abs_time
            new_mid.tracks.append(meta_track)
        
        # Create a track for each channel that has messages
        for channel in range(16):
            if channel_messages[channel]:
                track = mido.MidiTrack()
                last_time = 0
                
                # Sort by time (should already be sorted, but just in case)
                channel_messages[channel].sort(key=lambda x: x[0])
                
                for abs_time, msg in channel_messages[channel]:
                    # Convert absolute time back to delta time
                    msg.time = abs_time - last_time
                    track.append(msg)
                    last_time = abs_time
                
                # Add end of track
                track.append(mido.MetaMessage('end_of_track', time=0))
                new_mid.tracks.append(track)
        
        return new_mid
    
    def process_files(self, midi_files):
        """Process list of MIDI files"""
        self.log(f"Found {len(midi_files)} MIDI file(s)")
        
        # Create output folders in same location as first file
        first_file = Path(midi_files[0])
        output_folder_type0 = first_file.parent / "Type0_Converted"
        output_folder_type1 = first_file.parent / "Type1_Top5"
        output_folder_type0.mkdir(exist_ok=True)
        output_folder_type1.mkdir(exist_ok=True)
        
        self.log(f"Type 0 output: {output_folder_type0}")
        self.log(f"Type 1 output: {output_folder_type1}")
        self.log(f"Settings: Keep top {self.max_tracks} tracks, "
                f"minimum {self.min_events} events\n")
        
        # Stats
        type0_count = 0
        type1_count = 0
        trimmed_count = 0
        skipped_count = 0
        removed_empty_count = 0
        
        for midi_file in midi_files:
            try:
                mid = mido.MidiFile(midi_file)
                
                # Handle Type 0 - convert to Type 1 first
                if mid.type == 0:
                    type0_count += 1
                    self.log(f"📝 {midi_file.name}: Converting Type 0 to Type 1...")
                    mid = self.convert_type0_to_type1(mid)
                    output_folder = output_folder_type0
                    
                elif mid.type == 1:
                    type1_count += 1
                    output_folder = output_folder_type1
                    
                else:
                    skipped_count += 1
                    self.log(f"○ {midi_file.name}: Skipped (Type {mid.type})")
                    continue
                
                # Now process as Type 1 (whether converted or original)
                original_tracks = len(mid.tracks)
                
                # Count events for each track
                track_info = []
                for i, track in enumerate(mid.tracks):
                    event_count = self.count_track_events(track)
                    track_info.append({
                        'index': i,
                        'track': track,
                        'events': event_count
                    })
                
                # Filter out tracks with too few events
                substantial_tracks = [t for t in track_info 
                                    if t['events'] >= self.min_events]
                
                removed_empty = len(track_info) - len(substantial_tracks)
                if removed_empty > 0:
                    removed_empty_count += removed_empty
                
                # Sort by event count (descending) and keep top N
                substantial_tracks.sort(key=lambda x: x['events'], reverse=True)
                top_tracks = substantial_tracks[:self.max_tracks]
                
                # Get channel for each track
                for t in top_tracks:
                    t['channel'] = self.get_track_channel(t['track'])
                
                # Standardize channels to 0,1,2,3,9
                top_tracks = self.standardize_channels(top_tracks)
                
                # Detect bass and move to channel 1
                top_tracks = self.detect_bass_track(top_tracks)
                
                # Now sort the top tracks by channel number for organized display
                top_tracks.sort(key=lambda x: x['channel'])
                
                # Log track information
                # Check if any remapping occurred
                any_remapped = any('old_channel' in t for t in top_tracks)
                bass_detected = any('is_bass' in t for t in top_tracks)
                
                if len(top_tracks) < original_tracks or any_remapped or bass_detected:
                    self.log(f"✓ {midi_file.name}:")
                    if len(top_tracks) < original_tracks:
                        self.log(f"   Original: {original_tracks} tracks → Kept: {len(top_tracks)}")
                    else:
                        self.log(f"   Tracks: {len(top_tracks)} (no trimming needed)")
                    if removed_empty > 0:
                        self.log(f"   Removed {removed_empty} tracks with < {self.min_events} events")
                    if bass_detected:
                        self.log(f"   🎸 Bass detected and moved to channel 1 (device ch 2)")
                    self.log(f"   Channel assignment (standardized to 0,1,2,3,9):")
                    for i, t in enumerate(top_tracks, 1):
                        ch = t['channel'] if t['channel'] != 999 else 'Meta'
                        label = ""
                        if 'is_bass' in t:
                            label = " [BASS]"
                        elif 'old_channel' in t:
                            label = f" [remapped from {t['old_channel']}]"
                        elif 'moved_from' in t:
                            label = f" [moved from channel {t['moved_from']}]"
                        elif 'swapped_from' in t:
                            label = f" [swapped from channel {t['swapped_from']}]"
                        self.log(f"      #{i}: Channel {ch} ({t['events']} events){label}")
                    if len(top_tracks) < original_tracks:
                        trimmed_count += 1
                else:
                    self.log(f"✓ {midi_file.name}: "
                            f"{len(top_tracks)} tracks, already using standard channels")
                
                # Create new MIDI file with only top tracks
                new_mid = mido.MidiFile(type=1)
                new_mid.ticks_per_beat = mid.ticks_per_beat
                
                # Add the top tracks in order of event count
                for t in top_tracks:
                    new_mid.tracks.append(t['track'])
                
                # Save to appropriate folder
                output_file = output_folder / midi_file.name
                new_mid.save(output_file)
                    
            except Exception as e:
                self.log(f"✗ {midi_file.name}: Error - {e}")
                skipped_count += 1
        
        # Summary
        self.log("\n" + "="*60)
        self.log("SUMMARY:")
        self.log(f"  Total files: {len(midi_files)}")
        self.log(f"  Type 0 converted: {type0_count}")
        self.log(f"  Type 1 processed: {type1_count}")
        self.log(f"  Files trimmed: {trimmed_count}")
        self.log(f"  Empty tracks removed: {removed_empty_count}")
        self.log(f"  Skipped: {skipped_count}")
        self.log(f"  Type 0 output: {output_folder_type0}")
        self.log(f"  Type 1 output: {output_folder_type1}")
        self.log("="*60)
        self.log("✅ Done!\n")

def main():
    root = tk.Tk()
    app = MIDIFilterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
