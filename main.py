import os
import sys
import time
import threading
import math
import json
import random
import openai
from datetime import datetime

# --- Kivy and App Dependencies ---
from kivymd.app import MDApp
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
from kivy.uix.image import Image as KivyImage
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.checkbox import CheckBox
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.lang import Builder
    
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
        if api_key is None:
            # Load from config.json
            try:
                app_dir = os.path.dirname(os.path.abspath(__file__))
                with open(os.path.join(app_dir, "config.json")) as f:
                    config = json.load(f)
                    api_key = config.get("openai_api_key")
            except Exception as e:
                print(f"Failed to load OpenAI API key: {e}")
        self.api_key = api_key
        openai.api_key = self.api_key

    def chat(self, messages, model="gpt-4", temperature=0.7, max_tokens=500):
        """
        messages: list of dicts, e.g.
          [{"role": "system", "content": "You are a gentle CBT coach."},
           {"role": "user", "content": "I feel anxious"}]
        """
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None

class JerryAI:
    MAX_HISTORY = 20

    def __init__(self, jerry, app, conversation_log_path, jerry_memory_path, api_key=None):
        print("[JerryAI] Initialized with api_key:", api_key)
        self.jerry = jerry
        self.app = app
        self.conversation_log = ConversationLog(conversation_log_path)
        self.memory = JerryMemory(jerry_memory_path)
        self.api_key = api_key
        self.chat_lock = threading.Lock()  # Thread safety lock
        self.is_thinking = False
        self.chat_history = []

        # Load API key robustly
        try:
            app_dir = App.get_running_app().directory
            config_path = os.path.join(app_dir, 'config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.api_key = self.api_key or config.get('api_key') or config.get('openai_api_key')
            print(f"Loaded API key from {config_path}: {'****' if self.api_key else 'None'}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Could not load config.json: {e}")

        if self.api_key:
            self.openai_client = OpenAIClient(api_key=self.api_key)
            print("Jerry AI initialized with OpenAI support.")
        else:
            self.openai_client = None
            print("Jerry AI initialized in basic mode (no API key provided).")

        self.system_prompt = "You are Jerry, a friendly, gentle, and supportive AI companion. Keep your responses brief and caring."

    def get_response(self, user_input, callback):
        self.is_thinking = True
        with self.chat_lock:
            self.chat_history.append({"role": "user", "content": user_input})
            if len(self.chat_history) > self.MAX_HISTORY:
                self.chat_history = self.chat_history[-self.MAX_HISTORY:]

        def get_response_thread():
            if self.openai_client:
                messages = [{"role": "system", "content": self.system_prompt}] + self.chat_history
                ai_response = self.openai_client.chat(messages=messages)
                if ai_response is None:
                    ai_response = self.get_fallback_response(user_input)
            else:
                ai_response = self.get_fallback_response(user_input)

            with self.chat_lock:
                self.chat_history.append({"role": "assistant", "content": ai_response})
                if len(self.chat_history) > self.MAX_HISTORY:
                    self.chat_history = self.chat_history[-self.MAX_HISTORY:]

            Clock.schedule_once(lambda dt, resp=ai_response: callback(resp))
            Clock.schedule_once(lambda dt: setattr(self, 'is_thinking', False))

        threading.Thread(target=get_response_thread, daemon=True).start()

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._post_init)
        self.anim_event = None
        self.thinking_event = None
        self.current_interval = None

    def _post_init(self, dt):
        self.app = MDApp.get_running_app()
        self.jerry = self.app.jerry
        self.theme = self.app.theme
        self._define_sprites()

    def _define_sprites(self):
        self.sprites = {
            "content": [[[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],[3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],[3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]],
            "low_insight": [[[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[3,1,1,1,4,4,1,1,1,1,4,4,1,1,1,3],[3,1,1,1,1,4,4,1,1,4,4,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,4,4,1,1,1,1,1,1,3],[3,1,1,1,1,1,4,1,1,4,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[3,1,1,1,4,4,1,1,1,1,4,4,1,1,1,3],[3,1,1,1,1,4,4,1,1,4,4,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,4,4,4,4,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]],
            "low_calm": [[[0,0,0,3,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,1,1,1,1,1,1,1,1,1,3,0,0,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,3,0,0],[3,1,1,1,4,4,1,1,1,4,4,1,1,1,3,0],[3,1,1,1,4,4,1,1,1,4,4,1,1,1,3,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,3,0,0],[0,0,3,1,1,1,1,1,1,1,1,1,3,0,0,0],[0,0,0,3,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],[[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,3,1,1,1,4,4,1,1,1,4,4,1,1,3,0],[0,3,1,1,1,4,4,1,1,1,4,4,1,1,3,0],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],[0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],[0,3,1,1,1,1,1,1,1,1,1,1,1,3,0,0],[0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],[0,0,0,3,3,3,3,3,3,3,3,3,3,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]],
            "thinking": [[[0,0,0,0,0,0,0,0,0,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,3,1,1,1,3,0,0,0],[0,0,0,0,0,0,0,3,1,1,1,1,1,3,0,0],[0,0,0,0,0,0,0,3,1,2,0,2,1,1,3,0],[0,0,0,0,0,0,3,1,1,1,1,1,1,1,3,0],[0,0,0,0,0,3,1,1,1,1,1,1,1,3,0,0],[0,0,0,0,0,0,3,3,3,3,3,3,3,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],[[0,0,0,0,0,0,0,0,0,3,3,3,0,0,0,0],[0,0,0,0,0,0,0,0,3,1,1,1,3,0,0,0],[0,0,0,0,0,0,0,3,1,1,1,1,1,3,0,0],[0,0,0,0,0,0,0,3,1,2,2,2,1,1,3,0],[0,0,0,0,0,0,3,1,1,1,1,1,1,1,3,0],[0,0,0,0,0,3,1,1,1,1,1,1,1,3,0,0],[0,0,0,0,0,0,3,3,3,3,3,3,3,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]]
        }
        self.sprites["low_clarity"] = self.sprites["content"]

    def start(self):
        if not hasattr(self, 'jerry'): return
        self.stop()
        self.is_thinking = False
        self.current_interval = 0.35
        self.anim_event = Clock.schedule_interval(self.animate, self.current_interval)

    def stop(self):
        if self.anim_event:
            self.anim_event.cancel()
            self.anim_event = None
        if self.thinking_event:
            self.thinking_event.cancel()
            self.thinking_event = None

    def animate(self, dt):
        self.jerry.update_needs()
        needs = self.jerry.needs
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

        # Medium bright blue body color (normalized 0-1)
        body_c = (0.3, 0.6, 0.9, 1)  # medium bright blue

        # Brighter blue outline
        outline_c = (0.5, 0.8, 1.0, 1)  # bright blue

        # White eyes
        eye_c = (1, 1, 1, 1)

        # Feature color: slightly lighter blue
        feature_c = (0.6, 0.85, 1.0, 1)

        # Optionally keep the low_insight tint adjustment
        if anim_key == 'low_insight':
            # Darker tint for body and features in low insight state
            body_c = (body_c[0]*0.8, body_c[1]*0.8, body_c[2]*0.8, 1)
            feature_c = (0.4, 0.57, 0.65, 1)  # darker feature blue

        with self.canvas:
            for y, row in enumerate(data):
                for x, p in enumerate(row):
                    if p > 0:
                        if p == 1:
                            Color(*body_c)
                        elif p == 2:
                            Color(*eye_c)
                        elif p == 3:
                            Color(*outline_c)
                        elif p == 4:
                            Color(*feature_c)
                        Rectangle(
                            pos=(x * pixel_size + offset_x, self.height - (y + 1) * pixel_size - offset_y),
                            size=(pixel_size, pixel_size)
                        )

class SplashScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(self.go_to_jerry, 2)

    def go_to_jerry(self, dt):
        if self.manager:
            self.manager.transition = FadeTransition(duration=0.5)
            self.manager.current = 'jerry'

class JerryScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(self.setup_screen)

    def setup_screen(self, dt):
        self.update_ui()
        # self.ids.animator.start() # This will only work if your 'animator' widget has a 'start' method
        
        # FIXED: Check if the layout has children, not if it has text
        if not self.ids.chat_log.children:
            self.add_message("Jerry", "It's good to see you again.")
            
        self.ids.user_entry.focus = True
        MDApp.get_running_app().update_affirmation_banner(self.name)

    def on_leave(self):
        # self.ids.animator.stop() # This will only work if your 'animator' widget has a 'stop' method
        # MDApp.get_running_app().ai.end_session()
        pass

    def update_ui(self, *args):
        jerry = MDApp.get_running_app().jerry
        jerry.update_needs()
        self.ids.clarity_bar.value = jerry.needs['clarity']
        self.ids.insight_bar.value = jerry.needs['insight']
        self.ids.calm_bar.value = jerry.needs['calm']
        self.ids.level_label.text = f"Level {jerry.level}"
        
        # FIXED: 'xp_bar' is a Label, so we set its .text property, not .value
        self.ids.xp_bar.text = f"XP: {jerry.xp} / {jerry.xp_to_next_level}"

    def send_message(self):
        # app = MDApp.get_running_app()
        # if app.ai.is_thinking: return
        user_text = self.ids.user_entry.text.strip()
        if not user_text: return
        
        self.add_message("You", user_text)
        self.ids.user_entry.text = ""
        # The AI call can be added back here. For now, we will simulate a response.
        self.handle_ai_response("This is a response from Jerry.")


    def handle_ai_response(self, response):
        if response.startswith("ACTION:"):
            MDApp.get_running_app().root.ids.sm.current = response.split(":")[1].strip()
        else:
            # FIXED: Directly call add_message. The complex "typing" effect is removed
            # as it's not compatible with adding widgets and is prone to errors.
            self.add_message("Jerry", response)

    def add_message(self, speaker, message):
        """
        FIXED: This function now creates a new MDLabel for each message
        and adds it to the 'chat_log' MDBoxLayout.
        """
        app = MDApp.get_running_app()
        speaker_color = app.theme_cls.primary_color if speaker == 'Jerry' else app.theme_cls.accent_color

        # Create a new label widget for the message
        message_label = MDLabel(
            text=f"[b][color={get_hex_from_color(speaker_color)}]{speaker}:[/color][/b] {message}",
            markup=True,
            size_hint_y=None,
            theme_text_color="Primary",
            valign="top"
        )
        
        # Allow the label to wrap text and define its height
        message_label.bind(
            width=lambda *x: message_label.setter('text_size')(message_label, (message_label.width, None)),
            texture_size=lambda *x: message_label.setter('height')(message_label, message_label.texture_size[1])
        )
        
        # Add the new widget to the layout
        self.ids.chat_log.add_widget(message_label)
        self.scroll_to_bottom()
        
    def scroll_to_bottom(self):
        # FIXED: Use the 'scroller' ID from the ScrollView to control scrolling
        scroll_view = self.ids.scroller
        Clock.schedule_once(lambda dt: setattr(scroll_view, 'scroll_y', 0), 0.1)

    # REMOVED: The 'type_out_message' function is not compatible with this corrected
    # approach and has been removed to ensure the app works correctly.

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
        theme = app.theme.COLORS

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
                background_color=get_color_from_hex(theme[key]),
                background_normal=''
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
                id='current_answer',
                text=self.flow_data.get(question_data["key"], ''),
                size_hint_y=None,
                height=dp(150),
                multiline=True,
                hint_text=question_data.get("hint", "")
            )
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
        body_box = self.ids.entries_log.ids.body_box
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
        MDApp.get_running_app().update_affirmation_banner(self.name)
        log_label = self.ids.history_log.ids.history_text
        log_label.text = ""
        
        convo_log = MDApp.get_running_app().ai.conversation_log.load_log()
        if not convo_log:
            log_label.text = "No conversation history."
        else:
            full_text = []
            for session in convo_log:
                timestamp = session.get('timestamp', 'Unknown Date')
                full_text.append(f"[b]Session: {timestamp}[/b]\n")
                
                conversation = session.get('conversation', [])
                for message in conversation:
                    role = message.get('role', 'model')
                    speaker = "Jerry" if role == 'model' else 'You'
                    
                    parts = message.get('parts', ['(Message not found)'])
                    text = parts[0] if isinstance(parts, list) and parts else '(Empty message)'
                    
                    full_text.append(f"[b]{speaker}:[/b] {text}\n")
                full_text.append("\n")
            log_label.text = "".join(full_text)
            
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
            app.jerry.feed("calm", 100); app.jerry.add_xp(5)
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
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Indigo"

        api_key = None
        try:
            with open("config.json") as f:
                secrets = json.load(f)
                api_key = secrets.get("api_key")
        except Exception as e:
            print(f"!!! Could not load API key from config.json: {e}. Jerry will be in basic mode.")

        user_data_dir = self.user_data_dir
        logs_path = os.path.join(user_data_dir, "logs")
        os.makedirs(logs_path, exist_ok=True)
        
        jerry_state_path = os.path.join(logs_path, "jerry_state.json")
        entries_log_path = os.path.join(logs_path, "entries_log.json")
        conversation_log_path = os.path.join(logs_path, "conversation_log.json")
        jerry_memory_path = os.path.join(logs_path, "jerry_memory.json")
        
        self.jerry = JerryCompanion(jerry_state_path)
        self.ai = JerryAI(jerry=self.jerry, app=self, conversation_log_path=conversation_log_path, jerry_memory_path=jerry_memory_path, api_key=api_key)
        self.entries_log = EntriesLog(entries_log_path)
        
        self.sound = None
        self.current_track_index = 0
        self.play_music()

        return RootWidget()

    def on_start(self):
        Window.bind(on_request_close=self.on_request_close)
        self.root.ids.sm.current = 'splash'
        
    def on_stop(self):
        self.ai.end_session()
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
                self.sound.volume = 0.3
                self.sound.play()
                self.sound.bind(on_stop=self.next_track)
                
    def next_track(self, *args):
        self.current_track_index = (self.current_track_index + 1) % len(PLAYLIST)
        self.play_music()

if __name__ == '__main__':
    HushOSApp().run()
