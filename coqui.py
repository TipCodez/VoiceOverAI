# Imports
import flet as ft
from flet_audio import audio
import requests
import os
from murf import Murf
# from api_key import API_KEY
import math
import time
import threading
import json
import sys
import datetime

# API Client
client = Murf(api_key="ap2_8051e08c-7fcc-4b99-9d84-ba9c5df2328b")
# client = Murf(api_key=API_KEY)

voices = client.text_to_speech.get_voices()
for voice in voices:
    print(f"Voice ID: {voice.voice_id}, Name: {voice.display_name}, Moods: {voice.available_styles}")

# Voice Settings
VOICE_MOODS = {
    "Miles": {
        "voice_id": "en-US-miles",
        "moods": ['Conversational', 'Promo', 'Sports Commentary', 'Narration', 'Newscast', 'Sad', 'Angry', 'Calm',
                  'Terrified', 'Inspirational', 'Pirate']
    },
    "Shane": {
        "voice_id": "en-AU-shane",
        "moods": ['Conversational', 'Narration']
    },
    "Natalie": {
        "voice_id": "en-US-natalie",
        "moods": ['Promo', 'Narration', 'Newscast Formal', 'Meditative', 'Sad', 'Angry', 'Conversational',
                  'Newscast Casual', 'Furious', 'Sorrowful', 'Terrified', 'Inspirational']
    }
}


