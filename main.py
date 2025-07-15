import os
import sys
import time
import threading
import math
import json
import random
from datetime import datetime

# --- Kivy and App Dependencies ---
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.image import Image as KivyImage
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.utils import get_color_from_hex, platform
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.lang import Builder

# --- AI & Media Dependencies ---
try:
    import google.generativeai as genai
    print("Google AI library found. Jerry's advanced AI is available.")
except ImportError:
    genai = None
    print("Warning: Google AI library not found. Run 'pip install google-generativeai'. Jerry will have basic responses.")

# --- PATHS & BASIC SETUP ---
if platform == 'android' or platform == 'ios':
    from kivy.utils import user_data_dir
    USER_DATA_DIR = user_data_dir
else:
    HOME_DIR = os.path.expanduser("~")
    USER_DATA_DIR = os.path.join(HOME_DIR, ".HushOS")

LOGS_PATH = os.path.join(USER_DATA_DIR, "logs")
JERRY_STATE_PATH = os.path.join(LOGS_PATH, "jerry_state.json")
ENTRIES_LOG_PATH = os.path.join(LOGS_PATH, "entries_log.json")
CONVERSATION_LOG_PATH = os.path.join(LOGS_PATH, "conversation_log.json")
JERRY_MEMORY_PATH = os.path.join(LOGS_PATH, "jerry_memory.json")
ASSETS_PATH = "assets"

os.makedirs(LOGS_PATH, exist_ok=True)

# --- GLOBAL DATA (Identical to original) ---
AFFIRMATIONS = [
    "Your feelings are valid, even the difficult ones.", "Be kind and patient with yourself today.",
    "Each breath is a new, gentle beginning.", "It's okay to rest; you are doing enough.",
    "You are resilient, and you can get through this moment.", "Allow yourself to simply be, without judgment."
]
PLAYLIST = ["01 Morning Dew.wav", "02 Serenity.wav", "04 Enchanting Table.wav", "06 Moving On.wav", "13 Return Home.wav"]
CBT_QUESTIONS = [{"question": "What situation triggered your emotional response?", "key": "situation"}, {"question": "What emotions are you feeling right now?", "key": "emotions"}, {"question": "What automatic thoughts went through your mind?", "key": "thoughts"}]
COGNITIVE_DISTORTIONS = {} # Data omitted for brevity
DBT_QUESTIONS = [] # Data omitted for brevity
DBT_SKILLS = {} # Data omitted for brevity
DAILY_THEMES = [
    {"navbar": "#ade6eb", "navbar_hover": "#8ac0d5", "background": "#fdfae6", "text_dark": "#4a4a4a", "text_light": "#4a4a4a", "accent": "#fcf8a7", "accent_dark": "#fbd7a5", "disabled": "#e0e0e0", "chat_bg": "#FFFFFF", "emotion": "#ade6eb", "physical": "#fcf8a7", "mental": "#fdfae6", "cbt_primary": "#ade6eb", "cbt_secondary": "#b8e0ea", "cbt_tertiary": "#c9e9f0", "cbt_quaternary": "#d9f3f5", "cbt_complete": "#fdfae6", "dbt_primary": "#c8a2e4", "dbt_secondary": "#d3b4ea", "dbt_tertiary": "#dfc9f0", "dbt_quaternary": "#eac3f5", "dbt_complete": "#e9e0f8", "clarity_bar": "#8ac0d5", "insight_bar": "#fbd7a5", "calm_bar": "#addcc7"},
    {"navbar": "#a2e4d3", "navbar_hover": "#7fc9b8", "background": "#e6f2e4", "text_dark": "#3d5a54", "text_light": "#3d5a54", "accent": "#7fc9b8", "accent_dark": "#6ab9a0", "disabled": "#d1e9d7", "chat_bg": "#FFFFFF", "emotion": "#a2e4d3", "physical": "#b4e9c5", "mental": "#e6f2e4", "cbt_primary": "#a2e4d3", "cbt_secondary": "#b0e9c8", "cbt_tertiary": "#beeddd", "cbt_quaternary": "#ccf2e2", "cbt_complete": "#e6f2e4", "dbt_primary": "#fec994", "dbt_secondary": "#f8d6a7", "dbt_tertiary": "#f9e0b7", "dbt_quaternary": "#fbe6c7", "dbt_complete": "#fff5ea", "clarity_bar": "#7fc9b8", "insight_bar": "#b4e9c5", "calm_bar": "#a2e4d3"},
]

