#!/usr/bin/env python3
"""
main.py — monolithic Hush app (all logic, sprites, screens, and data classes included)

Notes:
- This file contains all classes in a single module as requested.
- It errs on the side of defensive checks (many hasattr checks) so the app won't crash
  immediately if parts of the UI/KV aren't present at load time.
- The app expects a KV file (or Builder string) to create widgets with ids such as:
  root.ids.sm, root.ids.jerry_screen, etc. If you don't use KV, you will need to create
  those widgets in Python before on_start accesses them.
"""

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
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
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

# attempt to load .env if present (harmless)
try:
    load_dotenv()
except Exception:
    pass

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
    def __init__(self, filepath):
        self.filepath = filepath

    def load_log(self):
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def add_session(self, chat_history):
        if not chat_history:
            return
        log = self.load_log()
        session = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "conversation": chat_history}
        log.insert(0, session)
        try:
            with open(self.filepath, 'w') as f:
                json.dump(log, f, indent=4)
        except Exception as e:
            print(f"[ConversationLog] Error saving log: {e}")

class JerryMemory:
    def __init__(self, filepath):
        self.filepath = filepath

    def load_memory(self):
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_memory(self, memory_dict):
        try:
            with open(self.filepath, 'w') as f:
                json.dump(memory_dict, f, indent=4)
        except Exception as e:
            print(f"[JerryMemory] Error saving memory: {e}")

class EntriesLog:
    def __init__(self, entries_filepath):
        self.filepath = entries_filepath
        self.entries = self.load_entries()

    def load_entries(self):
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def add_entry(self, entry_type, data):
        entry = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "type": entry_type, "data": data}
        self.entries.insert(0, entry)
        self.save_entries()

    def save_entries(self):
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.entries, f, indent=4)
        except Exception as e:
            print(f"[EntriesLog] Error saving entries: {e}")

    def get_all_entries(self):
        return self.entries

class JerryCompanion:
    def __init__(self, state_filepath):
        self.state_filepath = state_filepath
        self.needs = {"clarity": 100, "insight": 100, "calm": 100}
        self.last_fed = {"clarity": time.time(), "insight": time.time(), "calm": time.time()}
        self.decay_rates_hours = {"clarity": 24, "insight": 48, "calm": 12}
        self.xp = 0
        self.level = 1
        self.xp_to_next_level = 100
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
        except (FileNotFoundError, json.JSONDecodeError):
            # create initial state file
            self.save_state()
        except Exception as e:
            print(f"[JerryCompanion] Error loading state: {e}")
            self.save_state()

    def save_state(self):
        try:
            with open(self.state_filepath, 'w') as f:
                json.dump({
                    "needs": self.needs,
                    "last_fed": self.last_fed,
                    "xp": self.xp,
                    "level": self.level,
                    "xp_to_next_level": self.xp_to_next_level
                }, f, indent=4)
        except Exception as e:
            print(f"[JerryCompanion] Error saving state: {e}")

    def update_needs(self):
        now = time.time()
        for n, t in self.last_fed.items():
            try:
                decay_rate = self.decay_rates_hours.get(n, 24)
                self.needs[n] = max(0, 100 - ((now - t) / 3600 / decay_rate) * 100)
            except Exception:
                self.needs[n] = self.needs.get(n, 100)

    def feed(self, n, a=100):
        self.update_needs()
        if n in self.needs:
            self.needs[n] = min(100, self.needs[n] + a)
            self.last_fed[n] = time.time()
            self.save_state()

    def add_xp(self, a):
        self.xp += a
        if self.xp >= self.xp_to_next_level:
            self.level_up()
        self.save_state()

    def level_up(self):
        self.level += 1
        self.xp -= self.xp_to_next_level
        self.xp_to_next_level = int(self.xp_to_next_level * 1.5)

