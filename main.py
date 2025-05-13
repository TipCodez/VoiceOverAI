import flet as ft
import pyttsx3
import os
import threading
import time
import datetime
import sys
import tempfile
# import pydub
import PyPDF2
import docx

# Setup pyttsx3 engine
engine = pyttsx3.init()
voices = engine.getProperty('voices')

# Build a list of available voices
VOICE_OPTIONS = {v.name: v.id for v in voices}

# Print all available voices for reference
print("Available voices:")
for v in voices:
    print(f"Name: {v.name}, ID: {v.id}, Lang: {getattr(v, 'languages', 'N/A')}, Gender: {getattr(v, 'gender', 'N/A')}")

# Define moods and their TTS parameter presets
MOOD_PRESETS = {
    "Neutral": {"rate": 150, "volume": 1.0},
    "Happy": {"rate": 180, "volume": 1.2},
    "Sad": {"rate": 120, "volume": 0.8},
    "Angry": {"rate": 200, "volume": 1.3},
    "Excited": {"rate": 220, "volume": 1.1},
    "Calm": {"rate": 110, "volume": 0.9},
}

# Build the Flet App
def main(page: ft.Page):
    page.title = "Audiora"
    page.padding = 40
    page.bgcolor = "#1E1E2F"

    # UI Widgets
    title = ft.Text("Audiora", size=42, weight=ft.FontWeight.BOLD, color="#FFD700")

    text_input = ft.TextField(
        label="Enter your text here...",
        width=600,
        height=100,
        multiline=True,
        max_lines=4,
        min_lines=2,
        text_align="left",
        bgcolor="#23234A",
        color="#FFD700",
        border_radius=18,
        border_color="#FFD700"
    )

    voice_selection = ft.Dropdown(
        label="Choose Voice",
        options=[ft.dropdown.Option(name) for name in VOICE_OPTIONS.keys()],
        width=350,
        bgcolor="#23234A",
        color="#FFD700",
        value=list(VOICE_OPTIONS.keys())[0]
    )

    mood_selection = ft.Dropdown(
        label="Choose Mood",
        options=[ft.dropdown.Option(mood) for mood in MOOD_PRESETS.keys()],
        width=350,
        bgcolor="#23234A",
        color="#FFD700",
        value="Neutral"
    )

    speed_slider = ft.Slider(
        min=50, max=300, value=150, divisions=10, label="{value} wpm", active_color="#FFD700"
    )

    # State
    generated_audios = []
    selected_audio = ft.Ref()
    temp_audio_path = ft.Ref()  # Store the path to the temp audio file
    audio_dropdown = ft.Dropdown(
        label="Select Audio",
        options=[],
        width=350,
        bgcolor="#23234A",
        color="#FFD700",
        on_change=lambda e: select_audio_file(e.control.value)
    )
    status_text = ft.Text("", color="#FFD700")
    loading_indicator = ft.ProgressRing(visible=False, color="#FFD700")
    highlighting_active = threading.Event()
    word_spans = ft.Ref()
    word_spans.current = None
    highlighted_word_index = ft.Ref()
    highlighted_word_index.current = None

    ASSETS_DIR = "offline_audio"
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)

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
        status_text.value = ""
        page.update()

    text_input.on_change = on_text_input_change

    def select_audio_file(filepath):
        if filepath and os.path.exists(filepath):
            selected_audio.current = filepath
            temp_audio_path.current = filepath
            page.update()
        else:
            status_text.value = "Selected audio file not found."
            page.update()

    def play_audio(e=None):
        filepath = selected_audio.current
        if filepath and os.path.exists(filepath):
            page.overlay.clear()
            page.overlay.append(file_picker)
            page.overlay.append(ft.Audio(src=filepath, autoplay=True))
            page.update()
            highlighting_active.set()
            threading.Thread(target=highlight_words_during_audio, daemon=True).start()
        else:
            status_text.value = "No audio file to play. Generate or select audio first."
            page.update()

    def pause_audio(e=None):
        # Not supported in flet_audio, but you can clear overlay
        page.overlay.clear()
        page.overlay.append(file_picker)
        highlighting_active.clear()
        page.update()

    def unpause_audio(e=None):
        play_audio()

    def download_audio(e=None):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        filepath = selected_audio.current
        if not filepath or not os.path.exists(filepath):
            status_text.value = "No audio file to download. File not found."
            page.update()
            return
        # Save to offline_audio and Desktop with a new unique filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"audio_{timestamp}.wav"
        offline_path = os.path.join(ASSETS_DIR, unique_filename)
        dst = os.path.join(desktop, f"AI_TipKode_{unique_filename}")
        try:
            # Save to offline_audio
            with open(filepath, "rb") as fsrc, open(offline_path, "wb") as fdst:
                fdst.write(fsrc.read())
            # Save to desktop
            with open(filepath, "rb") as fsrc, open(dst, "wb") as fdst:
                fdst.write(fsrc.read())
            generated_audios.append(unique_filename)
            audio_dropdown.options = [ft.dropdown.Option(text=os.path.basename(offline_path), key=offline_path)]
            audio_dropdown.value = offline_path
            selected_audio.current = offline_path
            status_text.value = f"Audio saved and downloaded to {dst}"
            temp_audio_path.current = None  # Clear temp
        except Exception as ex:
            status_text.value = f"Download error: {ex}"
        page.update()

    def delete_audio(e=None):
        filepath = selected_audio.current
        if not filepath or not os.path.exists(filepath):
            status_text.value = "No audio file selected to delete."
            page.update()
            return
        try:
            os.remove(filepath)
            # Remove from generated_audios if present
            filename = os.path.basename(filepath)
            if filename in generated_audios:
                generated_audios.remove(filename)
            status_text.value = f"Deleted {filename}"
            # Update dropdown to remove the deleted file
            remaining_files = [opt.key for opt in audio_dropdown.options if opt.key != filepath and os.path.exists(opt.key)]
            audio_dropdown.options = [ft.dropdown.Option(text=os.path.basename(f), key=f) for f in remaining_files]
            if remaining_files:
                audio_dropdown.value = remaining_files[-1]
                selected_audio.current = remaining_files[-1]
            else:
                audio_dropdown.value = None
                selected_audio.current = None
            page.overlay.clear()
            page.overlay.append(file_picker)
        except Exception as ex:
            status_text.value = f"Delete error: {ex}"
        page.update()

    def exit_app(e=None):
        try:
            page.window_close()
        except Exception:
            try:
                page.window_destroy()
            except Exception:
                page.controls.clear()
                page.add(
                    ft.Row([
                        ft.Container(
                            ft.Text("Audiora has exited. You can now close this window.", size=18, color="#FFD700"),
                            alignment=ft.alignment.center,
                            padding=10,
                            border_radius=12,
                            bgcolor="#23234A",
                            height=50,
                            shadow=ft.BoxShadow(blur_radius=8, spread_radius=2, color="#FFD700", offset=ft.Offset(0, 2)),
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
                )
                page.update()

    def save_and_play(e):
        loading_indicator.visible = True
        status_text.value = "Generating audio..."
        page.update()
        text = text_input.value.strip()
        if not text:
            status_text.value = "ERROR: you need some text..."
            loading_indicator.visible = False
            page.update()
            return

        try:
            # Use a temporary file for the audio (wav)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
                temp_audio_path.current = temp_wav.name

            # Set voice and properties
            engine.setProperty('voice', VOICE_OPTIONS[voice_selection.value])
            mood = mood_selection.value
            preset = MOOD_PRESETS.get(mood, MOOD_PRESETS["Neutral"])
            engine.setProperty('rate', int(preset["rate"]))
            engine.setProperty('volume', float(preset["volume"]))

            # Generate audio (wav)
            engine.save_to_file(text, temp_audio_path.current)
            engine.runAndWait()

            status_text.value = "Audio ready! (Not saved)"

            # Store full path as value, but show only file name in dropdown
            audio_dropdown.options = [ft.dropdown.Option(text=os.path.basename(temp_audio_path.current), key=temp_audio_path.current)]
            audio_dropdown.value = temp_audio_path.current
            selected_audio.current = temp_audio_path.current

            # Play the temp audio
            page.overlay.clear()
            page.overlay.append(file_picker)
            page.overlay.append(ft.Audio(src=temp_audio_path.current, autoplay=True))
            loading_indicator.visible = False
            page.update()
            highlighting_active.set()
            threading.Thread(target=highlight_words_during_audio, daemon=True).start()

        except Exception as ex:
            status_text.value = f"Error generating audio: {ex}"
            loading_indicator.visible = False
            page.update()

    def highlight_words_during_audio():
        words = text_input.value.split()
        if not words:
            return
        # Estimate duration: use 150 wpm as default
        duration = len(words) / (speed_slider.value / 60)
        word_time = duration / len(words)
        for i in range(len(words)):
            if not highlighting_active.is_set():
                break
            update_word_highlight(i)
            try:
                time.sleep(word_time)
            except Exception:
                pass
        reset_word_highlight()

    # FilePicker for importing text
    def on_file_selected(ev):
        file_path = ev.files[0].path if ev.files else None
        if not file_path:
            status_text.value = "No file selected."
            page.update()
            return
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text_input.value = f.read()
            elif ext == '.docx':
                doc = docx.Document(file_path)
                text_input.value = '\n'.join([p.text for p in doc.paragraphs])
            elif ext == '.pdf':
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ''
                    for page_ in reader.pages:
                        text += page_.extract_text() or ''
                    text_input.value = text
            else:
                status_text.value = "Unsupported file type."
                page.update()
                return
            status_text.value = f"Imported text from {os.path.basename(file_path)}"
            reset_word_highlight()
            page.update()
        except Exception as ex:
            status_text.value = f"Import error: {ex}"
            page.update()

    file_picker = ft.FilePicker(on_result=on_file_selected)
    page.overlay.append(file_picker)

    def import_text_file(e=None):
        file_picker.pick_files(allow_multiple=False, allowed_extensions=['txt', 'docx', 'pdf'])

    # Buttons
    btn_play = ft.IconButton(icon=ft.Icons.PLAY_ARROW, tooltip="Play", on_click=play_audio, icon_color="#FFD700")
    btn_pause = ft.IconButton(icon=ft.Icons.PAUSE, tooltip="Pause", on_click=pause_audio, icon_color="#FFD700")
    btn_unpause = ft.IconButton(icon=ft.Icons.REPLAY, tooltip="Unpause", on_click=unpause_audio, icon_color="#FFD700")
    btn_download = ft.IconButton(icon=ft.Icons.DOWNLOAD, tooltip="Download", on_click=download_audio, icon_color="#FFD700")
    btn_delete = ft.IconButton(icon=ft.Icons.DELETE, tooltip="Delete", on_click=delete_audio, icon_color="#FFD700")
    btn_enter = ft.ElevatedButton(
        "Generate Voice",
        bgcolor="#FFD700",
        color="#1E1E2F",
        on_click=save_and_play,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))
    )
    btn_exit = ft.ElevatedButton(
        "Exit",
        bgcolor="#FFD700",
        color="#1E1E2F",
        on_click=exit_app,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))
    )
    btn_import = ft.ElevatedButton(
        "Import Text",
        bgcolor="#FFD700",
        color="#1E1E2F",
        on_click=import_text_file,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))
    )

    # Settings (dummy for now)
    def open_settings(e):
        pass
    btn_settings = ft.IconButton(
        icon=ft.Icons.SETTINGS,
        tooltip="Settings",
        on_click=open_settings,
        icon_color="#FFD700",
        disabled=False
    )

    # Build a UI Container
    word_spans.current = build_word_spans()
    input_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([
                    ft.Container(content=text_input, padding=ft.Padding(16, 12, 16, 12))
                ], alignment=ft.MainAxisAlignment.CENTER),
                word_spans.current,
                voice_selection,
                mood_selection,
                ft.Text("Adjust Speed", size=18, weight=ft.FontWeight.BOLD, color="#FFD700"),
                speed_slider, btn_import, btn_enter, audio_dropdown,
                ft.Row([btn_play, btn_pause, btn_unpause, btn_download, btn_delete, btn_settings, btn_exit], alignment=ft.MainAxisAlignment.CENTER),
                loading_indicator, status_text
            ],
            spacing=18,
            alignment=ft.MainAxisAlignment.CENTER
        ),
        padding=28,
        border_radius=28,
        bgcolor="#23234A",
        shadow=ft.BoxShadow(blur_radius=18, spread_radius=4, color="#FFD700", offset=ft.Offset(0, 6)),
        animate=400
    )

    # Gradient background
    gradient_bg = ft.Container(
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#1E1E2F", "#3A3A6A", "#6A1B9A", "#FFD700", "#FF8A65"],
            tile_mode="mirror"
        ),
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

if __name__ == "__main__":
    ft.app(target=main)