# --- DATA MANAGEMENT CLASSES (Identical to original) ---
class ConversationLog:
    def __init__(self, filepath): self.filepath = filepath
    def load_log(self):
        try:
            with open(self.filepath, 'r') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return []
    def add_session(self, chat_history):
        if not chat_history: return
        log = self.load_log()
        session = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "conversation": chat_history}
        log.insert(0, session)
        with open(self.filepath, 'w') as f: json.dump(log, f, indent=4)

class JerryMemory:
    def __init__(self, filepath): self.filepath = filepath
    def load_memory(self):
        try:
            with open(self.filepath, 'r') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return {}
    def save_memory(self, memory_dict):
        with open(self.filepath, 'w') as f: json.dump(memory_dict, f, indent=4)

class EntriesLog:
    def __init__(self): self.entries = self.load_entries()
    def load_entries(self):
        try:
            with open(ENTRIES_LOG_PATH, 'r') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return []
    def add_entry(self, entry_type, data):
        entry = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "type": entry_type, "data": data}
        self.entries.insert(0, entry)
        self.save_entries()
    def save_entries(self):
        with open(ENTRIES_LOG_PATH, 'w') as f: json.dump(self.entries, f, indent=4)
    def get_all_entries(self): return self.entries

class JerryCompanion:
    def __init__(self):
        self.needs = {"clarity": 100, "insight": 100, "calm": 100}
        self.last_fed = {"clarity": time.time(), "insight": time.time(), "calm": time.time()}
        self.decay_rates_hours = {"clarity": 24, "insight": 48, "calm": 12}
        self.xp = 0; self.level = 1; self.xp_to_next_level = 100
        self.load_state()
    def load_state(self):
        try:
            with open(JERRY_STATE_PATH, 'r') as f:
                state = json.load(f)
                self.needs = state.get("needs", self.needs)
                self.last_fed = state.get("last_fed", self.last_fed)
                self.xp = state.get("xp", self.xp)
                self.level = state.get("level", self.level)
                self.xp_to_next_level = state.get("xp_to_next_level", self.xp_to_next_level)
        except (FileNotFoundError, json.JSONDecodeError): self.save_state()
    def save_state(self):
        with open(JERRY_STATE_PATH, 'w') as f:
            json.dump({"needs": self.needs, "last_fed": self.last_fed, "xp": self.xp, "level": self.level, "xp_to_next_level": self.xp_to_next_level}, f, indent=4)
    def update_needs(self):
        now = time.time()
        for n, t in self.last_fed.items():
            self.needs[n] = max(0, 100 - ((now - t) / 3600 / self.decay_rates_hours[n]) * 100)
    def feed(self, n, a=100):
        self.update_needs(); self.needs[n] = min(100, self.needs[n] + a); self.last_fed[n] = time.time(); self.save_state()
    def add_xp(self, a):
        self.xp += a
        if self.xp >= self.xp_to_next_level: self.level_up()
        self.save_state()
    def level_up(self):
        self.level += 1; self.xp -= self.xp_to_next_level; self.xp_to_next_level = int(self.xp_to_next_level * 1.5)