class JerryAI:
    MAX_HISTORY = 20

    def __init__(self, jerry, app, conversation_log_path, jerry_memory_path, api_key=None):
        app_dir = app.user_data_dir if hasattr(app, 'user_data_dir') else os.path.dirname(os.path.abspath(__file__))
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

        if self.api_key:
            openai.api_key = self.api_key
            print("[JerryAI] Initialized with OpenAI support.")
        else:
            print("[JerryAI] No API key found — running in basic mode.")

        self.system_prompt = "You are Jerry, a friendly, gentle, and supportive AI companion. Keep your responses brief and caring."

    @property
    def needs(self):
        return self.companion.needs

    def get_response_thread(self, user_input, callback):
        def run():
            if self.api_key:
                try:
                    messages = [{"role": "system", "content": self.system_prompt}] + self.chat_history
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=messages,
                        temperature=0.7
                    )
                    # compatibility: response.choices[0].message.content or response.choices[0].text
                    ai_response = ""
                    try:
                        ai_response = response.choices[0].message.content.strip()
                    except Exception:
                        ai_response = getattr(response.choices[0], "text", "").strip()
                        if not ai_response:
                            ai_response = "I'm here to listen."
                except Exception as e:
                    print(f"[JerryAI] OpenAI error: {e}")
                    ai_response = self.get_fallback_response(user_input)
            else:
                ai_response = self.get_fallback_response(user_input)

            with self.chat_lock:
                self.chat_history.append({"role": "user", "content": user_input})
                self.chat_history.append({"role": "assistant", "content": ai_response})
                if len(self.chat_history) > self.MAX_HISTORY:
                    self.chat_history = self.chat_history[-self.MAX_HISTORY:]

            # send response back to UI thread
            try:
                Clock.schedule_once(lambda dt, resp=ai_response: callback(resp))
                Clock.schedule_once(lambda dt: setattr(self, 'is_thinking', False))
            except Exception:
                # fallback: call directly (dangerous, but doesn't crash)
                try:
                    callback(ai_response)
                except Exception as e:
                    print(f"[JerryAI] Callback error: {e}")

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
    evolution_level = NumericProperty(0)
    aura_color = None

    def __init__(self, companion=None, **kwargs):
        super().__init__(**kwargs)
        self.companion = companion
        self.anim_event = None
        self.thinking_event = None
        self.current_interval = None
        Clock.schedule_once(self._post_init)

    def _post_init(self, dt):
        app = MDApp.get_running_app()
        if app:
            self.app = app
            if hasattr(app, 'jerry_ai'):
                self.jerry = app.jerry_ai
            self.theme_cls = app.theme_cls
            self._define_sprites()
            # Start only if companion exists or will exist
            self.start()

    def _define_sprites(self):
        # Sprites: lists of 16x16 integer matrices, multiple frames per animation.
        # Kept the original sprite data provided by you.
        self.sprites = {
            "content": [[[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],
                         [0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],
                         [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                         [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                         [3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],
                         [3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],
                         [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                         [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                         [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                         [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                         [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                         [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                         [0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],
                         [0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],
                         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],
                        [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                         [0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],
                         [0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],
                         [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                         [3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],
                         [3,1,1,1,1,2,2,1,1,1,2,2,1,1,1,3],
                         [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                         [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                         [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                         [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                         [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                         [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                         [0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],
                         [0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],
                         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]],
            "low_insight": [[[0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],
                             [0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],
                             [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                             [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                             [3,1,1,1,4,4,1,1,1,1,4,4,1,1,1,3],
                             [3,1,1,1,1,4,4,1,1,4,4,1,1,1,1,3],
                             [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                             [3,1,1,1,1,1,1,4,4,1,1,1,1,1,1,3],
                             [3,1,1,1,1,1,4,1,1,4,1,1,1,1,1,3],
                             [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                             [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                             [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                             [0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],
                             [0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],
                            [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],
                             [0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],
                             [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                             [3,1,1,1,4,4,1,1,1,1,4,4,1,1,1,3],
                             [3,1,1,1,1,4,4,1,1,4,4,1,1,1,1,3],
                             [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                             [3,1,1,1,1,1,4,4,4,4,1,1,1,1,1,3],
                             [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                             [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                             [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                             [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                             [0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],
                             [0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]],
            "low_calm": [[[0,0,0,3,3,3,3,3,3,3,3,3,0,0,0,0],
                          [0,0,3,1,1,1,1,1,1,1,1,1,3,0,0,0],
                          [0,3,1,1,1,1,1,1,1,1,1,1,1,3,0,0],
                          [3,1,1,1,4,4,1,1,1,4,4,1,1,1,3,0],
                          [3,1,1,1,4,4,1,1,1,4,4,1,1,1,3,3],
                          [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                          [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                          [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                          [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                          [0,3,1,1,1,1,1,1,1,1,1,1,1,3,0,0],
                          [0,0,3,1,1,1,1,1,1,1,1,1,3,0,0,0],
                          [0,0,0,3,3,3,3,3,3,3,3,3,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],
                         [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0],
                          [0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],
                          [0,3,1,1,1,4,4,1,1,1,4,4,1,1,3,0],
                          [0,3,1,1,1,4,4,1,1,1,4,4,1,1,3,0],
                          [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                          [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                          [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
                          [0,3,1,1,1,1,1,1,1,1,1,1,1,1,3,0],
                          [0,3,1,1,1,1,1,1,1,1,1,1,1,3,0,0],
                          [0,0,3,3,1,1,1,1,1,1,1,1,3,3,0,0],
                          [0,0,0,3,3,3,3,3,3,3,3,3,3,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]],
            "thinking": [[[0,0,0,0,0,0,0,0,0,3,3,3,0,0,0,0],
                          [0,0,0,0,0,0,0,0,3,1,1,1,3,0,0,0],
                          [0,0,0,0,0,0,0,3,1,1,1,1,1,3,0,0],
                          [0,0,0,0,0,0,0,3,1,2,0,2,1,1,3,0],
                          [0,0,0,0,0,0,3,1,1,1,1,1,1,1,3,0],
                          [0,0,0,0,0,3,1,1,1,1,1,1,1,3,0,0],
                          [0,0,0,0,0,0,3,3,3,3,3,3,3,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],
                         [[0,0,0,0,0,0,0,0,0,3,3,3,0,0,0,0],
                          [0,0,0,0,0,0,0,0,3,1,1,1,3,0,0,0],
                          [0,0,0,0,0,0,0,3,1,1,1,1,1,3,0,0],
                          [0,0,0,0,0,0,0,3,1,2,2,2,1,1,3,0],
                          [0,0,0,0,0,0,3,1,1,1,1,1,1,1,3,0],
                          [0,0,0,0,0,3,1,1,1,1,1,1,1,3,0,0],
                          [0,0,0,0,0,0,3,3,3,3,3,3,3,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]]
        }
        # alias
        self.sprites["low_clarity"] = self.sprites["content"]

    def evolve(self, level):
        self.evolution_level = level
        if self.aura_color:
            try:
                Animation.cancel_all(self.aura_color)
            except Exception:
                pass
            self.aura_color = None

        if self.evolution_level >= 2:
            self.start_aura_animation()

    def start_aura_animation(self):
        # aura_color is an Instruction; animate its 'rgba' alpha component via property 'a'
        # Create a Color instruction; animate attribute 'a' on that Color object.
        self.aura_color = Color(rgba=(0.5, 0.8, 1, 0))
        max_alpha = 0.4 if self.evolution_level >= 3 else 0.2
        anim = Animation(a=max_alpha, d=3) + Animation(a=0.05, d=3)
        anim.repeat = True
        anim.start(self.aura_color)

    def start(self):
        # ensure necessary attributes exist
        if not hasattr(self, 'jerry') and not hasattr(self, 'companion'):
            # still ok — start will be attempted after post_init
            return
        self.stop()
        self.is_thinking = False
        self.current_interval = 0.35
        try:
            self.anim_event = Clock.schedule_interval(self.animate, self.current_interval)
        except Exception as e:
            print(f"[JerryAnimator] schedule error: {e}")

    def stop(self):
        try:
            if self.anim_event:
                self.anim_event.cancel()
                self.anim_event = None
            if self.thinking_event:
                self.thinking_event.cancel()
                self.thinking_event = None
            if self.aura_color:
                try:
                    Animation.cancel_all(self.aura_color)
                except Exception:
                    pass
                self.aura_color = None
        except Exception as e:
            print(f"[JerryAnimator] stop error: {e}")

    def animate(self, dt):
        if not self.companion:
            return
        try:
            self.companion.update_needs()
            needs = self.companion.needs
            # find min need key
            min_need = min(needs, key=needs.get)
            anim_key = f"low_{min_need}" if needs[min_need] < 50 else "content"
            new_interval = 0.15 if anim_key == "low_calm" else 0.35

            if new_interval != self.current_interval:
                if self.anim_event:
                    self.anim_event.cancel()
                self.anim_event = Clock.schedule_interval(self.animate, new_interval)
                self.current_interval = new_interval

            if hasattr(self, 'sprites') and anim_key in self.sprites:
                frames = self.sprites[anim_key]
                self.anim_frame = (self.anim_frame + 1) % len(frames)
                self.draw_sprite(frames[self.anim_frame], anim_key)
        except Exception as e:
            print(f"[JerryAnimator] animate error: {e}")

    def show_thinking_sprite(self):
        try:
            self.stop()
            self.is_thinking = True
            self.anim_frame = 0
            self.thinking_event = Clock.schedule_interval(self.animate_thinking, 0.5)
        except Exception as e:
            print(f"[JerryAnimator] show_thinking_sprite error: {e}")

    def animate_thinking(self, dt):
        try:
            if hasattr(self, 'sprites') and 'thinking' in self.sprites:
                frames = self.sprites["thinking"]
                self.anim_frame = (self.anim_frame + 1) % len(frames)
                self.draw_sprite(frames[self.anim_frame], 'thinking')
        except Exception as e:
            print(f"[JerryAnimator] animate_thinking error: {e}")

    def draw_sprite(self, data, anim_key):
        # safety check for size
        if not data or self.width == 0 or self.height == 0:
            return

        try:
            self.canvas.clear()
            pixel_size = self.width / 18
            offset_x = (self.width - (16 * pixel_size)) / 2
            offset_y = (self.height - (16 * pixel_size)) / 2

            body_c = (0.3, 0.6, 0.9, 1)
            outline_c = (0.5, 0.8, 1.0, 1)
            eye_c = (1, 1, 1, 1)
            feature_c = (0.6, 0.85, 1.0, 1)

            if self.evolution_level >= 1:
                body_c = (0.4, 0.6, 1.0, 1)
                outline_c = (0.6, 0.9, 1.0, 1)

            if self.evolution_level >= 3:
                body_c = (body_c[0] * 0.9, body_c[1] * 0.9, body_c[2] * 0.7, 1)
                feature_c = (1.0, 0.9, 0.5, 1)

            if anim_key == 'low_insight':
                body_c = (body_c[0]*0.8, body_c[1]*0.8, body_c[2]*0.8, 1)
                feature_c = (0.4, 0.57, 0.65, 1)

            with self.canvas:
                if self.evolution_level >= 2 and self.aura_color:
                    try:
                        self.canvas.add(self.aura_color)
                    except Exception:
                        pass
                    aura_size = (16 * pixel_size + 40, 16 * pixel_size + 40)
                    aura_pos = (offset_x - 20, offset_y - 20)
                    Ellipse(pos=aura_pos, size=aura_size)

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
        except Exception as e:
            print(f"[JerryAnimator] draw_sprite error: {e}")

class SplashScreen(Screen):
    def on_enter(self):
        layout = BoxLayout()
        # Check if splash image exists, use placeholder if not
        try:
            if os.path.exists(os.path.join(ASSETS_PATH, 'new_splash.png')):
                splash = Image(source=os.path.join(ASSETS_PATH, 'new_splash.png'), allow_stretch=True, keep_ratio=False)
            else:
                splash = Label(text='HUSH\nLoading...', font_size='24sp', halign='center')
        except Exception as e:
            print(f"Error loading splash image: {e}")
            splash = Label(text='HUSH\nLoading...', font_size='24sp', halign='center')

        layout.add_widget(splash)
        self.add_widget(layout)

        Clock.schedule_once(self.go_to_jerry, 2)

    def go_to_jerry(self, dt):
        if self.manager:
            try:
                self.manager.transition = FadeTransition(duration=0.5)
                self.manager.current = 'jerry'
            except Exception as e:
                print(f"[SplashScreen] go_to_jerry error: {e}")

class JerryScreen(Screen):
    last_known_level = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.jerry_ai = None

    def on_enter(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'jerry_ai'):
            self.jerry_ai = app.jerry_ai

        Clock.schedule_once(self.setup_screen)

    def setup_screen(self, dt):
        self.update_ui()
        # Check if chat_log exists before accessing
        if hasattr(self, 'ids') and hasattr(self.ids, 'chat_log'):
            try:
                if not self.ids.chat_log.children:
                    self.add_message("Jerry", "It's good to see you again.")
                if hasattr(self.ids, 'user_entry'):
                    self.ids.user_entry.focus = True
            except Exception as e:
                print(f"[JerryScreen] setup_screen error: {e}")

        app = MDApp.get_running_app()
        if app and hasattr(app, 'update_affirmation_banner'):
            app.update_affirmation_banner(self.name)

    def update_needs(self):
        if self.jerry_ai and hasattr(self.jerry_ai, 'companion'):
            self.jerry_ai.companion.update_needs()

    def update_ui(self, *args):
        if not self.jerry_ai or not hasattr(self.jerry_ai, 'companion'):
            return

        try:
            self.jerry_ai.companion.update_needs()

            # Safely access UI elements
            if hasattr(self, 'ids'):
                if hasattr(self.ids, 'clarity_bar'):
                    self.ids.clarity_bar.value = self.jerry_ai.needs.get('clarity', 0)
                if hasattr(self.ids, 'insight_bar'):
                    self.ids.insight_bar.value = self.jerry_ai.needs.get('insight', 0)
                if hasattr(self.ids, 'calm_bar'):
                    self.ids.calm_bar.value = self.jerry_ai.needs.get('calm', 0)
                if hasattr(self.ids, 'level_label'):
                    self.ids.level_label.text = f"Level {self.jerry_ai.companion.level}"
                if hasattr(self.ids, 'xp_bar'):
                    self.ids.xp_bar.text = f"XP: {self.jerry_ai.companion.xp} / {self.jerry_ai.companion.xp_to_next_level}"
        except Exception as e:
            print(f"[JerryScreen] update_ui error: {e}")

        if self.jerry_ai.companion.level > self.last_known_level:
            self.check_for_evolution(self.jerry_ai.companion.level)
            self.last_known_level = self.jerry_ai.companion.level

    def check_for_evolution(self, current_level):
        if not hasattr(self, 'ids'):
            return

        try:
            if hasattr(self.ids, 'animator'):
                animator = self.ids.animator
                evolution_stage = current_level // 10
                animator.evolve(evolution_stage)

            if hasattr(self.ids, 'jerry_title_label'):
                title_label = self.ids.jerry_title_label
                evolution_stage = current_level // 10

                if evolution_stage == 1:
                    title_label.text = "Jerry the Listener"
                elif evolution_stage == 2:
                    title_label.text = "Calm Companion"
                elif evolution_stage == 3:
                    title_label.text = "Beacon of Insight"
                else:
                    title_label.text = ""
        except Exception as e:
            print(f"[JerryScreen] check_for_evolution error: {e}")

    def send_message(self):
        if not hasattr(self, 'ids') or not hasattr(self.ids, 'user_entry'):
            return

        user_text = self.ids.user_entry.text.strip()
        if not user_text:
            return

        self.add_message("You", user_text)
        self.ids.user_entry.text = ""

        if self.jerry_ai:
            self.jerry_ai.get_response_thread(user_text, self.handle_ai_response)

    def handle_ai_response(self, response):
        try:
            if response.startswith("ACTION:"):
                app = MDApp.get_running_app()
                if app and hasattr(app, 'root') and hasattr(app.root, 'ids') and 'sm' in app.root.ids:
                    app.root.ids.sm.current = response.split(":", 1)[1].strip()
            else:
                self.add_message("Jerry", response)
        except Exception as e:
            print(f"[JerryScreen] handle_ai_response error: {e}")

    def add_message(self, speaker, message):
        if not hasattr(self, 'ids') or not hasattr(self.ids, 'chat_log'):
            return

        app = MDApp.get_running_app()
        if not app:
            return

        speaker_color = app.theme_cls.primary_color if speaker == 'Jerry' else app.theme_cls.accent_color

        try:
            message_label = MDLabel(
                text=f"[b][color={get_hex_from_color(speaker_color)}]{speaker}:[/color][/b] {message}",
                markup=True,
                size_hint_y=None,
                theme_text_color="Primary",
                valign="top"
            )

            message_label.bind(
                width=lambda *x: message_label.setter('text_size')(message_label, (message_label.width, None)),
                texture_size=lambda *x: message_label.setter('height')(message_label, message_label.texture_size[1])
            )

            self.ids.chat_log.add_widget(message_label)
            self.scroll_to_bottom()
        except Exception as e:
            print(f"[JerryScreen] add_message error: {e}")

    def scroll_to_bottom(self):
        if hasattr(self, 'ids') and hasattr(self.ids, 'scroller'):
            scroll_view = self.ids.scroller
            try:
                Clock.schedule_once(lambda dt: setattr(scroll_view, 'scroll_y', 0), 0.1)
            except Exception:
                pass

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_first_setup = False

    def on_enter(self):
        app = MDApp.get_running_app()

        if not self.is_first_setup and app and hasattr(app, 'update_affirmation_banner'):
            app.update_affirmation_banner(self.name)

        self.load_current_settings()

    def load_current_settings(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'api_key') and app.api_key and hasattr(self, 'ids') and hasattr(self.ids, 'api_key_input'):
            self.ids.api_key_input.text = app.api_key

    def save_api_key(self):
        if not hasattr(self, 'ids') or not hasattr(self.ids, 'api_key_input'):
            return

        api_key = self.ids.api_key_input.text.strip()
        app = MDApp.get_running_app()
        if app and hasattr(app, 'set_api_key'):
            app.set_api_key(api_key)

        self.show_message("API key saved successfully!")

        if self.is_first_setup:
            self.is_first_setup = False
            app = MDApp.get_running_app()
            if app and hasattr(app, 'root') and hasattr(app.root, 'ids') and 'sm' in app.root.ids:
                app.root.ids.sm.current = "splash"
        else:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'root') and hasattr(app.root, 'ids') and 'sm' in app.root.ids:
                app.root.ids.sm.current = "jerry"

    def skip_setup(self):
        if self.is_first_setup:
            app = MDApp.get_running_app()
            if app:
                app.setup_completed = True
                if hasattr(app, 'save_settings'):
                    app.save_settings()
                self.is_first_setup = False
                if hasattr(app, 'root') and hasattr(app.root, 'ids') and 'sm' in app.root.ids:
                    app.root.ids.sm.current = "splash"

    def show_message(self, message):
        if hasattr(self, 'ids') and hasattr(self.ids, 'message_label'):
            self.ids.message_label.text = message
            self.ids.message_label.opacity = 1

            def fade_message(dt):
                anim = Animation(opacity=0, duration=0.5)
                anim.start(self.ids.message_label)

            Clock.schedule_once(fade_message, 3)

class CheckinScreen(Screen):
    checkin_step = NumericProperty(0)

    def on_enter(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'update_affirmation_banner'):
            app.update_affirmation_banner(self.name)
        self.checkin_data = {}
        self.checkin_step = 0
        self.display_step()

    def display_step(self):
        if not hasattr(self, 'ids') or not hasattr(self.ids, 'checkin_content'):
            return

        try:
            self.ids.checkin_content.clear_widgets()
            app = MDApp.get_running_app()
            if not app:
                return

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

            if hasattr(self.ids, 'progress_bar'):
                self.ids.progress_bar.value = (self.checkin_step + 1) / len(steps) * 100
            if hasattr(self.ids, 'checkin_title_label'):
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
        except Exception as e:
            print(f"[CheckinScreen] display_step error: {e}")

    def next_step(self, category, choice):
        try:
            self.checkin_data[category] = choice
            self.checkin_step += 1
            self.display_step()
        except Exception as e:
            print(f"[CheckinScreen] next_step error: {e}")

    def complete_checkin(self):
        app = MDApp.get_running_app()
        if not app:
            return

        summary = f"Emotionally feeling {self.checkin_data.get('emotion', 'N/A')}, physically {self.checkin_data.get('physical', 'N/A')}, mentally {self.checkin_data.get('mental', 'N/A')}."
        log_data = {"summary": summary, "details": self.checkin_data}

        if hasattr(app, 'entries_log'):
            app.entries_log.add_entry("Check-in", log_data)
        if hasattr(app, 'jerry_ai') and app.jerry_ai and hasattr(app.jerry_ai, 'companion'):
            app.jerry_ai.companion.feed("clarity", 50)
            app.jerry_ai.companion.add_xp(10)

        if hasattr(app, 'root') and hasattr(app.root, 'ids') and 'sm' in app.root.ids:
            app.root.ids.sm.current = 'jerry'

class TherapyScreenBase(Screen):
    flow_step = NumericProperty(0)

    def on_enter(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'update_affirmation_banner'):
            app.update_affirmation_banner(self.name)
        self.flow_data = {}
        self.flow_step = 0
        self.questions = []
        self.checklist = {}
        self.entry_type = ""
        self.setup_flow()
        self.display_step()

    def setup_flow(self):
        pass

    def display_step(self):
        if not hasattr(self, 'ids') or not hasattr(self.ids, 'content_box'):
            return

        try:
            content_box = self.ids.content_box
            content_box.clear_widgets()
            num_questions = len(self.questions)
            if self.flow_step < num_questions:
                self.display_question_step()
            elif self.flow_step == num_questions and self.checklist:
                self.display_checklist_step()
            else:
                self.complete_flow()
        except Exception as e:
            print(f"[TherapyScreenBase] display_step error: {e}")

    def display_question_step(self):
        try:
            if not self.questions or self.flow_step >= len(self.questions):
                return

            question_data = self.questions[self.flow_step]

            if hasattr(self.ids, 'title_label'):
                self.ids.title_label.text = question_data["question"]
            if hasattr(self.ids, 'next_button'):
                self.ids.next_button.text = 'Next'

            if not hasattr(self.ids, 'content_box'):
                return

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
                    text=self.flow_data.get(question_data["key"], ""),
                    multiline=True,
                    size_hint_y=None,
                    height=dp(100),
                    hint_text=question_data.get("hint", "")
                )
                # Clear existing bindings before adding new ones
                if hasattr(self.ids, 'next_button'):
                    try:
                        self.ids.next_button.unbind(on_press=self.get_text_input_answer)
                    except Exception:
                        pass
                    self.ids.next_button.bind(on_press=self.get_text_input_answer(question_data["key"], text_input))
                content_box.add_widget(text_input)
        except Exception as e:
            print(f"[TherapyScreenBase] display_question_step error: {e}")

    def get_text_input_answer(self, key, text_input):
        def on_press_callback(instance):
            try:
                self.flow_data[key] = text_input.text
                self.flow_step += 1
                self.display_step()
            except Exception as e:
                print(f"[TherapyScreenBase] get_text_input_answer callback error: {e}")
        return on_press_callback

    def set_rating_answer(self, key, value):
        self.flow_data[key] = value

    def display_checklist_step(self):
        if not hasattr(self, 'ids') or not hasattr(self.ids, 'title_label') or not hasattr(self.ids, 'next_button') or not hasattr(self.ids, 'content_box'):
            return

        try:
            self.ids.title_label.text = "Which cognitive distortions apply?"
            self.ids.next_button.text = 'Complete'
            content_box = self.ids.content_box
            content_box.clear_widgets()

            scroll_view = ScrollView()
            checklist_grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(10))
            checklist_grid.bind(minimum_height=checklist_grid.setter('height'))

            for distortion, definition in self.checklist.items():
                box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), padding=dp(5), spacing=dp(10))
                chk = CheckBox(size_hint_x=None, width=dp(30))
                chk.bind(active=lambda instance, value, d=distortion: self.toggle_checklist_item(d, value))

                label = MDLabel(text=f"[b]{distortion}:[/b] {definition}", markup=True)
                box.add_widget(chk)
                box.add_widget(label)
                checklist_grid.add_widget(box)

            scroll_view.add_widget(checklist_grid)
            content_box.add_widget(scroll_view)

            # Clear existing bindings
            try:
                self.ids.next_button.unbind(on_press=self.get_text_input_answer)
            except Exception:
                pass
            self.ids.next_button.bind(on_press=lambda x: self.complete_flow())
        except Exception as e:
            print(f"[TherapyScreenBase] display_checklist_step error: {e}")

    def toggle_checklist_item(self, item, is_active):
        try:
            if is_active:
                if "distortions" not in self.flow_data:
                    self.flow_data["distortions"] = []
                if item not in self.flow_data["distortions"]:
                    self.flow_data["distortions"].append(item)
            else:
                if "distortions" in self.flow_data and item in self.flow_data["distortions"]:
                    self.flow_data["distortions"].remove(item)
        except Exception as e:
            print(f"[TherapyScreenBase] toggle_checklist_item error: {e}")

    def complete_flow(self):
        app = MDApp.get_running_app()
        if not app:
            return

        try:
            if hasattr(app, 'entries_log'):
                app.entries_log.add_entry(self.entry_type, self.flow_data)

            if hasattr(app, 'jerry_ai') and app.jerry_ai and hasattr(app.jerry_ai, 'companion'):
                if self.entry_type == "CBT":
                    app.jerry_ai.companion.feed("insight", 50)
                    app.jerry_ai.companion.add_xp(20)
                elif self.entry_type == "DBT":
                    app.jerry_ai.companion.feed("calm", 50)
                    app.jerry_ai.companion.add_xp(20)

            if hasattr(app, 'root') and hasattr(app.root, 'ids') and 'sm' in app.root.ids:
                app.root.ids.sm.current = 'jerry'
        except Exception as e:
            print(f"[TherapyScreenBase] complete_flow error: {e}")

class CBTFlowScreen(TherapyScreenBase):
    def setup_flow(self):
        self.questions = CBT_QUESTIONS
        self.checklist = COGNITIVE_DISTORTIONS
        self.entry_type = "CBT"

class DBTFlowScreen(TherapyScreenBase):
    def setup_flow(self):
        self.questions = DBT_QUESTIONS
        self.checklist = DBT_SKILLS
        self.entry_type = "DBT"

# --- MAIN APP CLASS ---
class HushApp(MDApp):
    dialog = None
    affirmation_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Avoid exceptions if on_request_close isn't present yet; bind to Window safely
        try:
            Window.bind(on_request_close=self.on_request_close)
        except Exception:
            pass
        self.setup_completed = False
        self.font_size_multiplier = 1.0
        # default theme settings (will be overridden by load_settings)
        try:
            self.theme_cls.theme_style = "Dark"
        except Exception:
            pass
        self.api_key = ""

    def build(self):
        # Set up theme defaults
        try:
            self.theme_cls.theme_style = "Dark"
            self.theme_cls.primary_palette = "Indigo"
        except Exception:
            pass

        # load settings (uses self.user_data_dir)
        self.load_settings()

        # Return RootWidget — make sure your KV or Python creates expected child widgets (screen manager etc.)
        return RootWidget()

    def load_settings(self):
        # user_data_dir should exist (MDApp provides it). Use fallback if not present.
        try:
            settings_path = os.path.join(self.user_data_dir, "app_settings.json")
        except Exception:
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_settings.json")

        if not os.path.exists(settings_path):
            self.save_settings()
            return

        try:
            with open(settings_path, "r") as f:
                settings = json.load(f)
                try:
                    self.theme_cls.theme_style = settings.get("theme_style", "Dark")
                except Exception:
                    pass
                self.set_font_size(settings.get("font_size", 1.0))
                self.api_key = settings.get("HUSHOS_API_KEY", "")
                self.setup_completed = settings.get("setup_completed", False)
        except (FileNotFoundError, json.JSONDecodeError):
            self.font_size_multiplier = 1.0
            try:
                self.theme_cls.theme_style = "Dark"
            except Exception:
                pass
            self.api_key = ""
            self.setup_completed = False
            self.save_settings()
        except Exception as e:
            print(f"[HushApp] load_settings unexpected error: {e}")

    def save_settings(self):
        try:
            settings_path = os.path.join(self.user_data_dir, "app_settings.json")
        except Exception:
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_settings.json")

        try:
            settings = {
                "theme_style": getattr(self.theme_cls, "theme_style", "Dark"),
                "font_size": self.font_size_multiplier,
                "HUSHOS_API_KEY": self.api_key,
                "setup_completed": self.setup_completed,
            }
            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"[HushApp] Error saving settings: {e}")

    def toggle_theme_style(self):
        try:
            current = getattr(self.theme_cls, "theme_style", "Dark")
            self.theme_cls.theme_style = "Dark" if current == "Light" else "Light"
            self.save_settings()
        except Exception as e:
            print(f"[HushApp] toggle_theme_style error: {e}")

    def set_font_size(self, multiplier):
        try:
            self.font_size_multiplier = float(multiplier)
            self.save_settings()
        except Exception as e:
            print(f"[HushApp] set_font_size error: {e}")

    def set_api_key(self, api_key):
        try:
            self.api_key = api_key.strip()
            self.setup_completed = True
            self.save_settings()
            if hasattr(self, "jerry_ai") and self.jerry_ai:
                self.jerry_ai.api_key = self.api_key
                if self.api_key:
                    openai.api_key = self.api_key
        except Exception as e:
            print(f"[HushApp] set_api_key error: {e}")

    def on_start(self):
        try:
            # Ensure user data paths exist
            try:
                base_dir = self.user_data_dir
            except Exception:
                base_dir = os.path.dirname(os.path.abspath(__file__))

            self.conversation_log_path = os.path.join(base_dir, "conversation_log.json")
            self.jerry_memory_path = os.path.join(base_dir, "jerry_memory.json")
            self.entries_filepath = os.path.join(base_dir, "entries.json")

            self.entries_log = EntriesLog(self.entries_filepath)

            # Safely add screens if screen manager exists in root ids
            if hasattr(self.root, "ids") and "sm" in self.root.ids:
                sm = self.root.ids.sm
                # avoid adding duplicates; check names
                existing_names = set()
                for w in sm.children:
                    if hasattr(w, 'name'):
                        existing_names.add(w.name)
                if 'settings' not in existing_names:
                    sm.add_widget(SettingsScreen(name="settings"))
                if 'checkin' not in existing_names:
                    sm.add_widget(CheckinScreen(name="checkin"))
                if 'cbt_flow' not in existing_names:
                    sm.add_widget(CBTFlowScreen(name="cbt_flow"))
                if 'dbt_flow' not in existing_names:
                    sm.add_widget(DBTFlowScreen(name="dbt_flow"))

            # Initialize JerryAI with safe access to animator
            jerry_animator = None
            if (
                hasattr(self.root, "ids")
                and "jerry_screen" in self.root.ids
                and hasattr(self.root.ids.jerry_screen, "ids")
                and "animator" in self.root.ids.jerry_screen.ids
            ):
                jerry_animator = self.root.ids.jerry_screen.ids.animator

            self.jerry_ai = JerryAI(
                jerry_animator,
                self,
                self.conversation_log_path,
                self.jerry_memory_path,
                self.api_key,
            )

            # Decide startup screen
            if not self.setup_completed:
                if hasattr(self.root, "ids") and "sm" in self.root.ids:
                    self.root.ids.sm.current = "settings"
                # flag first-setup if settings_screen widget is named differently,
                # the SettingsScreen added above uses name 'settings'
                if hasattr(self.root, "ids") and "settings_screen" in self.root.ids:
                    try:
                        self.root.ids.settings_screen.is_first_setup = True
                    except Exception:
                        pass
                # if using the 'settings' name in sm children, set attribute if present
                try:
                    if hasattr(self.root, "ids") and 'sm' in self.root.ids:
                        for w in self.root.ids.sm.children:
                            if getattr(w, 'name', '') == 'settings':
                                try:
                                    w.is_first_setup = True
                                except Exception:
                                    pass
                except Exception:
                    pass
            else:
                if hasattr(self.root, "ids") and "sm" in self.root.ids:
                    self.root.ids.sm.current = "jerry"

            # Schedule Jerry updates
            if hasattr(self, "jerry_ai") and self.jerry_ai:
                Clock.schedule_interval(lambda dt: self.jerry_ai.companion.update_needs(), 60)
            # Update affirmation banner safely (only if sm exists)
            if hasattr(self.root, "ids") and "sm" in self.root.ids:
                try:
                    self.update_affirmation_banner(self.root.ids.sm.current)
                except Exception:
                    pass
            Clock.schedule_interval(lambda dt: self.update_affirmation_banner(), 10)

        except Exception as e:
            print(f"[HushApp] Error in on_start: {e}")

    def on_stop(self):
        try:
            if hasattr(self, "jerry_ai"):
                self.jerry_ai.end_session()
        except Exception as e:
            print(f"[HushApp] on_stop error: {e}")
        # Let the OS manage window closing and lifecycle

    def update_affirmation_banner(self, screen_name=None):
        # If screen_name not provided, try to determine from screen manager
        try:
            if not (hasattr(self.root, "ids") and "sm" in self.root.ids):
                return
            if screen_name is None:
                screen_name = self.root.ids.sm.current

            if screen_name in ("jerry", "checkin"):
                self.affirmation_text = random.choice(AFFIRMATIONS)
            else:
                self.affirmation_text = ""
        except Exception as e:
            print(f"[HushApp] update_affirmation_banner error: {e}")

    def show_exit_dialog(self):
        try:
            if not self.dialog:
                self.dialog = MDDialog(
                    title="Exit Hush?",
                    text="Are you sure you want to exit?",
                    buttons=[
                        MDFlatButton(
                            text="CANCEL",
                            theme_text_color="Custom",
                            text_color=self.theme_cls.primary_color,
                            on_release=self.dismiss_dialog,
                        ),
                        MDRaisedButton(
                            text="EXIT",
                            theme_text_color="Custom",
                            text_color=self.theme_cls.primary_color,
                            on_release=lambda x: self.stop(),
                        ),
                    ],
                )
            self.dialog.open()
        except Exception as e:
            print(f"[HushApp] show_exit_dialog error: {e}")

    def dismiss_dialog(self, obj):
        try:
            if self.dialog:
                self.dialog.dismiss()
        except Exception as e:
            print(f"[HushApp] dismiss_dialog error: {e}")

    def on_request_close(self, *args):
        # show dialog and prevent immediate close
        try:
            self.show_exit_dialog()
            return True
        except Exception:
            return True

# --- Main Entry Point ---
if __name__ == "__main__":
    if not os.path.exists(ASSETS_PATH):
        print("Assets folder not found!")
    HushApp().run()
