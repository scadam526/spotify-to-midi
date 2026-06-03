import sys
import pretty_midi
from pathlib import Path

def generate_midi_text(midi_path):
    pm = pretty_midi.PrettyMIDI(str(midi_path))
    notes = []
    for inst in pm.instruments:
        if not inst.is_drum:
            notes.extend(inst.notes)
            
    notes.sort(key=lambda x: x.start)
    
    groups = []
    current_group = []
    current_start = -1
    
    for note in notes:
        # Notes starting within 50ms of each other are grouped as a chord/simultaneous
        if current_start == -1 or note.start - current_start < 0.05:
            current_group.append(note)
            if current_start == -1:
                current_start = note.start
        else:
            groups.append((current_start, current_group))
            current_group = [note]
            current_start = note.start
            
    if current_group:
        groups.append((current_start, current_group))
        
    try:
        from music21 import chord, harmony
        has_music21 = True
    except ImportError:
        has_music21 = False

    lines = [f"MIDI Notes for: {Path(midi_path).name}", "="*40, ""]
    for start_time, group in groups:
        # Sort notes from lowest to highest pitch
        group.sort(key=lambda x: x.pitch)
        names = [pretty_midi.note_number_to_name(n.pitch) for n in group]
        
        minutes = int(start_time // 60)
        seconds = start_time % 60
        time_str = f"[{minutes:02d}:{seconds:05.2f}]"
        
        line = f"{time_str} {' + '.join(names)}"
        
        # Identify chord if 3 or more unique pitches are played simultaneously
        if has_music21 and len(set(n.pitch % 12 for n in group)) >= 3:
            try:
                # Use the lowest pitch as the bass note explicitly
                # We already sorted `group` by pitch, so `names[0]` is the bass
                unique_names = []
                seen = set()
                for n in names:
                    # music21 expects names like C#4. pretty_midi uses #.
                    if n not in seen:
                        seen.add(n)
                        unique_names.append(n)
                
                c = chord.Chord(unique_names)
                figure = harmony.chordSymbolFigureFromChord(c)
                if figure and "Cannot Be Identified" not in figure:
                    line += f"  -  {figure}"
            except Exception:
                pass
                
        lines.append(line)
        
    return "\n".join(lines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python visualize_midi.py <path_to_midi>")
        sys.exit(1)
        
    midi_path = Path(sys.argv[1])
    if not midi_path.exists():
        print(f"File not found: {midi_path}")
        sys.exit(1)
        
    text = generate_midi_text(midi_path)
    
    out_path = midi_path.with_name(f"{midi_path.stem}_notes.txt")
    out_path.write_text(text, encoding='utf-8')
    print(f"Saved visual representation to: {out_path}")
