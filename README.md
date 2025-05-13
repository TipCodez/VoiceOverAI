# Audiora - Offline Text-to-Speech App (pyttsx3)

This is the offline version of **Audiora**, a beautiful, modern text-to-speech (TTS) application built with Python and Flet. It uses the local pyttsx3 engine, so you can generate speech without an internet connection.

## Features
- Convert text to speech using your system's voices (offline)
- Choose from all available system voices
- Select moods (simulated with speed/volume presets)
- Adjust speech speed
- Save and play multiple generated audio files
- Download audio files to your desktop
- **Delete unwanted audio files from the dropdown and disk**
- Highlight words as they are spoken
- Beautiful, animated, and modern UI
- Exit button to close the app
- **Robust audio playback controls:** play, pause (stop), and resume (replay) any audio file

## Installation
1. **Clone the repository or download the source code.**
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Mac/Linux:
   source .venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   - For mp3 export, you also need ffmpeg installed and in your PATH (for pydub).

## Usage
1. **Run the app:**
   ```bash
   python main.py
   ```
2. **Enter your text, select voice/mood, and click 'Generate Voice'.**
3. **Play, pause, resume, download, or delete any generated audio from the dropdown.**
4. **Use the dropdown to select and play any previously generated audio.**
5. **Click 'Exit' to close Audiora.**

## Requirements
- Python 3.8+
- No internet required for TTS generation
- System voices (install more voices via your OS settings for more options)
- ffmpeg (for mp3 export, optional)

## Notes
- Moods are simulated by adjusting speed and volume. For true expressive/emotional TTS, consider using Coqui TTS.
- Audio files are saved in the `offline_audio` directory and can be downloaded to your desktop.
- You can delete any audio file you no longer want directly from the app.

## Troubleshooting
- **Audio does not play:** Ensure the file exists and is not corrupted. Try generating a new audio file.
- **Pause/Resume:** Pause stops playback. Resume replays the audio from the start (true resume is not supported in Flet).
- **Delete:** If you delete an audio file, it is removed from both the dropdown and disk.

## License
MIT License 