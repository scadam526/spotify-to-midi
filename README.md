# Spotify to MIDI Converter

A graphical application that records system audio (like Spotify), separates the piano stem using Demucs, and converts the piano audio into a MIDI file using Basic Pitch, complete with intelligent chord recognition.

## Architecture

This application uses heavy machine learning libraries (PyTorch and TensorFlow). To keep the main executable small and fast, these heavy libraries are installed in a local Python virtual environment called `venv311` that sits in the same directory as the executable.

When you run `SpotifyToMidi.exe` for the first time, it will automatically look for the `venv311` directory. If it doesn't exist, it will automatically download and install the environment for you!

## Installation

### Prerequisites
- Windows 10/11
- Python 3.11 installed on your system.

### Automatic Setup (Recommended)
1. Download `SpotifyToMidi.exe` and `requirements.txt` into the same folder.
2. Double-click `SpotifyToMidi.exe`.
3. The app will detect that the ML environment is missing and automatically build `venv311` and install all required models (Demucs, Basic Pitch, TensorFlow, PyTorch).
   *Note: This initial setup downloads several gigabytes of models and may take 5-10 minutes depending on your internet connection.*

### Manual Setup (If automatic fails)
If you prefer to set up the environment manually or automatic setup fails:
1. Open a terminal in the directory containing the executable.
2. Create a virtual environment using Python 3.11: 
   ```bash
   py -3.11 -m venv venv311
   ```
3. Activate it: 
   ```bash
   venv311\Scripts\activate
   ```
4. Install `uv` (for faster installations): 
   ```bash
   pip install uv
   ```
5. Install requirements: 
   ```bash
   uv pip install -r requirements.txt
   ```

## Usage
1. Click **● Record** to start recording your system audio.
2. Play the song you want to convert on Spotify or any other application.
3. Click **■ Stop** to save the audio.
4. Click **1. Separate Stems** to isolate the piano using Demucs.
5. Click **2. Convert to MIDI** to transcribe the piano to MIDI and automatically generate a lead sheet with chord names!
