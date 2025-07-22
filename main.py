import os
import sys
import time
import threading
import math
import json
import random
import openai
from datetime import datetime
from shutil import copyfile

# --- Kivy and App Dependencies ---
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivy.app import App
from kivymd.uix.screen import MDScreen
from kivymd.uix.navigationdrawer import MDNavigationLayout
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.image import Image
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.checkbox import CheckBox
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.utils import platform, get_hex_from_color, get_color_from_hex
from kivy.metrics import dp
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.lang import Builder
from dotenv import load_dotenv

if platform == "android":
    from android.storage import app_storage_path
    app_dir = app_storage_path()
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
# --- PATHS & BASIC SETUP ---
ASSETS_PATH = "assets"

# --- GLOBAL DATA ---
AFFIRMATIONS = [
    "Your feelings are valid, even the difficult ones.", "Be kind and patient with yourself today.",
    "Each breath is a new, gentle beginning.", "It's okay to rest; you are doing enough.",
    "You are resilient, and you can get through this moment.", "Allow yourself to simply be, without judgment."
]
PLAYLIST = ["01 Morning Dew.wav", "02 Serenity.wav", "04 Enchanting Table.wav", "06 Moving On.wav", "13 Return Home.wav"]

CBT_QUESTIONS = [
    {"question": "What was the situation or event that triggered the difficult feeling?", "key": "situation", "hint": "e.g., I had a disagreement with a friend."},
    {"question": "What emotions did you feel? (e.g., sad, angry, anxious)", "key": "emotions", "hint": "List the primary emotions."},
    {"question": "What were the automatic thoughts that went through your mind?", "key": "thoughts", "hint": "What did you immediately think or believe?"}
]
COGNITIVE_DISTORTIONS = {
    "All-or-Nothing Thinking": "Viewing things in black-and-white categories.", "Overgeneralization": "Seeing a single negative event as a never-ending pattern of defeat.",
    "Mental Filter": "Picking out a single negative detail and dwelling on it exclusively.", "Disqualifying the Positive": "Rejecting positive experiences by insisting they 'don't count'.",
    "Jumping to Conclusions": "Making a negative interpretation despite no definite facts.", "Mind Reading": "Concluding that someone is reacting negatively to you without evidence.",
    "Fortune Telling": "Anticipating that things will turn out badly.", "Magnification/Minimization": "Exaggerating the importance of negative things or shrinking positive things.",
    "Emotional Reasoning": "Assuming that your negative emotions necessarily reflect the way things really are.", "Should Statements": "Motivating yourself with 'shoulds' and 'shouldn'ts'.",
    "Labeling": "An extreme form of overgeneralization; attaching a negative label to yourself.", "Personalization": "Seeing yourself as the cause of some negative external event which you were not responsible for."
}
DBT_QUESTIONS = [
    {"question": "Rate the intensity of your ANGER (0-5).", "key": "anger", "type": "rating"}, {"question": "Rate the intensity of your SADNESS (0-5).", "key": "sadness", "type": "rating"},
    {"question": "Rate the intensity of your FEAR (0-5).", "key": "fear", "type": "rating"}, {"question": "Rate the intensity of your SHAME (0-5).", "key": "shame", "type": "rating"},
    {"question": "Rate your urge for self-harm (0-5).", "key": "self_harm_urge", "type": "rating"}, {"question": "Rate your urge to use substances (0-5).", "key": "substance_urge", "type": "rating"},
]
DBT_SKILLS = {
    "Mindfulness": ["Observe", "Describe", "Participate", "Non-judgmentally", "One-mindfully", "Effectively"], "Distress Tolerance": ["TIP", "ACCEPTS", "Self-Soothe", "IMPROVE the moment", "Radical Acceptance"],
    "Emotion Regulation": ["Check the Facts", "Opposite Action", "Problem Solving", "ABC PLEASE"], "Interpersonal Effectiveness": ["DEAR MAN", "GIVE", "FAST"]
}

# --- DATA MANAGEMENT CLASSES ---
class ColorProgressBar(ProgressBar):
    # RGBA color list property for the bar's fill color
    bar_color = ListProperty([1, 0, 0, 1])  # default red color
    
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
    def __init__(self, entries_filepath):
        self.filepath = entries_filepath
        self.entries = self.load_entries()
    def load_entries(self):
        try:
            with open(self.filepath, 'r') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return []
    def add_entry(self, entry_type, data):
        entry = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "type": entry_type, "data": data}
        self.entries.insert(0, entry)
        self.save_entries()
    def save_entries(self):
        with open(self.filepath, 'w') as f: json.dump(self.entries, f, indent=4)
    def get_all_entries(self): return self.entries

