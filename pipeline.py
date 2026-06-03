import os
import sys
import subprocess
from pathlib import Path

class AudioPipeline:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Using explicit paths to the venv executables
        python_exe = sys.executable
        scripts_dir = Path(python_exe).parent
        
        self.demucs_cmd = [python_exe, "-m", "demucs.separate"]
        self.basic_pitch_cmd = [str(scripts_dir / "basic-pitch.exe")]
        
    def separate_stems(self, input_wav_path, progress_callback=None):
        input_wav = Path(input_wav_path)
        if not input_wav.exists():
            if progress_callback: progress_callback("Error: Input WAV file not found.")
            return False, None
            
        if progress_callback: progress_callback("Starting Demucs stem separation (htdemucs_6s)...")
        
        demucs_out = self.output_dir / "demucs_separated"
        demucs_out.mkdir(parents=True, exist_ok=True)
        
        demucs_args = self.demucs_cmd + ["-n", "htdemucs_6s", "--out", str(demucs_out), str(input_wav)]
        
        try:
            subprocess.run(demucs_args, capture_output=True, text=True, check=True)
            if progress_callback: progress_callback("Demucs separation completed.")
        except subprocess.CalledProcessError as e:
            if progress_callback: progress_callback(f"Demucs Error:\n{e.stderr}")
            return False, None
            
        track_name = input_wav.stem
        piano_stem_path = demucs_out / "htdemucs_6s" / track_name / "piano.wav"
        
        if not piano_stem_path.exists():
            if progress_callback: progress_callback(f"Error: Piano stem not found at {piano_stem_path}")
            return False, None
            
        # Copy the piano stem to the root output for easy listening
        final_piano_wav = self.output_dir / f"{track_name}_piano.wav"
        # Overwrite if exists
        if final_piano_wav.exists(): final_piano_wav.unlink()
        
        import shutil
        shutil.copy(piano_stem_path, final_piano_wav)
            
        return True, final_piano_wav

    def convert_to_midi(self, piano_stem_path, progress_callback=None, track_name=None):
        piano_stem_path = Path(piano_stem_path)
        if not piano_stem_path.exists():
            if progress_callback: progress_callback("Error: Piano stem WAV file not found.")
            return False
            
        if progress_callback: progress_callback("Starting Basic Pitch MIDI conversion on piano stem...")
        
        midi_out = self.output_dir
        if not track_name: track_name = piano_stem_path.parent.name
        
        bp_args = self.basic_pitch_cmd + [str(midi_out), str(piano_stem_path)]
        
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            subprocess.run(bp_args, capture_output=True, text=True, check=True, encoding="utf-8", env=env)
            if progress_callback: progress_callback("Basic Pitch conversion completed successfully!")
                
            # Basic Pitch outputs `<stem_name>_basic_pitch.mid`
            # e.g., if input is track_piano.wav, it outputs track_piano_basic_pitch.mid
            expected_midi = midi_out / f"{piano_stem_path.stem}_basic_pitch.mid"
            
            if expected_midi.exists():
                new_midi_name = midi_out / f"{track_name}_piano.mid"
                if new_midi_name.exists(): new_midi_name.unlink()
                expected_midi.rename(new_midi_name)
                
            try:
                from visualize_midi import generate_midi_text
                text = generate_midi_text(new_midi_name)
                notes_path = midi_out / f"{track_name}_piano_notes.txt"
                notes_path.write_text(text, encoding='utf-8')
            except Exception as ex:
                if progress_callback: progress_callback(f"Note Visualization Error: {ex}")
            
            if progress_callback: progress_callback(f"Done! MIDI and Notes saved to {self.output_dir}")
            return True
        except subprocess.CalledProcessError as e:
            if progress_callback: progress_callback(f"Basic Pitch Error:\n{e.stderr}")
            return False