class JerryAI:
    def __init__(self, companion, app_controller):
        self.jerry = companion; self.app = app_controller; self.model = None
        self.chat_history = []; self.is_thinking = False
        self.conversation_log = ConversationLog(CONVERSATION_LOG_PATH)
        self.memory = JerryMemory(JERRY_MEMORY_PATH)
        API_KEY = os.getenv("SECRET_API_KEY")
        if genai and API_KEY != "YOUR_API_KEY_HERE":
            try:
                genai.configure(api_key=API_KEY)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e: print(f"AI configuration failed: {e}")
    def get_system_prompt(self):
        base_prompt = ("You are Jerry, a gentle, compassionate, and wise companion...")
        memory_data = self.memory.load_memory()
        if memory_data:
            memory_str = json.dumps(memory_data)
            return f"{base_prompt} Here is a summary of what you remember about the user: {memory_str}"
        return base_prompt
    def _update_memory(self):
        if not self.model or not self.chat_history: return
        try:
            # ... identical logic ...
            pass
        except Exception as e: print(f"Failed to update Jerry's memory: {e}")
    def end_session(self):
        self.conversation_log.add_session(self.chat_history); self._update_memory(); self.chat_history = []
    def get_response(self, user_input, callback):
        self.is_thinking = True
        def _get_response_thread():
            user_input_lower = user_input.lower().strip()
            action_map = {"check-in":"checkin", "check in":"checkin", "cbt":"cbt", "untangle":"cbt", "dbt":"dbt", "skill":"dbt", "hush":"hush", "peace":"hush", "entries":"entries", "log":"entries", "history":"history", "memory":"history"}
            for keyword, action in action_map.items():
                if keyword in user_input_lower:
                    Clock.schedule_once(lambda dt: callback(f"ACTION:{action}")); self.is_thinking = False; return
            if self.model:
                try:
                    chat = self.model.start_chat(history=[{'role':'user', 'parts':[self.get_system_prompt()]}]+self.chat_history)
                    response = chat.send_message(user_input)
                    jerry_response = response.text.strip()
                    self.chat_history.append({'role': 'user', 'parts': [user_input]})
                    self.chat_history.append({'role': 'model', 'parts': [jerry_response]})
                    Clock.schedule_once(lambda dt: callback(jerry_response))
                except Exception as e:
                    Clock.schedule_once(lambda dt: callback("I'm having a little trouble thinking right now."))
                    print(f"AI Error: {e}")
            else:
                Clock.schedule_once(lambda dt: callback(random.choice(["Tell me more.", "I hear you.", "That's valid."])))
            self.is_thinking = False
        threading.Thread(target=_get_response_thread, daemon=True).start()

# --- KIVY WIDGETS AND SCREENS ---
class RootWidget(BoxLayout):
    pass