# Build the Flet App
def main(page: ft.Page):
    page.title = "AI TipKode"
    page.padding = 40
    page.bgcolor = "#1E1E2F"

    # Create the UI Widgets
    title = ft.Text("AI TipKode", size=42, weight=ft.FontWeight.BOLD, color="#FFD700")

    text_input = ft.TextField(
        label="Enter some text here...",
        width=350,
        bgcolor="#2A2A3B",
        color="#ffffff",
        border_radius=15,
        border_color="#FFD700"
    )

    voice_selection = ft.Dropdown(
        label="Choose Voice",
        options=[ft.dropdown.Option(voice) for voice in VOICE_MOODS.keys()],
        width=350,
        bgcolor="#2A2A3B",
        color="#ffffff",
        value="Miles"
    )

    mood_selection = ft.Dropdown(
        label="Choose Mood",
        width=350,
        bgcolor="#2A2A3B",
        color="#ffffff"
    )

    def update_moods(e=None):
        selected_voice = voice_selection.value
        mood_selection.options = [
            ft.dropdown.Option(mood) for mood in VOICE_MOODS.get(selected_voice, {}).get("moods", [])
        ]
        mood_selection.value = mood_selection.options[0].text if mood_selection.options else None
        page.update()

    voice_selection.on_change = update_moods
    update_moods()

    voice_speed = ft.Slider(
        min=-30, max=30, value=0, divisions=10, label="{value}%", active_color="#FFD700"
    )

    # Generate AI Voice
    def generate_audio():
        selected_voice = voice_selection.value
        voice_id = VOICE_MOODS.get(selected_voice, {}).get("voice_id")

        if not text_input.value.strip():
            status_text.current = "ERROR: you need some text..."
            print("ERROR: you need some text...")
            page.update()
            return None

        try:
            print(f"Generating audio for text: {text_input.value}")
            response = client.text_to_speech.generate(
                format="MP3",
                sample_rate=48000.0,
                channel_type="STEREO",
                text=text_input.value,
                voice_id=voice_id,
                style=mood_selection.value,
                pitch=voice_speed.value
            )
            print(f"Murf API response: {response}")
            audio_url = getattr(response, 'audio_file', None)
            print(f"Audio URL: {audio_url}")
            return audio_url
        except Exception as e:
            print(f"Error: {e}")
            status_text.current = f"Error generating audio: {e}"
            page.update()
            return None

    # Define assets directory for audio
    ASSETS_DIR = "Murf-x-flet-main/Murf-x-flet-main/AI_Flet_Speech"
    AUDIO_FILENAME = "audio.mp3"
    AUDIO_PATH = os.path.join(ASSETS_DIR, AUDIO_FILENAME)
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)

    # Audio player reference
    audio_player = ft.Audio(src=AUDIO_FILENAME, autoplay=False)
    page.overlay.append(audio_player)

    # Word highlighting state
    highlighted_word_index = ft.Ref()
    highlighted_word_index.current = None
    word_spans = ft.Ref()
    word_spans.current = None

    SETTINGS_FILE = "settings.json"

    # Load settings from file if exists
    def load_settings():
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    app_settings.update(data)
            except Exception as e:
                print(f"Failed to load settings: {e}")
                status_text.current = f"Failed to load settings: {e}"
                page.update()

    # Save settings to file
    def save_settings():
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(app_settings, f)
        except Exception as e:
            print(f"Failed to save settings: {e}")
            status_text.current = f"Failed to save settings: {e}"
            page.update()

    # Settings state
    app_settings = {
        "theme": "dark",
        "default_voice": "Miles",
        "default_mood": VOICE_MOODS["Miles"]["moods"][0],
        "default_pitch": 0,
    }

    def apply_theme():
        if app_settings["theme"] == "dark":
            page.bgcolor = "#1E1E2F"
            input_container.bgcolor = "#2A2A3B"
            title.color = "#FFD700"
        else:
            page.bgcolor = "#F5F5F5"
            input_container.bgcolor = "#FFFFFF"
            title.color = "#23234A"
        page.update()

    def on_theme_change(e):
        app_settings["theme"] = e.control.value
        apply_theme()
        save_settings()

    def on_default_voice_change(e):
        app_settings["default_voice"] = e.control.value
        voice_selection.value = e.control.value
        update_moods()
        mood_selection.value = VOICE_MOODS[voice_selection.value]["moods"][0]
        app_settings["default_mood"] = mood_selection.value
        page.update()
        save_settings()

    def on_default_mood_change(e):
        app_settings["default_mood"] = e.control.value
        mood_selection.value = e.control.value
        page.update()
        save_settings()

    def on_default_pitch_change(e):
        app_settings["default_pitch"] = e.control.value
        voice_speed.value = e.control.value
        page.update()
        save_settings()

    # Load settings at startup
    load_settings()

    # --- Smooth highlight transitions for words ---
    def build_word_spans():
        words = text_input.value.split()
        spans = []
        for i, word in enumerate(words):
            is_highlighted = highlighted_word_index.current == i
            color = "#FFD700" if is_highlighted else "#ffffff"
            weight = ft.FontWeight.BOLD if is_highlighted else ft.FontWeight.NORMAL
            size = 22 if is_highlighted else 20
            spans.append(
                ft.Text(
                    word + (" " if i < len(words) - 1 else ""),
                    style=ft.TextStyle(color=color, weight=weight, size=size)
                )
            )
        return ft.Row(spans, wrap=True)

    def update_word_highlight(idx):
        highlighted_word_index.current = idx
        word_spans.current = build_word_spans()
        page.update()

    def reset_word_highlight():
        highlighted_word_index.current = None
        word_spans.current = build_word_spans()
        page.update()

    def on_text_input_change(e):
        reset_word_highlight()
        on_input_change(e)

    text_input.on_change = on_text_input_change

    # Thread-safe flag for word highlighting
    highlighting_active = threading.Event()

    # List to keep track of generated audio files
    generated_audios = []
    selected_audio = ft.Ref()

    # Dropdown for selecting audio files
    audio_dropdown = ft.Dropdown(
        label="Select Audio",
        options=[],
        width=350,
        bgcolor="#2A2A3B",
        color="#FFD700",
        on_change=lambda e: select_audio_file(e.control.value)
    )

    def select_audio_file(filename):
        if filename and os.path.exists(os.path.join(ASSETS_DIR, filename)):
            audio_player.src = filename
            selected_audio.current = filename
            page.update()
        else:
            status_text.current = "Selected audio file not found."
            page.update()

    # Audio control functions
    def play_audio(e=None):
        # Always set the audio source to the selected audio file and play
        filename = selected_audio.current or (generated_audios[-1] if generated_audios else None)
        if filename and os.path.exists(os.path.join(ASSETS_DIR, filename)):
            audio_player.src = filename
            audio_player.autoplay = True
            page.update()
            highlighting_active.set()
            threading.Thread(target=highlight_words_during_audio, daemon=True).start()
        else:
            status_text.current = "No audio file to play. Generate or select audio first."
            page.update()

    def pause_audio(e=None):
        audio_player.pause()
        highlighting_active.clear()
        page.update()

    def unpause_audio(e=None):
        audio_player.resume()
        highlighting_active.set()
        page.update()
        threading.Thread(target=highlight_words_during_audio, daemon=True).start()

    def download_audio(e=None):
        # Save selected audio to user's desktop
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        filename = selected_audio.current or (generated_audios[-1] if generated_audios else None)
        if not filename:
            status_text.current = "No audio file to download."
            page.update()
            return
        src = os.path.join(ASSETS_DIR, filename)
        dst = os.path.join(desktop, f"AI_TipKode_{filename}")
        try:
            if os.path.exists(src):
                with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
                    fdst.write(fsrc.read())
                status_text.current = f"Audio downloaded to {dst}"
            else:
                status_text.current = "No audio file to download."
        except Exception as ex:
            print(f"Download error: {ex}")
            status_text.current = f"Download error: {ex}"
        page.update()

    # Exit button function
    def exit_app(e=None):
        page.window_close()

    # State to track if audio is loaded
    audio_loaded = ft.Ref()
    audio_loaded.current = False
    loading_indicator = ft.ProgressRing(visible=False, color="#FFD700")
    status_text = ft.Text("", color="#FFD700")

    def set_audio_controls_enabled(enabled):
        btn_play.disabled = not enabled
        btn_pause.disabled = not enabled
        btn_unpause.disabled = not enabled
        btn_download.disabled = not enabled
        page.update()

    # Update save_and_play to save audio with a unique filename and update dropdown
    def save_and_play(e):
        loading_indicator.visible = True
        status_text.current = "Generating audio..."
        set_audio_controls_enabled(False)
        page.update()
        audio_url = generate_audio()
        if not audio_url:
            status_text.current = "Error: No audio found."
            print("Error: No audio found.")
            loading_indicator.visible = False
            set_audio_controls_enabled(False)
            page.update()
            return

        try:
            print(f"Downloading audio from: {audio_url}")
            # Generate a unique filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"audio_{timestamp}.mp3"
            unique_path = os.path.join(ASSETS_DIR, unique_filename)
            response = requests.get(audio_url, stream=True, timeout=30)
            if response.status_code == 200:
                try:
                    with open(unique_path, "wb") as file:
                        for chunk in response.iter_content(chunk_size=1024):
                            file.write(chunk)
                    print(f"Audio saved to: {unique_path}")
                    print(
                        f"File exists: {os.path.exists(unique_path)}, Size: {os.path.getsize(unique_path) if os.path.exists(unique_path) else 0} bytes")
                except Exception as file_err:
                    status_text.current = f"Error saving audio: {file_err}"
                    print(f"Error saving audio: {file_err}")
                    loading_indicator.visible = False
                    set_audio_controls_enabled(False)
                    page.update()
                    return
                # Add to list and update dropdown
                generated_audios.append(unique_filename)
                audio_dropdown.options = [ft.dropdown.Option(f) for f in generated_audios]
                audio_dropdown.value = unique_filename
                selected_audio.current = unique_filename
                audio_player.src = unique_filename
                audio_player.autoplay = True
                audio_loaded.current = True
                status_text.current = "Audio ready!"
                print("Audio ready and should play now.")
                set_audio_controls_enabled(True)
            else:
                status_text.current = f"Failed to get audio: {response.status_code}"
                print(f"Failed to get audio: {response.status_code}")
                audio_loaded.current = False
                set_audio_controls_enabled(False)
            loading_indicator.visible = False
            page.update()
        except Exception as e:
            print("ERROR", e)
            status_text.current = f"Error downloading audio: {e}"
            loading_indicator.visible = False
            audio_loaded.current = False
            set_audio_controls_enabled(False)
            page.update()

    # Regenerate audio when text, voice, or mood changes (user must click Generate Voice)
    def on_input_change(e):
        audio_loaded.current = False
        set_audio_controls_enabled(False)
        status_text.current = ""
        page.update()

    text_input.on_change = on_input_change
    voice_selection.on_change = lambda e: (update_moods(), on_input_change(e))
    mood_selection.on_change = on_input_change

    # Audio control buttons (redefine to use disabled state)
    btn_play = ft.IconButton(icon=ft.icons.PLAY_ARROW, tooltip="Play", on_click=play_audio, icon_color="#FFD700",
                             disabled=True)
    btn_pause = ft.IconButton(icon=ft.icons.PAUSE, tooltip="Pause", on_click=pause_audio, icon_color="#FFD700",
                              disabled=True)
    btn_unpause = ft.IconButton(icon=ft.icons.REPLAY, tooltip="Unpause", on_click=unpause_audio, icon_color="#FFD700",
                                disabled=True)
    btn_download = ft.IconButton(icon=ft.icons.DOWNLOAD, tooltip="Download", on_click=download_audio,
                                 icon_color="#FFD700", disabled=True)

    # enter_button
    btn_enter = ft.ElevatedButton(
        "Generate Voice",
        bgcolor="#FFD700",
        color="#1E1E2F",
        on_click=save_and_play,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))
    )

    # Add Exit button
    btn_exit = ft.ElevatedButton(
        "Exit",
        bgcolor="#FFD700",
        color="#1E1E2F",
        on_click=exit_app,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))
    )

    # Gradient background (using a Container with a gradient)
    gradient_bg = ft.Container(
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#1E1E2F", "#23234A", "#FFD700"],
        ),
    )

    # Settings panel (expanded)
    settings_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD, color="#FFD700"),
        content=ft.Column([
            ft.Text("Theme", color="#FFD700"),
            ft.Dropdown(
                options=[ft.dropdown.Option("dark"), ft.dropdown.Option("light")],
                value=app_settings["theme"],
                on_change=on_theme_change,
                width=200,
                bgcolor="#2A2A3B",
                color="#FFD700"
            ),
            ft.Text("Default Voice", color="#FFD700"),
            ft.Dropdown(
                options=[ft.dropdown.Option(v) for v in VOICE_MOODS.keys()],
                value=app_settings["default_voice"],
                on_change=on_default_voice_change,
                width=200,
                bgcolor="#2A2A3B",
                color="#FFD700"
            ),
            ft.Text("Default Mood", color="#FFD700"),
            ft.Dropdown(
                options=[ft.dropdown.Option(m) for m in VOICE_MOODS[app_settings["default_voice"]]["moods"]],
                value=app_settings["default_mood"],
                on_change=on_default_mood_change,
                width=200,
                bgcolor="#2A2A3B",
                color="#FFD700"
            ),
            ft.Text("Default Pitch", color="#FFD700"),
            ft.Slider(
                min=-30, max=30, value=app_settings["default_pitch"], divisions=10, label="{value}%",
                active_color="#FFD700",
                on_change=on_default_pitch_change
            ),
        ], spacing=10),
        actions=[ft.TextButton("Close", on_click=lambda e: page.dialog.close())],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_settings(e):
        page.dialog = settings_dialog
        settings_dialog.open = True
        page.update()

    btn_settings = ft.IconButton(
        icon=ft.icons.SETTINGS,
        tooltip="Settings",
        on_click=open_settings,
        icon_color="#FFD700",
        disabled=False
    )

    # Button hover style
    button_style = ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=15),
        color="#1E1E2F",
        bgcolor="#FFD700"
    )
    btn_enter.style = button_style

    # IconButton style (for main controls)
    for btn in [btn_play, btn_pause, btn_unpause, btn_download, btn_settings]:
        btn.style = ft.ButtonStyle(
            shape=ft.CircleBorder(),
        )

    # Build a UI Container
    word_spans.current = build_word_spans()
    input_container = ft.Container(
        content=ft.Column(
            controls=[word_spans.current, text_input, voice_selection, mood_selection,
                      ft.Text("Adjust Pitch", size=18, weight=ft.FontWeight.BOLD, color="#FFD700"),
                      voice_speed, btn_enter, audio_dropdown,
                      ft.Row([btn_play, btn_pause, btn_unpause, btn_download, btn_settings, btn_exit],
                             alignment=ft.MainAxisAlignment.CENTER),
                      loading_indicator, status_text
                      ],
            spacing=15,
            alignment=ft.MainAxisAlignment.CENTER
        ),
        padding=20,
        border_radius=20,
        bgcolor="#2A2A3B",
        shadow=ft.BoxShadow(blur_radius=10, spread_radius=2, color="#FFD700")
    )

    # Add gradient background and main content
    page.add(
        gradient_bg,
        ft.Column(
            controls=[title, input_container],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )
    page.update()

    # Apply theme on startup
    apply_theme()

    def highlight_words_during_audio():
        try:
            try:
                import mutagen
                from mutagen.mp3 import MP3
                audio_file = MP3(AUDIO_PATH)
                duration = audio_file.info.length
            except ImportError:
                status_text.current = "mutagen not installed, using default duration."
                duration = 3.0  # fallback
                page.update()
        except Exception as e:
            print(f"Error reading audio duration: {e}")
            duration = 3.0  # fallback
        words = text_input.value.split()
        if not words:
            return
        word_time = duration / len(words)
        for i in range(len(words)):
            if not highlighting_active.is_set():
                break
            update_word_highlight(i)
            try:
                time.sleep(word_time)
            except Exception as e:
                print(f"Error during word highlight sleep: {e}")
        reset_word_highlight()


# Run the App
if __name__ == "__main__":
    ft.app(target=main, assets_dir="Murf-x-flet-main/Murf-x-flet-main/AI_Flet_Speech")


