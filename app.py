import os
import sys
import threading
import subprocess
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog
from audio_recorder import AudioRecorder
from pipeline import AudioPipeline

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Spotify to MIDI Converter")
        self.geometry("600x550")
        
        self.output_dir = Path.home() / "Music" / "SpotifyMidi"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.recorder = AudioRecorder()
        self.current_recording_path = None
        self.current_piano_path = None
        self.current_midi_path = None
        
        self.setup_ui()

    def setup_ui(self):
        # Title Label
        self.title_label = ctk.CTkLabel(self, text="Spotify Piano to MIDI", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        # Output Directory Selection
        self.dir_frame = ctk.CTkFrame(self)
        self.dir_frame.pack(pady=10, padx=20, fill="x")
        
        self.dir_label = ctk.CTkLabel(self.dir_frame, text=f"Output: {self.output_dir}", font=ctk.CTkFont(size=12))
        self.dir_label.pack(side="left", padx=10, pady=10)
        
        self.dir_button = ctk.CTkButton(self.dir_frame, text="Change", command=self.change_dir, width=80)
        self.dir_button.pack(side="right", padx=10, pady=10)

        # Settings
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.pack(pady=(0, 10), padx=20, fill="x")
        
        self.device_label = ctk.CTkLabel(self.settings_frame, text="Processing Mode:")
        self.device_label.pack(side="left", padx=10, pady=10)
        
        self.device_var = ctk.StringVar(value="Auto (NVIDIA GPU)")
        self.device_menu = ctk.CTkOptionMenu(self.settings_frame, values=["Auto (NVIDIA GPU)", "CPU (Integrated Graphics)"], variable=self.device_var)
        self.device_menu.pack(side="left", padx=10, pady=10)

        # Controls
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.pack(pady=10, padx=20, fill="x")
        
        self.record_btn = ctk.CTkButton(self.controls_frame, text="● Record", fg_color="red", hover_color="darkred", command=self.start_recording)
        self.record_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.stop_btn = ctk.CTkButton(self.controls_frame, text="■ Stop", state="disabled", command=self.stop_recording)
        self.stop_btn.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.open_btn = ctk.CTkButton(self.controls_frame, text="📂 Open Audio or MIDI...", command=self.open_file)
        self.open_btn.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        self.sep_btn = ctk.CTkButton(self.controls_frame, text="1. Separate Stems", fg_color="blue", hover_color="darkblue", state="disabled", command=self.separate_stems)
        self.sep_btn.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.midi_btn = ctk.CTkButton(self.controls_frame, text="2. Convert to MIDI", fg_color="green", hover_color="darkgreen", state="disabled", command=self.convert_to_midi)
        self.midi_btn.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        self.vis_btn = ctk.CTkButton(self.controls_frame, text="3. Visualize MIDI", fg_color="purple", hover_color="darkmagenta", state="disabled", command=self.visualize_midi)
        self.vis_btn.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        self.controls_frame.columnconfigure(0, weight=1)
        self.controls_frame.columnconfigure(1, weight=1)

        # Log Output
        self.log_box = ctk.CTkTextbox(self, state="disabled", height=150)
        self.log_box.pack(pady=10, padx=20, fill="both", expand=True)
        self.log_message("Ready. Press 'Start Recording' when Spotify is playing.")

        # Check for venv automatically on startup
        self.after(1000, self.check_and_install_venv)

    def log_message(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def change_dir(self):
        new_dir = filedialog.askdirectory(initialdir=self.output_dir)
        if new_dir:
            self.output_dir = Path(new_dir)
            self.dir_label.configure(text=f"Output: {self.output_dir}")

    def lock_buttons(self):
        self.record_btn.configure(state="disabled")
        self.open_btn.configure(state="disabled")
        self.sep_btn.configure(state="disabled")
        self.midi_btn.configure(state="disabled")
        self.vis_btn.configure(state="disabled")

    def unlock_buttons(self):
        self.record_btn.configure(state="normal")
        self.open_btn.configure(state="normal")
        if self.current_recording_path or self.current_piano_path:
            self.sep_btn.configure(state="normal")
            self.midi_btn.configure(state="normal")
        if self.current_midi_path:
            self.vis_btn.configure(state="normal")

    def check_and_install_venv(self):
        base_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
        venv_dir = base_dir / "venv311"
        if not venv_dir.exists():
            self.lock_buttons()
            self.log_message("First run detected! Setting up the machine learning environment...")
            self.log_message("This will download several gigabytes and take a few minutes.")
            threading.Thread(target=self.run_venv_setup, args=(base_dir, venv_dir), daemon=True).start()

    def run_venv_setup(self, base_dir, venv_dir):
        try:
            req_file = base_dir / "requirements.txt"
            if not req_file.exists():
                self.after(0, self.log_message, "Error: requirements.txt not found! Cannot setup environment automatically.")
                return

            self.after(0, self.log_message, f"Creating Python 3.11 virtual environment at {venv_dir.name}...")
            try:
                creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
                subprocess.run(["py", "-3.11", "-m", "venv", str(venv_dir)], check=True, capture_output=True, creationflags=creationflags)
            except subprocess.CalledProcessError:
                subprocess.run(["python", "-m", "venv", str(venv_dir)], check=True, capture_output=True, creationflags=creationflags)
                
            python_exe = venv_dir / "Scripts" / "python.exe"
            
            self.after(0, self.log_message, "Installing uv package manager...")
            subprocess.run([str(python_exe), "-m", "pip", "install", "uv"], check=True, capture_output=True, creationflags=creationflags)
            
            uv_exe = venv_dir / "Scripts" / "uv.exe"
            
            self.after(0, self.log_message, "Downloading and installing ML models (Demucs, Basic Pitch)...")
            result = subprocess.run([str(uv_exe), "pip", "install", "-r", str(req_file)], capture_output=True, text=True, creationflags=creationflags)
            if result.returncode != 0:
                self.after(0, self.log_message, f"Installation failed. See terminal for details or run manually.")
            else:
                self.after(0, self.log_message, "Environment setup complete! The application is fully ready to use.")
        except Exception as e:
            self.after(0, self.log_message, f"Setup error: {str(e)}")
        finally:
            self.after(0, self.unlock_buttons)

    def start_recording(self):
        if not self.recorder.wasapi_info:
            self.log_message("Error: WASAPI loopback not available.")
            return

        self.current_recording_path = self.output_dir / "recorded_track.wav"
        success = self.recorder.start_recording(str(self.current_recording_path))
        
        if success:
            self.lock_buttons()
            self.stop_btn.configure(state="normal")
            self.log_message(f"Recording started... capturing system audio to {self.current_recording_path.name}")
        else:
            self.log_message("Failed to start recording.")

    def stop_recording(self):
        self.stop_btn.configure(state="disabled")
        self.log_message("Stopping recording...")
        
        captured_audio = self.recorder.stop_recording()
        if not captured_audio:
            self.log_message("Warning: No audio frames detected! Please make sure music is actively playing. A silent file was saved.")
        else:
            self.log_message("Recording saved. Ready to process.")
            
        self.current_piano_path = None
        self.unlock_buttons()

    def open_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=self.output_dir,
            title="Select Audio or MIDI File",
            filetypes=(("Audio/MIDI files", "*.wav *.mid *.midi"), ("All files", "*.*"))
        )
        if file_path:
            path = Path(file_path)
            self.lock_buttons()
            if path.suffix.lower() in ['.mid', '.midi']:
                self.current_midi_path = path
                self.current_recording_path = None
                self.current_piano_path = None
                self.log_message(f"Loaded MIDI: {path.name}. Ready to visualize.")
            else:
                self.current_recording_path = path
                self.current_piano_path = None
                self.current_midi_path = None
                self.log_message(f"Loaded Audio: {path.name}. Ready to process.")
            self.unlock_buttons()

    def separate_stems(self):
        if not self.current_recording_path or not self.current_recording_path.exists():
            self.log_message("Error: No audio file selected or recorded.")
            return
            
        self.lock_buttons()
        self.log_message(f"Starting Demucs separation for {self.current_recording_path.name}...")
        threading.Thread(target=self.run_separate, daemon=True).start()

    def run_separate(self):
        pipeline = AudioPipeline(str(self.output_dir))
        device_choice = "cpu" if "CPU" in self.device_var.get() else "auto"
        success, piano_path = pipeline.separate_stems(self.current_recording_path, progress_callback=lambda m: self.after(0, self.log_message, m), device=device_choice)
        if success and piano_path:
            self.current_piano_path = piano_path
        self.after(0, self.finish_task)

    def convert_to_midi(self):
        target_path = self.current_piano_path if self.current_piano_path else self.current_recording_path
        if not target_path or not target_path.exists():
            self.log_message("Error: No audio file selected.")
            return
            
        self.lock_buttons()
        self.log_message(f"Starting MIDI conversion for {target_path.name}...")
        threading.Thread(target=self.run_midi, args=(target_path,), daemon=True).start()

    def run_midi(self, target_path):
        pipeline = AudioPipeline(str(self.output_dir))
        track_name = self.current_recording_path.stem if self.current_recording_path else target_path.stem
        device_choice = "cpu" if "CPU" in self.device_var.get() else "auto"
        success = pipeline.convert_to_midi(target_path, progress_callback=lambda m: self.after(0, self.log_message, m), track_name=track_name, device=device_choice)
        if success:
            self.current_midi_path = self.output_dir / f"{track_name}_piano.mid"
        self.after(0, self.finish_task)

    def visualize_midi(self):
        if not self.current_midi_path or not self.current_midi_path.exists():
            self.log_message("Error: No MIDI file selected.")
            return
            
        self.lock_buttons()
        self.log_message(f"Generating visual representation for {self.current_midi_path.name}...")
        threading.Thread(target=self.run_visualize, daemon=True).start()

    def run_visualize(self):
        try:
            from visualize_midi import generate_midi_text
            text = generate_midi_text(self.current_midi_path)
            notes_path = self.current_midi_path.with_name(f"{self.current_midi_path.stem}_notes.txt")
            notes_path.write_text(text, encoding='utf-8')
            self.after(0, self.log_message, f"Saved visualization to: {notes_path.name}")
            
            os.startfile(notes_path)
        except Exception as e:
            self.after(0, self.log_message, f"Visualization Error: {e}")
            
        self.after(0, self.finish_task)

    def finish_task(self):
        self.unlock_buttons()
        self.stop_btn.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()