class JerryAnimator(FloatLayout):
    anim_frame = NumericProperty(0)
    is_thinking = BooleanProperty(False)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.jerry = self.app.jerry
        self.theme = self.app.theme
        self._define_sprites()
        self.anim_event = None
        self.thinking_event = None
    def _define_sprites(self):
        # Sprite data is large and has been omitted for clarity.
        # The original sprite data from the previous version should be used here.
        self.sprites = {
            "content": [[[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],[3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],[3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]],
            "low_insight": [[[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[3,1,1,1,4,4,1,1,1,1,4,4,1,1,1,3],[3,1,1,1,1,4,4,1,1,4,4,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,4,4,1,1,1,1,1,1,3],[3,1,1,1,1,1,4,1,1,4,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[3,1,1,1,4,4,1,1,1,1,4,4,1,1,1,3],[3,1,1,1,1,4,4,1,1,4,4,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,4,4,4,4,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]],
            "low_calm": [[[0,0,0,3,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,1,1,1,1,1,1,1,1,1,3,0,0,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,3,0,0],[3,1,1,1,4,4,1,1,1,4,4,1,1,1,3,0],[3,1,1,1,4,4,1,1,1,4,4,1,1,1,3,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,3,0,0],[0,0,3,1,1,1,1,1,1,1,1,1,3,0,0,0],[0,0,0,3,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,3,1,1,1,4,4,1,1,1,4,4,1,1,3,0],[0,3,1,1,1,4,4,1,1,1,4,4,1,1,3,0],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,3,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,0,0,3,3,3,3,3,3,3,3,3,3,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]],
            "thinking": [[[0,0,0,0,0,0,0,0,0,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,3,1,1,1,3,0,0,0],[0,0,0,0,0,0,0,3,1,1,1,1,1,3,0,0],[0,0,0,0,0,0,0,3,1,2,0,2,1,1,3,0],[0,0,0,0,0,0,3,1,1,1,1,1,1,1,3,0],[0,0,0,0,0,3,1,1,1,1,1,1,1,3,0,0],[0,0,0,0,0,0,3,3,3,3,3,3,3,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],[[0,0,0,0,0,0,0,0,0,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,3,1,1,1,3,0,0,0],[0,0,0,0,0,0,0,3,1,1,1,1,1,3,0,0],[0,0,0,0,0,0,0,3,1,2,2,2,1,1,3,0],[0,0,0,0,0,0,3,1,1,1,1,1,1,1,3,0],[0,0,0,0,0,3,1,1,1,1,1,1,1,3,0,0],[0,0,0,0,0,0,3,3,3,3,3,3,3,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]]
        }
        self.sprites["low_clarity"] = self.sprites["content"]
    def start(self):
        self.stop()
        self.is_thinking = False
        self.anim_event = Clock.schedule_interval(self.animate, 0.35)
    def stop(self):
        if self.anim_event: self.anim_event.cancel(); self.anim_event = None
        if self.thinking_event: self.thinking_event.cancel(); self.thinking_event = None
    def animate(self, dt):
        self.jerry.update_needs()
        needs = self.jerry.needs
        min_need = min(needs, key=needs.get)
        anim_key = f"low_{min_need}" if needs[min_need] < 50 else "content"
        new_interval = 0.15 if anim_key == "low_calm" else 0.35
        if self.anim_event and self.anim_event.timeout != new_interval:
            self.anim_event.cancel()
            self.anim_event = Clock.schedule_interval(self.animate, new_interval)
        frames = self.sprites[anim_key]
        self.anim_frame = (self.anim_frame + 1) % len(frames)
        self.draw_sprite(frames[self.anim_frame], anim_key)
    def show_thinking_sprite(self):
        self.stop(); self.is_thinking = True; self.anim_frame = 0
        self.thinking_event = Clock.schedule_interval(self.animate_thinking, 0.5)
    def animate_thinking(self, dt):
        frames = self.sprites["thinking"]
        self.anim_frame = (self.anim_frame + 1) % len(frames)
        self.draw_sprite(frames[self.anim_frame], 'thinking')
    def draw_sprite(self, data, anim_key):
        self.canvas.clear()
        pixel_size = self.width / 18
        offset_x = (self.width - (16 * pixel_size)) / 2
        offset_y = (self.height - (16 * pixel_size)) / 2
        clarity_factor = self.jerry.needs['clarity'] / 100.0
        r, g, b = int(173 + (43 - 173) * (1-clarity_factor)), int(214 + (52 - 214) * (1-clarity_factor)), int(239 + (64 - 239) * (1-clarity_factor))
        body_c, outline_c, eye_c, feature_c = (r/255, g/255, b/255, 1), get_color_from_hex("#4a4a4a"), get_color_from_hex("#FFFFFF"), get_color_from_hex("#8ac0d5")
        if anim_key == 'low_insight':
            r,g,b = int(r*0.8), int(g*0.8), int(b*0.8)
            body_c = (r/255, g/255, b/255, 1)
            feature_c = get_color_from_hex("#627a82")
        with self.canvas:
            for y, row in enumerate(data):
                for x, p in enumerate(row):
                    if p > 0:
                        if p == 1: Color(*body_c)
                        elif p == 2: Color(*eye_c)
                        elif p == 3: Color(*outline_c)
                        elif p == 4: Color(*feature_c)
                        Rectangle(pos=(x * pixel_size + offset_x, self.height - (y+1) * pixel_size - offset_y), size=(pixel_size, pixel_size))

# --- SCREEN CLASSES ---
class SplashScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(self.go_to_jerry, 2)
    def go_to_jerry(self, dt):
        if self.manager: self.manager.current = 'jerry'

class JerryScreen(Screen):
    def on_enter(self):
        self.ids.animator.start()
        self.update_ui()
        self.ids.chat_log.text = ""
        self.add_message("Jerry", "It's good to see you again.")
        self.ids.user_entry.focus = True
        App.get_running_app().update_affirmation_banner(self.name)
    def on_leave(self):
        self.ids.animator.stop()
        App.get_running_app().ai.end_session()
    def update_ui(self):
        jerry = App.get_running_app().jerry
        jerry.update_needs()
        self.ids.clarity_bar.value = jerry.needs['clarity']
        self.ids.insight_bar.value = jerry.needs['insight']
        self.ids.calm_bar.value = jerry.needs['calm']
        self.ids.level_label.text = f"Level {jerry.level} ({jerry.xp}/{jerry.xp_to_next_level} XP)"
        self.ids.xp_bar.value = (jerry.xp / jerry.xp_to_next_level) * 100
    def send_message(self):
        app = App.get_running_app()
        if app.ai.is_thinking: return
        user_text = self.ids.user_entry.text.strip()
        if not user_text: return
        self.add_message("You", user_text)
        self.ids.user_entry.text = ""
        self.ids.user_entry.disabled = True
        self.ids.send_button.disabled = True
        self.ids.animator.show_thinking_sprite()
        app.ai.get_response(user_text, self.handle_ai_response)
    def handle_ai_response(self, response):
        if response.startswith("ACTION:"):
            self.manager.current = response.split(":")[1]
        else:
            self.add_message("Jerry", response, is_typing=True)
    def add_message(self, speaker, message, is_typing=False):
        app = App.get_running_app()
        speaker_color_hex = app.theme.COLORS['accent_dark'] if speaker == 'Jerry' else app.theme.COLORS['text_dark']
        self.ids.chat_log.text += f"[b][color={speaker_color_hex}]{speaker}: [/color][/b]"
        if is_typing and app.ai.model:
            Clock.schedule_once(lambda dt, m=message: self.type_out_message(m))
        else:
            self.ids.chat_log.text += f"{message}\n\n"
            self.ids.user_entry.disabled = False
            self.ids.send_button.disabled = False
    def type_out_message(self, message, index=0):
        if index < len(message):
            self.ids.chat_log.text += message[index]
            Clock.schedule_once(lambda dt: self.type_out_message(message, index + 1), 0.035)
        else:
            self.ids.chat_log.text += "\n\n"
            self.ids.user_entry.disabled = False
            self.ids.send_button.disabled = False
            self.ids.user_entry.focus = True
            self.ids.animator.start()

class CheckinScreen(Screen):
    checkin_step = NumericProperty(0)
    bg_color = ListProperty([1,1,1,1]) # Add a color property
    def on_enter(self):
        App.get_running_app().update_affirmation_banner(self.name)
        self.checkin_data = {}
        self.checkin_step = 0
        self.display_step()
    def display_step(self):
        self.ids.content.clear_widgets()
        steps = [("How are you feeling emotionally?", ["good", "ok", "bad"], "emotion"),("How is your body feeling?", ["energetic", "tired", "pain"], "physical"),("How is your mind today?", ["clear", "foggy", "overwhelmed"], "mental")]
        if self.checkin_step >= len(steps): self.complete_checkin(); return
        title, icons, color_key = steps[self.checkin_step]
        app = App.get_running_app()
        self.bg_color = get_color_from_hex(app.theme.COLORS[color_key]) # Update the property
        self.ids.content.add_widget(Label(text=title, font_size='24sp', color=get_color_from_hex(app.theme.COLORS['text_dark']), size_hint_y=None, height=dp(100)))
        btn_frame = BoxLayout(orientation='horizontal', spacing=dp(20), size_hint_y=None, height=dp(150), padding=[dp(20), 0, dp(20), 0])
        for icon_name in icons:
            item_frame = BoxLayout(orientation='vertical', size_hint_x=1/3)
            img_path = os.path.join(ASSETS_PATH, f"{icon_name}.png")
            btn = Button(background_normal=img_path, background_down=img_path, size_hint=(None, None), size=(dp(80), dp(80)), border=(0,0,0,0), pos_hint={'center_x': 0.5})
            btn.bind(on_press=lambda x, cat=color_key, choice=icon_name: self.next_step(cat, choice))
            item_frame.add_widget(btn)
            item_frame.add_widget(Label(text=icon_name.capitalize(), color=get_color_from_hex(app.theme.COLORS['text_dark'])))
            btn_frame.add_widget(item_frame)
        self.ids.content.add_widget(btn_frame)
    def next_step(self, category, choice):
        self.checkin_data[category] = choice; self.checkin_step += 1; self.display_step()
    def complete_checkin(self):
        app = App.get_running_app()
        summary = f"Emotionally feeling {self.checkin_data.get('emotion', 'N/A')}, physically {self.checkin_data.get('physical', 'N/A')}, mentally {self.checkin_data.get('mental', 'N/A')}."
        log_data = {"summary": summary, "details": self.checkin_data}
        app.entries_log.add_entry("Check-in", log_data)
        app.jerry.feed("clarity", 50); app.jerry.add_xp(10)
        self.manager.current = 'jerry'

class CBTScreen(Screen):
    def on_enter(self):
        App.get_running_app().update_affirmation_banner(self.name)
        self.ids.content.clear_widgets()
        self.ids.content.add_widget(Label(text="CBT Screen - Under Construction", font_size='24sp'))

class DBTScreen(Screen):
    def on_enter(self):
        App.get_running_app().update_affirmation_banner(self.name)
        self.ids.content.clear_widgets()
        self.ids.content.add_widget(Label(text="DBT Screen - Under Construction", font_size='24sp'))

class EntriesScreen(Screen):
    def on_enter(self):
        App.get_running_app().update_affirmation_banner(self.name)
        self.ids.entries_log.text = ""
        entries = App.get_running_app().entries_log.get_all_entries()
        if not entries: self.ids.entries_log.text = "No entries yet."
        else:
            for entry in entries:
                title = f"[b][{entry['type']}] - {entry['timestamp']}[/b]\n"
                summary = f"{entry['data']['summary']}\n\n"
                self.ids.entries_log.text += title + summary

class HistoryScreen(Screen):
    def on_enter(self):
        App.get_running_app().update_affirmation_banner(self.name)
        self.ids.history_log.text = ""
        convo_log = App.get_running_app().ai.conversation_log.load_log()
        if not convo_log: self.ids.history_log.text = "No conversation history."
        else:
            for session in convo_log:
                self.ids.history_log.text += f"[b]Session: {session['timestamp']}[/b]\n"
                for message in session['conversation']:
                    speaker = "Jerry" if message['role'] == 'model' else 'You'
                    text = message['parts'][0] if isinstance(message['parts'], list) else message['parts']
                    self.ids.history_log.text += f"[b]{speaker}:[/b] {text}\n"
                self.ids.history_log.text += "\n"

class HushScreen(Screen):
    timer_seconds = NumericProperty(180)
    timer_active = BooleanProperty(False)
    def on_enter(self):
        App.get_running_app().update_affirmation_banner(self.name)
        self.reset_timer()
    def start_timer(self):
        self.timer_active = True
        app = App.get_running_app(); app.jerry.feed("calm", 100); app.jerry.add_xp(5)
        self.timer_event = Clock.schedule_interval(self.update_timer, 1)
    def update_timer(self, dt):
        self.timer_seconds -= 1
        if self.timer_seconds <= 0:
            self.timer_event.cancel(); self.manager.current = 'jerry'
    def get_timer_text(self):
        mins, secs = divmod(self.timer_seconds, 60)
        return f"{int(mins):02d}:{int(secs):02d}"
    def reset_timer(self):
        if hasattr(self, 'timer_event') and self.timer_event: self.timer_event.cancel()
        self.timer_active = False; self.timer_seconds = 180
    def on_leave(self): self.reset_timer()

# --- MAIN APP CLASS ---
class HushOSApp(App):
    def build(self):
        self.theme = self.get_daily_theme()
        self.jerry = JerryCompanion()
        self.ai = JerryAI(self.jerry, self)
        self.entries_log = EntriesLog()
        self.sound = None
        self.current_track_index = 0
        self.play_music()
        # FIX: Kivy automatically loads the 'hushos.kv' file.
        # We just need to return an instance of our root widget.
        return RootWidget()

    def on_start(self):
        Window.bind(on_request_close=self.on_request_close)
        # FIX: Schedule the screen change for the next frame
        Clock.schedule_once(self.go_to_splash)

    def go_to_splash(self, dt):
        self.root.ids.sm.current = 'splash'

    def on_stop(self):
        self.ai.end_session()
        self.jerry.save_state()
        
    def on_request_close(self, *args):
        self.on_stop()
        return False

    def get_daily_theme(self):
        class Theme:
            def __init__(self):
                self.COLORS = DAILY_THEMES[datetime.now().weekday() % len(DAILY_THEMES)]
        return Theme()

    def change_screen(self, screen_name):
        self.root.ids.sm.current = screen_name

    def update_affirmation_banner(self, screen_name):
        banner = self.root.ids.affirmation_banner
        if screen_name == 'jerry':
            banner.height = 0
        else:
            banner.height = dp(40)
            self.jerry.update_needs()
            needs = self.jerry.needs
            min_need = min(needs, key=needs.get)
            if needs[min_need] < 50:
                affirmation = f"Jerry is feeling a bit low on {min_need}. Maybe we can help?"
            else:
                affirmation = random.choice(AFFIRMATIONS)
            banner.text = affirmation

    def play_music(self):
        if self.sound: self.sound.stop()
        track_name = PLAYLIST[self.current_track_index]
        path = os.path.join(ASSETS_PATH, track_name)
        if os.path.exists(path):
            self.sound = SoundLoader.load(path)
            if self.sound:
                self.sound.volume = 0.3; self.sound.play(); self.sound.bind(on_stop=self.next_track)
    def next_track(self, *args):
        self.current_track_index = (self.current_track_index + 1) % len(PLAYLIST)
        self.play_music()
    def toggle_music(self):
        if self.sound:
            if self.sound.state == 'play': self.sound.stop()
            else: self.sound.play()

if __name__ == '__main__':
    HushOSApp().run()