class JerryCompanion:
    def __init__(self, state_filepath):
        self.state_filepath = state_filepath
        self.needs = {"clarity": 100, "insight": 100, "calm": 100}
        self.last_fed = {"clarity": time.time(), "insight": time.time(), "calm": time.time()}
        self.decay_rates_hours = {"clarity": 24, "insight": 48, "calm": 12}
        self.xp = 0; self.level = 1; self.xp_to_next_level = 100
        self.load_state()
    def load_state(self):
        try:
            with open(self.state_filepath, 'r') as f:
                state = json.load(f)
                self.needs = state.get("needs", self.needs)
                self.last_fed = state.get("last_fed", self.last_fed)
                self.xp = state.get("xp", self.xp)
                self.level = state.get("level", self.level)
                self.xp_to_next_level = state.get("xp_to_next_level", self.xp_to_next_level)
        except (FileNotFoundError, json.JSONDecodeError): self.save_state()
    def save_state(self):
        with open(self.state_filepath, 'w') as f:
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

class OpenAIClient:
    def __init__(self, api_key=None):
        # Try to load from .env if not provided
        if api_key is None:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("HUSHOS_API_KEY")

            # Fallback to config.json if still not found
            if not api_key:
                try:
                    app_dir = os.path.dirname(os.path.abspath(__file__))
                    config_path = os.path.join(app_dir, "config.json")
                    with open(config_path) as f:
                        config = json.load(f)
                        api_key = config.get("HUSHOS_API_KEY")
                        print(f"[OpenAIClient] Loaded API key from config.json: {'Yes' if api_key else 'No'}")
                except Exception as e:
                    print(f"[OpenAIClient] Failed to load API key: {e}")

        self.api_key = api_key
        openai.api_key = self.api_key

class JerryAI:
    MAX_HISTORY = 20

    def __init__(self, jerry, app, conversation_log_path, jerry_memory_path, api_key=None):
        app_dir = App.get_running_app().user_data_dir
        state_filepath = os.path.join(app_dir, "jerry_state.json")
        self.companion = JerryCompanion(state_filepath)
        self.jerry = jerry
        self.app = app
        self.conversation_log = ConversationLog(conversation_log_path)
        self.memory = JerryMemory(jerry_memory_path)
        self.api_key = api_key
        self.chat_lock = threading.Lock()
        self.is_thinking = False
        self.chat_history = []

        # Fallback to config.json inside the app's data dir
        if not self.api_key:
            config_path = os.path.join(app.user_data_dir, "config.json")
            print(f"[JerryAI] Looking for config at {config_path}")
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    self.api_key = config.get("HUSHOS_API_KEY")
                    print(f"[JerryAI] API key loaded: {'Yes' if self.api_key else 'No'}")
            except Exception as e:
                print(f"[JerryAI] Failed to load config.json: {e}")

        # Initialize OpenAI client
        if self.api_key:
            self.openai_client = OpenAIClient(api_key=self.api_key)
            print("Jerry AI initialized with OpenAI support.")
        else:
            self.openai_client = None
            print("Jerry AI initialized in basic mode (no API key).")

        self.system_prompt = "You are Jerry, a friendly, gentle, and supportive AI companion. Keep your responses brief and caring."

    @property
    def needs(self):
        return self.companion.needs
        
    def get_response(self, user_input, callback):
        self.is_thinking = True
        with self.chat_lock:
            self.chat_history.append({"role": "user", "content": user_input})
            if len(self.chat_history) > self.MAX_HISTORY:
                self.chat_history = self.chat_history[-self.MAX_HISTORY:]

    def get_response_thread(user_input, callback):
        def run():
            if self.openai_client:
                messages = [{"role": "system", "content": self.system_prompt}] + self.chat_history
                ai_response = self.openai_client.chat(messages=messages)

                if ai_response is None:
                    ai_response = self.get_fallback_response(user_input)

                with self.chat_lock:
                    self.chat_history.append({"role": "assistant", "content": ai_response})
                    if len(self.chat_history) > self.MAX_HISTORY:
                        self.chat_history = self.chat_history[-self.MAX_HISTORY:]

                Clock.schedule_once(lambda dt, resp=ai_response: callback(resp))
                Clock.schedule_once(lambda dt: setattr(self, 'is_thinking', False))

        threading.Thread(target=run, daemon=True).start()

    def get_fallback_response(self, user_input):
        user_input = user_input.lower()
        responses = {
            "hello": "Hello! It's good to see you.",
            "hi": "Hello! It's good to see you.",
            "how are you": "I'm doing well, thank you! How can I help you today?",
            "thank": "You're very welcome!",
            "bye": "Goodbye! Have a great day!"
        }
        for key, value in responses.items():
            if key in user_input:
                return value
        return "I'm here to listen. Tell me what's on your mind."

    def end_session(self):
        if self.chat_history:
            print("Session ended. Saving conversation to log.")
            self.conversation_log.add_session(self.chat_history)
            self.chat_history = []
# --- KIVY WIDGETS AND SCREENS ---
class RootWidget(MDScreen):
    pass

