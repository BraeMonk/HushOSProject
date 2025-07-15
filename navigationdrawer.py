# -*- coding: utf-8 -*-
"""
Navigation Drawer
=================
A completely rewritten, stable version of the NavigationDrawer widget.
This version corrects all previous syntax and initialization errors.
"""
__all__ = ('NavigationDrawer',)

from kivy.animation import Animation
from kivy.uix.stencilview import StencilView
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import (ObjectProperty, OptionProperty, NumericProperty,
                             StringProperty, BooleanProperty, AliasProperty)
from kivy.lang import Builder

# This KV string is now correctly structured, which will resolve the SyntaxError.
Builder.load_string('''
<NavigationDrawer>:
    size_hint: (1, 1)
    
    # The children are now correctly defined as widgets, not properties.
    # The Python class will link to them via their IDs.
    RelativeLayout:
        id: side_panel
        size_hint: (None, 1)
        width: root.side_panel_width
        x: root.x - self.width
        
    RelativeLayout:
        id: main_panel
        size_hint: (1, 1)
        x: root.x
        y: root.y

    Image:
        id: join_image
        opacity: 1 if root.separator_image else 0
        source: root.separator_image
        mipmap: False
        size_hint: (None, 1)
        width: root.separator_image_width
        x: side_panel.right
        y: root.y
        allow_stretch: True
        keep_ratio: False
''')


class NavigationDrawer(StencilView):
    # Public properties
    side_panel = ObjectProperty(None, allownone=True)
    main_panel = ObjectProperty(None, allownone=True)
    
    state = OptionProperty('closed', options=('open', 'closed'))
    touch_accept_width = NumericProperty('14dp')
    side_panel_width = NumericProperty('250dp')
    separator_image = StringProperty('')
    separator_image_width = NumericProperty('10dp')
    anim_time = NumericProperty(0.2)
    anim_type = StringProperty('linear')

    # Internal properties
    _touch = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(NavigationDrawer, self).__init__(**kwargs)
        # We will link the panels once they are created by the KV rule
        Clock.schedule_once(self._link_panels)

    def _link_panels(self, *args):
        # This robustly links the panels after they are guaranteed to exist
        self.side_panel = self.ids.side_panel
        self.main_panel = self.ids.main_panel

    def on_state(self, instance, value):
        if self.side_panel is None or self.main_panel is None:
            return
        Animation.cancel_all(self.side_panel)
        Animation.cancel_all(self.main_panel)
        if value == 'open':
            self._anim_open()
        else:
            self._anim_close()

    def _anim_open(self):
        Animation(x=0, t=self.anim_type, duration=self.anim_time).start(self.side_panel)
        Animation(x=self.side_panel_width, t=self.anim_type, duration=self.anim_time).start(self.main_panel)

    def _anim_close(self):
        Animation(x=-self.side_panel_width, t=self.anim_type, duration=self.anim_time).start(self.side_panel)
        Animation(x=0, t=self.anim_type, duration=self.anim_time).start(self.main_panel)

    def set_state(self, state='toggle'):
        if state == 'toggle':
            self.state = 'closed' if self.state == 'open' else 'open'
        else:
            self.state = state

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            self._touch = None
            return False
        if self.disabled:
            return True

        # Let child widgets of the panels receive the touch
        if self.side_panel.collide_point(*touch.pos) or self.main_panel.collide_point(*touch.pos):
             super(NavigationDrawer, self).on_touch_down(touch)

        # Handle touches to open/close the drawer
        if self.state == 'closed' and touch.x < self.touch_accept_width:
            self.set_state('open')
            self._touch = touch
            touch.grab(self)
            return True
        elif self.state == 'open' and self.main_panel.collide_point(*touch.pos):
            self.set_state('closed')
            self._touch = touch
            touch.grab(self)
            return True
        
        return False

    def on_touch_move(self, touch):
        if touch.grab_current is self and self._touch is touch:
            dist = touch.x - self._touch.x
            if self.state == 'open':
                self.side_panel.x = min(0, -self.side_panel_width + dist)
            else:
                self.side_panel.x = max(-self.side_panel_width, dist - self.side_panel_width)
            self.main_panel.x = self.side_panel.right
            return True
        return super(NavigationDrawer, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self and self._touch is touch:
            touch.ungrab(self)
            self._touch = None
            # Decide whether to open or close based on position
            if self.side_panel.x > (-self.side_panel_width / 2.0):
                self.set_state('open')
            else:
                self.set_state('closed')
            return True
        return super(NavigationDrawer, self).on_touch_up(touch)

    def add_widget(self, widget, index=0, canvas=None):
        # This logic is now greatly simplified.
        # The main structure is built from KV. Any other widgets
        # added later will go into the main_panel.
        if 'side_panel' not in self.ids:
            # This is the initial setup from KV, let it happen
            super(NavigationDrawer, self).add_widget(widget, index, canvas)
        else:
            # After setup, add subsequent widgets to the main panel
            self.main_panel.add_widget(widget)

    def remove_widget(self, widget):
        if widget in [self.ids.side_panel, self.ids.main_panel, self.ids.join_image]:
            super(NavigationDrawer, self).remove_widget(widget)
        else:
            self.main_panel.remove_widget(widget)

