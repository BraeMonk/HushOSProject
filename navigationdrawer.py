# -*- coding: utf-8 -*-
"""
Navigation Drawer
=================
A stable, corrected version of the NavigationDrawer widget logic.
This file avoids the previous timing and initialization bugs.
"""
__all__ = ('NavigationDrawer',)

from kivy.properties import ObjectProperty, AliasProperty, OptionProperty, \
    NumericProperty, StringProperty, BooleanProperty, ListProperty
from kivy.uix.stencilview import StencilView
from kivy.uix.relativelayout import RelativeLayout
from kivy.animation import Animation

class NavigationDrawer(StencilView):
    # Internal properties used for binding
    _main_panel = ObjectProperty()
    _side_panel = ObjectProperty()
    _join_image = ObjectProperty()
    _anim_alpha = NumericProperty(0)
    _touch_started_in_panel = BooleanProperty(False)

    # Public properties
    side_panel = ObjectProperty(None, allownone=True)
    main_panel = ObjectProperty(None, allownone=True)
    state = OptionProperty('closed', options=('open', 'closed'))
    touch_accept_width = NumericProperty('14dp')
    side_panel_width = NumericProperty('250dp')
    separator_image = StringProperty('')
    separator_image_width = NumericProperty('10dp')
    anim_time = NumericProperty(0.3)
    anim_type = StringProperty('linear')

    def __init__(self, **kwargs):
        super(NavigationDrawer, self).__init__(**kwargs)
        self.bind(state=self._state_change)

    def _state_change(self, *args):
        Animation.cancel_all(self._main_panel)
        Animation.cancel_all(self._side_panel)
        if self.state == 'open':
            anim = Animation(x=self.side_panel_width, t=self.anim_type, duration=self.anim_time)
            anim.start(self._main_panel)
            anim = Animation(x=0, t=self.anim_type, duration=self.anim_time)
            anim.start(self._side_panel)
        else:
            anim = Animation(x=0, t=self.anim_type, duration=self.anim_time)
            anim.start(self._main_panel)
            anim = Animation(x=-self.side_panel_width, t=self.anim_type, duration=self.anim_time)
            anim.start(self._side_panel)

    def set_state(self, state='toggle'):
        if state == 'toggle':
            self.state = 'closed' if self.state == 'open' else 'open'
        else:
            self.state = state

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        if self.disabled:
            return True
        
        # Handle touches within the touch_accept_width to open the drawer
        if self.state == 'closed' and touch.x < self.touch_accept_width:
            self.set_state('open')
            return True
            
        # Handle touches on the main panel to close the drawer
        if self.state == 'open' and self._main_panel.collide_point(*touch.pos):
            self.set_state('closed')
            return True

        # Let the children of the panels handle the touch
        if self._side_panel.collide_point(*touch.pos) or self._main_panel.collide_point(*touch.pos):
            return super(NavigationDrawer, self).on_touch_down(touch)
        
        return False

    def add_widget(self, widget, index=0, canvas=None):
        # This method is called by Kivy when parsing the .kv file.
        # We need to correctly assign the main and side panels from the .kv rule.
        if not self._main_panel and not self._side_panel:
            # The first widget added becomes the side panel
            self._side_panel = widget
            widget.x = -self.side_panel_width
            widget.pos_hint = ({'x': 0, 'y': 0})
            widget.size_hint = (None, 1.0)
            widget.width = self.side_panel_width
            super(NavigationDrawer, self).add_widget(widget, index, canvas)
        elif not self._main_panel:
            # The second widget added becomes the main panel
            self._main_panel = widget
            widget.pos_hint = ({'x': 0, 'y': 0})
            widget.size_hint = (1.0, 1.0)
            super(NavigationDrawer, self).add_widget(widget, index, canvas)
        else:
            # Any subsequent widgets are added to the main panel by default
            self._main_panel.add_widget(widget)

    def remove_widget(self, widget):
        if widget in [self._main_panel, self._side_panel]:
            super(NavigationDrawer, self).remove_widget(widget)
        else:
            self._main_panel.remove_widget(widget)
            self._side_panel.remove_widget(widget)