class JerryAnimator(FloatLayout):
    anim_frame = NumericProperty(0)
    is_thinking = BooleanProperty(False)
    evolution_level = NumericProperty(0) # <<< NEW: To track Jerry's evolution state
    aura_color = None # <<< NEW: To hold the aura's color instruction for animation

    def __init__(self, companion=None, **kwargs):
        super().__init__(**kwargs)
        self.companion = companion
        Clock.schedule_once(self._post_init)
        self.anim_event = None
        self.thinking_event = None
        self.current_interval = None

    def _post_init(self, dt):
        self.app = MDApp.get_running_app()
        self.jerry = self.app.jerry_ai
        self.theme_cls = self.app.theme_cls
        self._define_sprites()
        self.start() # <<< MOVED: Start the animation once everything is ready

    def _define_sprites(self):
        # ... (your sprite dictionary is unchanged) ...
        self.sprites = {
            "content": [[[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],[3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],[3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]],
            "low_insight": [[[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[3,1,1,1,4,4,1,1,1,1,4,4,1,1,1,3],[3,1,1,1,1,4,4,1,1,4,4,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,4,4,1,1,1,1,1,1,3],[3,1,1,1,1,1,4,1,1,4,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[3,1,1,1,4,4,1,1,1,1,4,4,1,1,1,3],[3,1,1,1,1,4,4,1,1,4,4,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,4,4,4,4,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]],
            "low_calm": [[[0,0,0,3,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,1,1,1,1,1,1,1,1,1,3,0,0,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,3,0,0],[3,1,1,1,4,4,1,1,1,4,4,1,1,1,3,0],[3,1,1,1,4,4,1,1,1,4,4,1,1,1,3,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,3,0,0],[0,0,3,1,1,1,1,1,1,1,1,1,3,0,0,0],[0,0,0,3,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,3,1,1,1,4,4,1,1,1,4,4,1,1,3,0],[0,3,1,1,1,4,4,1,1,1,4,4,1,1,3,0],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,3,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,0,0,3,3,3,3,3,3,3,3,3,3,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]],
            "thinking": [[[0,0,0,0,0,0,0,0,0,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,3,1,1,1,3,0,0,0],[0,0,0,0,0,0,0,3,1,1,1,1,1,3,0,0],[0,0,0,0,0,0,0,3,1,2,0,2,1,1,3,0],[0,0,0,0,0,0,3,1,1,1,1,1,1,1,3,0],[0,0,0,0,0,3,1,1,1,1,1,1,1,3,0,0],[0,0,0,0,0,0,3,3,3,3,3,3,3,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],[[0,0,0,0,0,0,0,0,0,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,3,1,1,1,3,0,0,0],[0,0,0,0,0,0,0,3,1,1,1,1,1,3,0,0],[0,0,0,0,0,0,0,3,1,2,2,2,1,1,3,0],[0,0,0,0,0,0,3,1,1,1,1,1,1,1,3,0],[0,0,0,0,0,3,1,1,1,1,1,1,1,3,0,0],[0,0,0,0,0,0,3,3,3,3,3,3,3,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]]
        }
        self.sprites["low_clarity"] = self.sprites["content"]
        
    # <<< NEW: This is the method you will call from JerryScreen to trigger an evolution
    def evolve(self, level):
        self.evolution_level = level
        # Stop any existing aura animation
        if self.aura_color:
            Animation.cancel_all(self.aura_color)
            self.aura_color = None

        # Start a new aura animation if the level is high enough
        if self.evolution_level >= 2:
            self.start_aura_animation()

    # <<< NEW: This method handles the aura animation
    def start_aura_animation(self):
        # We define the aura color here but add it to the canvas in draw_sprite
        self.aura_color = Color(rgba=(0.5, 0.8, 1, 0)) # Start transparent
        
        # Animate the aura's transparency to make it "breathe"
        # At level 3, we make the aura brighter (a=0.4)
        max_alpha = 0.4 if self.evolution_level >= 3 else 0.2
        anim = Animation(a=max_alpha, d=3) + Animation(a=0.05, d=3)
        anim.repeat = True
        anim.start(self.aura_color)

    def start(self):
        # ... (start method is unchanged) ...
        if not hasattr(self, 'jerry'): return
        self.stop()
        self.is_thinking = False
        self.current_interval = 0.35
        self.anim_event = Clock.schedule_interval(self.animate, self.current_interval)

    def stop(self):
        # ... (stop method is unchanged) ...
        if self.anim_event:
            self.anim_event.cancel()
            self.anim_event = None
        if self.thinking_event:
            self.thinking_event.cancel()
            self.thinking_event = None
        if self.aura_color: # <<< NEW: Also stop aura animation
            Animation.cancel_all(self.aura_color)
            self.aura_color = None

    def animate(self, dt):
        # ... (animate method is unchanged) ...
        needs = self.companion.needs
        min_need = min(needs, key=needs.get)
        anim_key = f"low_{min_need}" if needs[min_need] < 50 else "content"
        new_interval = 0.15 if anim_key == "low_calm" else 0.35
    
        if new_interval != self.current_interval:
            if self.anim_event:
                self.anim_event.cancel()
                self.anim_event = Clock.schedule_interval(self.animate, new_interval)
                self.current_interval = new_interval
            frames = self.sprites[anim_key]
            self.anim_frame = (self.anim_frame + 1) % len(frames)
            self.draw_sprite(frames[self.anim_frame], anim_key)


    def show_thinking_sprite(self):
        # ... (show_thinking_sprite method is unchanged) ...
        self.stop(); self.is_thinking = True; self.anim_frame = 0
        self.thinking_event = Clock.schedule_interval(self.animate_thinking, 0.5)

    def animate_thinking(self, dt):
        # ... (animate_thinking method is unchanged) ...
        frames = self.sprites["thinking"]
        self.anim_frame = (self.anim_frame + 1) % len(frames)
        self.draw_sprite(frames[self.anim_frame], 'thinking')


    def draw_sprite(self, data, anim_key):
        self.canvas.clear()
        pixel_size = self.width / 18
        offset_x = (self.width - (16 * pixel_size)) / 2
        offset_y = (self.height - (16 * pixel_size)) / 2

        # --- Base Colors ---
        body_c = (0.3, 0.6, 0.9, 1)      # Medium bright blue
        outline_c = (0.5, 0.8, 1.0, 1)   # Bright blue
        eye_c = (1, 1, 1, 1)             # White
        feature_c = (0.6, 0.85, 1.0, 1)  # Lighter blue

        # <<< --- EVOLUTION LOGIC STARTS HERE --- >>>

        # LEVEL 1 EVOLUTION: Brighter Colors
        if self.evolution_level >= 1:
            # Make the body a slightly richer, more "insightful" purple-blue
            body_c = (0.4, 0.6, 1.0, 1)
            # Make the outline a brighter, almost glowing cyan
            outline_c = (0.6, 0.9, 1.0, 1)

        # LEVEL 3 EVOLUTION: Golden Tint
        if self.evolution_level >= 3:
            # Add a golden sheen to the body and features
            body_c = (body_c[0] * 0.9, body_c[1] * 0.9, body_c[2] * 0.7, 1) # Shift towards gold
            feature_c = (1.0, 0.9, 0.5, 1) # Make features golden

        # <<< --- EVOLUTION LOGIC ENDS HERE --- >>>

        if anim_key == 'low_insight':
            # This logic still applies on top of evolutions
            body_c = (body_c[0]*0.8, body_c[1]*0.8, body_c[2]*0.8, 1)
            feature_c = (0.4, 0.57, 0.65, 1)

        with self.canvas:
            # <<< NEW: Draw the aura first, if it exists
            if self.evolution_level >= 2 and self.aura_color:
                # Add the animated color instruction to the canvas
                self.canvas.add(self.aura_color)
                # Draw the ellipse shape for the aura
                aura_size = (16 * pixel_size + 40, 16 * pixel_size + 40)
                aura_pos = (offset_x - 20, offset_y - 20)
                Ellipse(pos=aura_pos, size=aura_size)

            # --- This is your original drawing loop ---
            for y, row in enumerate(data):
                for x, p in enumerate(row):
                    if p > 0:
                        if p == 1: Color(*body_c)
                        elif p == 2: Color(*eye_c)
                        elif p == 3: Color(*outline_c)
                        elif p == 4: Color(*feature_c)
                        Rectangle(
                            pos=(x * pixel_size + offset_x, self.height - (y + 1) * pixel_size - offset_y),
                            size=(pixel_size, pixel_size)
                        )

class SplashScreen(Screen):
    def on_enter(self):
        layout = BoxLayout()
        splash = Image(source='assets/new_splash.png', allow_stretch=True, keep_ratio=False)
        layout.add_widget(splash)
        self.add_widget(layout)
        
        Clock.schedule_once(self.go_to_jerry, 2)

    def go_to_jerry(self, dt):
        if self.manager:
            self.manager.transition = FadeTransition(duration=0.5)
            self.manager.current = 'jerry'

class JerryScreen(Screen):
    last_known_level = NumericProperty(0) # Use Kivy property for robustness

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # It's better to get the reference once in the app's on_start method,
        # but for now, we'll get it on enter.
        self.jerry_ai = None

    def on_enter(self):
        """
        Called when the screen is displayed.
        We set up the screen's initial state here.
        """
        # Ensure we have a reference to the main AI object
        if not self.jerry_ai:
            self.jerry_ai = MDApp.get_running_app().jerry_ai
        
        # Schedule UI updates to run on the next frame
        Clock.schedule_once(self.setup_screen)

    def setup_screen(self, dt):
        """
        Final setup after the screen is fully loaded.
        """
        self.update_ui()
        # Only add the initial message if the chat is empty
        if not self.ids.chat_log.children:
            self.add_message("Jerry", "It's good to see you again.")
            self.ids.user_entry.focus = True
        
        # Update the affirmation banner
        MDApp.get_running_app().update_affirmation_banner(self.name)

    def update_needs(self):
        self.companion.update_needs()

    def update_ui(self, *args):
        """
        Updates all UI elements with the latest data from the AI.
        This is the single source of truth for UI updates.
        """
        if not self.jerry_ai:
            return

        self.jerry_ai.companion.update_needs()
        self.ids.clarity_bar.value = self.jerry_ai.needs['clarity']
        self.ids.insight_bar.value = self.jerry_ai.needs['insight']
        self.ids.calm_bar.value = self.jerry_ai.needs['calm']
        self.ids.level_label.text = f"Level {self.jerry_ai.companion.level}"
        self.ids.xp_bar.text = f"XP: {self.jerry_ai.companion.xp} / {self.jerry_ai.companion.xp_to_next_level}"

        # Check if the level has changed to trigger evolution
        if self.jerry_ai.companion.level > self.last_known_level:
            self.check_for_evolution(self.jerry_ai.companion.level)
            self.last_known_level = self.jerry_ai.companion.level

    def check_for_evolution(self, current_level):
        """
        Checks the AI's level and tells the animator to evolve the sprite.
        """
        animator = self.ids.animator
        title_label = self.ids.jerry_title_label
        
        # Determine the evolution stage (e.g., one stage every 10 levels)
        evolution_stage = current_level // 10

        # Call the evolve() method in JerryAnimator
        animator.evolve(evolution_stage)

        # Update the title label based on the evolution stage
        if evolution_stage == 1:
            title_label.text = "Jerry the Listener"
        elif evolution_stage == 2:
            title_label.text = "Calm Companion"
        elif evolution_stage == 3:
            title_label.text = "Beacon of Insight"
        else:
            title_label.text = "" # No title at evolution stage 0

    def send_message(self):
        """
        Handles the user sending a message from the text input.
        """
        user_text = self.ids.user_entry.text.strip()
        if not user_text:
            return
        
        self.add_message("You", user_text)
        self.ids.user_entry.text = ""
        # This is a placeholder for your actual AI call
        self.handle_ai_response("I'm sorry. I seem to be offline.")

    def handle_ai_response(self, response):
        """
        Processes the response from the AI.
        """
        if response.startswith("ACTION:"):
            # Handle screen navigation actions
            MDApp.get_running_app().root.ids.sm.current = response.split(":")[1].strip()
        else:
            self.add_message("Jerry", response)

    def add_message(self, speaker, message):
        """
        Adds a formatted message bubble to the chat log.
        """
        app = MDApp.get_running_app()
        speaker_color = app.theme_cls.primary_color if speaker == 'Jerry' else app.theme_cls.accent_color
        
        message_label = MDLabel(
            text=f"[b][color={get_hex_from_color(speaker_color)}]{speaker}:[/color][/b] {message}",
            markup=True,
            size_hint_y=None,
            theme_text_color="Primary",
            valign="top"
        )
        
        # Bind label size to its texture size for proper wrapping
        message_label.bind(
            width=lambda *x: message_label.setter('text_size')(message_label, (message_label.width, None)),
            texture_size=lambda *x: message_label.setter('height')(message_label, message_label.texture_size[1])
        )
        
        self.ids.chat_log.add_widget(message_label)
        self.scroll_to_bottom()
        
    def scroll_to_bottom(self):
        """
        Scrolls the chat log to the most recent message.
        """
        scroll_view = self.ids.scroller
        Clock.schedule_once(lambda dt: setattr(scroll_view, 'scroll_y', 0), 0.1)

class CheckinScreen(Screen):
    checkin_step = NumericProperty(0)
    
    def on_enter(self):
        MDApp.get_running_app().update_affirmation_banner(self.name)
        self.checkin_data = {}
        self.checkin_step = 0
        self.display_step()

    def display_step(self):
        self.ids.checkin_content.clear_widgets()
        app = MDApp.get_running_app()
        theme_cls = app.theme_cls

        steps = [
            ("How are you feeling emotionally?", ["Good", "Okay", "Bad"], "emotion"),
            ("How is your body feeling?", ["Energetic", "Tired", "Pain"], "physical"),
            ("How is your mind today?", ["Clear", "Foggy", "Overwhelmed"], "mental")
        ]

        if self.checkin_step >= len(steps):
            self.complete_checkin()
            return

        title, choices, key = steps[self.checkin_step]
        
        self.ids.progress_bar.value = (self.checkin_step + 1) / len(steps) * 100
        self.ids.checkin_title_label.text = title

        button_layout = GridLayout(cols=1, spacing=dp(15), size_hint_y=None)
        button_layout.bind(minimum_height=button_layout.setter('height'))

        for choice in choices:
            btn = Button(
                text=choice,
                size_hint_y=None,
                height=dp(50),
                background_color=theme_cls.primary_color
            )
            btn.bind(on_press=lambda x, cat=key, c=choice: self.next_step(cat, c))
            button_layout.add_widget(btn)
        
        self.ids.checkin_content.add_widget(button_layout)

    def next_step(self, category, choice):
        self.checkin_data[category] = choice
        self.checkin_step += 1
        self.display_step()

    def complete_checkin(self):
        app = MDApp.get_running_app()
        summary = f"Emotionally feeling {self.checkin_data.get('emotion', 'N/A')}, physically {self.checkin_data.get('physical', 'N/A')}, mentally {self.checkin_data.get('mental', 'N/A')}."
        log_data = {"summary": summary, "details": self.checkin_data}
        app.entries_log.add_entry("Check-in", log_data)
        app.jerry.feed("clarity", 50)
        app.jerry.add_xp(10)
        app.root.ids.sm.current = 'jerry'

class TherapyScreenBase(Screen):
    flow_step = NumericProperty(0)

    def on_enter(self):
        MDApp.get_running_app().update_affirmation_banner(self.name)
        self.flow_data = {}
        self.flow_step = 0
        self.questions = []
        self.checklist = {}
        self.entry_type = ""
        self.setup_flow()
        self.display_step()

    def setup_flow(self):
        pass # To be overridden

    def display_step(self):
        content_box = self.ids.content_box
        content_box.clear_widgets()
        num_questions = len(self.questions)
        if self.flow_step < num_questions:
            self.display_question_step()
        elif self.flow_step == num_questions and self.checklist:
            self.display_checklist_step()
        else:
            self.complete_flow()

    def display_question_step(self):
        question_data = self.questions[self.flow_step]
        self.ids.title_label.text = question_data["question"]
        self.ids.next_button.text = 'Next'
        content_box = self.ids.content_box
        content_box.clear_widgets()
        
        if question_data.get("type") == "rating":
            def make_callback(key, val):
                return lambda instance: self.set_rating_answer(key, val)

            rating_box = GridLayout(cols=6, size_hint_y=None, height=dp(48))
            for i in range(6):
                val = str(i)
                btn = ToggleButton(
                    text=val,
                    group=question_data["key"],
                    size_hint_y=None,
                    height=dp(48)
                )
                if self.flow_data.get(question_data["key"]) == val:
                    btn.state = 'down'
                btn.bind(on_press=make_callback(question_data["key"], val))
                rating_box.add_widget(btn)
            content_box.add_widget(rating_box)
        else:
            text_input = TextInput(
                text=self.flow_data.get(question_data["key"], ''),
                size_hint_y=None,
                height=dp(150),
                multiline=True,
                hint_text=question_data.get("hint", "")
            )
            text_input.id = 'current_answer'  # <-- Set the ID after creation
            content_box.add_widget(text_input)

    def display_checklist_step(self):
        self.ids.title_label.text = "Did any of these apply?"
        self.ids.next_button.text = 'Finish'
        content_box = self.ids.content_box
        saved_checklist = self.flow_data.get('checklist', [])
        for item, description in self.checklist.items():
            line = BoxLayout(size_hint_y=None, height=dp(48))
            chk = CheckBox(size_hint_x=None, width=dp(48), active=(item in saved_checklist))
            chk.bind(active=lambda instance, value, key=item: self.on_checkbox_active(key, value))
            label = Label(text=f"{item}", text_size=(self.width * 0.7, None), halign='left', valign='middle')
            line.add_widget(chk)
            line.add_widget(label)
            content_box.add_widget(line)

    def on_checkbox_active(self, key, value):
        checked_items = self.flow_data.get('checklist', [])
        if value and key not in checked_items:
            checked_items.append(key)
        elif not value and key in checked_items:
            checked_items.remove(key)
        self.flow_data['checklist'] = checked_items

    def set_rating_answer(self, key, value):
        self.flow_data[key] = value

    def save_current_answer(self):
        if self.flow_step < len(self.questions):
            question_key = self.questions[self.flow_step]["key"]
            if self.ids.content_box.children:
                widget = self.ids.content_box.children[0]
                if isinstance(widget, TextInput):
                    self.flow_data[question_key] = widget.text.strip()

    def next_step(self):
        self.save_current_answer()
        self.flow_step += 1
        self.display_step()

    def prev_step(self):
        if self.flow_step > 0:
            self.save_current_answer()
            self.flow_step -= 1
            self.display_step()

    def complete_flow(self):
        app = MDApp.get_running_app()
        summary = ""
        for key, value in self.flow_data.items():
            summary += f"{key.replace('_', ' ').capitalize()}: {value}\n"
        log_data = {"summary": summary, "details": self.flow_data}
        app.entries_log.add_entry(self.entry_type, log_data)
        app.jerry.feed("insight", 50); app.jerry.add_xp(25)
        app.root.ids.sm.current = 'jerry'

class CBTScreen(TherapyScreenBase):
    def setup_flow(self):
        self.questions = CBT_QUESTIONS
        self.checklist = COGNITIVE_DISTORTIONS
        self.entry_type = "CBT Entry"

class DBTScreen(TherapyScreenBase):
    def setup_flow(self):
        self.questions = DBT_QUESTIONS
        self.checklist = DBT_SKILLS
        self.entry_type = "DBT Entry"
    
    def display_checklist_step(self): # Override for better layout
        self.ids.title_label.text = "Which skills did you use?"
        self.ids.next_button.text = 'Finish'
        content_box = self.ids.content_box
        content_box.clear_widgets()
        saved_checklist = self.flow_data.get('checklist', [])
        for category, skills in self.checklist.items():
            content_box.add_widget(Label(text=f"[b]{category}[/b]", markup=True, size_hint_y=None, height=dp(40)))
            for skill in skills:
                line = BoxLayout(size_hint_y=None, height=dp(48))
                chk = CheckBox(size_hint_x=None, width=dp(48), active=(skill in saved_checklist))
                chk.bind(active=lambda instance, value, key=skill: self.on_checkbox_active(key, value))
                label = Label(text=skill, text_size=(self.width * 0.7, None), halign='left', valign='middle')
                line.add_widget(chk)
                line.add_widget(label)
                content_box.add_widget(line)

class EntriesScreen(Screen):
    def on_enter(self):
        app = MDApp.get_running_app()
        app.update_affirmation_banner(self.name)
        body_box = self.ids.entries_text
        body_box.clear_widgets()
        body_label = self.ids.entries_text
        entries = app.entries_log.get_all_entries()
        if not entries:
            from kivymd.uix.label import MDLabel
            body_box.add_widget(MDLabel(
                text="No entries yet.",
                halign="center"
            ))
            return
            
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel
        for entry in entries:
            entry_type = entry.get('type', 'Entry')
            timestamp = entry.get('timestamp', 'Unknown Date')
            data = entry.get('data', {})
            summary = data.get('summary', 'No summary available.')

            card = MDCard(
                orientation="vertical",
                padding=dp(10),
                spacing=dp(5),
                size_hint_y=None,
                adaptive_height=True,
                md_bg_color=app.theme_cls.surface_container_low_color
            )
            card.add_widget(MDLabel(
                text=f"[{entry_type}] - {timestamp}",
                font_style="Overline",
                adaptive_height=True
            ))
            card.add_widget(MDLabel(
                text=summary,
                theme_text_color="Primary",
                adaptive_height=True
            ))
            body_box.add_widget(card)

class HistoryScreen(Screen):
    def on_enter(self):
        app = MDApp.get_running_app()
        app.update_affirmation_banner(self.name)

        container = self.ids.history_text
        container.clear_widgets()

        convo_log = app.jerry_ai.conversation_log.load_log()
        if not convo_log:
            container.add_widget(MDLabel(
                text="No conversation history.",
                halign="center",
                theme_text_color="Hint",
                adaptive_height=True
            ))
            return

        for session in convo_log:
            timestamp = session.get('timestamp', 'Unknown Date')

            # Session header card
            session_card = MDCard(
                orientation="vertical",
                padding=dp(10),
                spacing=dp(5),
                size_hint_y=None,
                adaptive_height=True,
                md_bg_color=app.theme_cls.surface_container_low_color
            )
            session_card.add_widget(MDLabel(
                text=f"[b]Session: {timestamp}[/b]",
                markup=True,
                font_style="Overline",
                adaptive_height=True
            ))

            container.add_widget(session_card)

            conversation = session.get('conversation', [])
            for message in conversation:
                role = message.get('role', 'model')
                speaker = "Jerry" if role == 'model' else 'You'

                parts = message.get('parts', ['(Message not found)'])
                text = parts[0] if isinstance(parts, list) and parts else '(Empty message)'

                msg_card = MDCard(
                    orientation="vertical",
                    padding=dp(8),
                    size_hint_y=None,
                    adaptive_height=True,
                    md_bg_color=app.theme_cls.surface_variant
                )
                msg_card.add_widget(MDLabel(
                    text=f"[b]{speaker}:[/b] {text}",
                    markup=True,
                    adaptive_height=True
                ))

                container.add_widget(msg_card)
            
class HushScreen(Screen):
    timer_seconds = NumericProperty(180)
    timer_active = BooleanProperty(False)
    timer_text = StringProperty("3:00")
    
    def on_enter(self):
        MDApp.get_running_app().update_affirmation_banner(self.name)
        self.reset_timer()
        
    def start_stop_timer(self):
        self.timer_active = not self.timer_active
        if self.timer_active:
            app = MDApp.get_running_app()
            app.jerry_ai.feed("calm", 100); app.jerry_ai.add_xp(5)
            self.timer_event = Clock.schedule_interval(self.update_timer, 1)
        else:
            if hasattr(self, 'timer_event'): self.timer_event.cancel()

    def update_timer(self, dt):
        self.timer_seconds -= 1
        # 2. Update the timer_text property every second.
        self.update_timer_text()
        if self.timer_seconds <= 0:
            self.timer_event.cancel()
            self.timer_active = False
            MDApp.get_running_app().root.ids.sm.current = 'jerry'

    def update_timer_text(self):
        """Formats the time and updates the StringProperty."""
        mins, secs = divmod(self.timer_seconds, 60)
        self.timer_text = f"{int(mins):02d}:{int(secs):02d}"
        
    def reset_timer(self):
        if hasattr(self, 'timer_event') and self.timer_event.is_scheduled(): self.timer_event.cancel()
        self.timer_active = False
        self.timer_seconds = 180
        self.update_timer_text()
        
    def on_leave(self):
        self.reset_timer()

class HushOSApp(MDApp):
    sound = None
    current_track_index = 0
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Indigo"
            
        return RootWidget()

    def on_start(self):
        app_dir = App.get_running_app().user_data_dir
        env_dest = os.path.join(app_dir, ".env")

        if not os.path.exists(env_dest):
            env_src = os.path.join(os.path.dirname(__file__), ".env")
            if os.path.exists(env_src):
                copyfile(env_src, env_dest)

        load_dotenv(dotenv_path=env_dest)

        Window.bind(on_request_close=self.on_request_close)
        self.setup_api_key_from_environment()
        self.jerry = self.root.ids.sm.get_screen('jerry')

        api_key = None
        # Priority 1: Try loading from config.json
        try:
            config_path = os.path.join(app_dir, "config.json")
            print(f"[HushOS] Trying to load API key from {config_path}")
            with open(config_path, "r") as f:
                secrets = json.load(f)
                api_key = secrets.get("HUSHOS_API_KEY")
                print(f"[HushOS] API key loaded from config.json: {'Yes' if api_key else 'No'}")
        except Exception as e:
            print(f"[HushOS] Could not load API key from config.json: {e}")
            # Priority 2: Try loading from .env if config.json failed
        if not api_key:
            api_key = os.environ.get("HUSHOS_API_KEY")
            print(f"[HushOS] API key loaded from .env: {'Yes' if api_key else 'No'}")
            
        self.jerry_ai = JerryAI(
            jerry=self.jerry,
            app=self,
            conversation_log_path=os.path.join(app_dir, "conversation_log.json"),
            jerry_memory_path=os.path.join(app_dir, "jerry_memory.json"),
            api_key=api_key,
        )

        from entries_log import EntriesLog  # If this class lives in a separate file
        log_path = os.path.join(app_dir, "entries_log.json")
        self.entries_log = EntriesLog(log_path)
        
        print(f"[HushOS] EntriesLog initialized with {len(self.entries_log.get_all_entries())} entries")

        animator = self.jerry.ids.animator
        animator.companion = self.jerry_ai.companion
        animator.start()
        
        self.root.ids.sm.current = 'splash'

    def setup_api_key_from_environment(self):
        """
        Loads API key from .env (if present) and persists it to config.json
        for consistent use across app sessions. Ensures Android runtime reads
        the correct file from the private app storage path.
        """

        env_path = os.path.join(self.user_data_dir, ".env")
        config_path = os.path.join(self.user_data_dir, "config.json")

        # First try to load the .env file directly
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        else:
            print(f"[HushOS] WARNING: .env not found at {env_path}")

        api_key = os.environ.get("HUSHOS_API_KEY")

        if api_key:
            print("[HushOS] API key loaded from .env — preparing config.json")
            if not os.path.exists(config_path):
                try:
                    with open(config_path, 'w') as f:
                        json.dump({"HUSHOS_API_KEY": api_key}, f)
                    print(f"[HushOS] Successfully created config.json at {config_path}")
                except Exception as e:
                    print(f"[HushOS] ERROR: Failed to write config.json: {e}")
        else:
            print("[HushOS] API key not found in environment — basic mode enabled")
        
    def on_stop(self):
        self.entries_log.save_entries()
        self.jerry_ai.end_session()
        self.jerry.save_state()
        
    def on_request_close(self, *args):
        self.on_stop()
        return True

    def on_pause(self):
        if self.sound and self.sound.state == 'play': self.sound.stop()
        if self.root.ids.sm.current == 'jerry':
            self.root.ids.sm.get_screen('jerry').ids.animator.stop()
        return True

    def on_resume(self):
        self.play_music()
        if self.root.ids.sm.current == 'jerry':
            self.root.ids.sm.get_screen('jerry').ids.animator.start()

    def change_screen(self, screen_name):
        self.root.ids.nav_drawer.set_state("close")
        sm = self.root.ids.sm
        if sm.current != screen_name:
            sm.current = screen_name

    # In main.py, inside the HushOSApp class

    def update_affirmation_banner(self, screen_name):
        try:
            # This is a more robust way to find the nested widgets
            sm = self.root.ids.sm
            # The screen manager's parent is the BoxLayout that holds the banner
            content_box = sm.parent
            # The children are in reverse order: [ScreenManager, MDLabel(banner), MDTopAppBar]
            banner = content_box.children[1]
        except Exception as e:
            print(f"Could not find the banner widget: {e}")
            return

        if screen_name == 'jerry':
            banner.height = 0
        else:
            banner.height = dp(40)
            self.jerry_ai.companion.update_needs()
            needs = self.jerry_ai.needs
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
                self.sound.volume = 0.3
                self.sound.play()
                self.sound.bind(on_stop=self.next_track)
                
    def next_track(self, *args):
        self.current_track_index = (self.current_track_index + 1) % len(PLAYLIST)
        self.play_music()

if __name__ == '__main__':
    HushOSApp().run()
