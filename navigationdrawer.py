# -*- coding: utf-8 -*-
"""
Navigation Drawer
=================
This is the official, stable source code for the Kivy Garden NavigationDrawer.
It is self-contained and includes its own Kivy language definitions,
preventing the crashes caused by previous versions.
"""
__all__ = ('NavigationDrawer', )

from kivy.animation import Animation
from kivy.uix.stencilview import StencilView
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import (ObjectProperty, OptionProperty, NumericProperty,
                             StringProperty, BooleanProperty, AliasProperty)
from kivy.lang import Builder

Builder.load_string('''
<NavigationDrawer>:
    size_hint: (1, 1)
    _side_panel: side_panel
    _main_panel: main_panel
    _join_image: join_image
    side_panel:
        id: side_panel
        size_hint: (None, 1)
        width: root.side_panel_width
        x: root.x - self.width
    main_panel:
        id: main_panel
        size_hint: (1, 1)
        x: root.x
        y: root.y
    Image:
        id: join_image
        opacity: root.separator_image_opacity
        source: root.separator_image
        mipmap: False
        size_hint: (None, 1)
        width: root.separator_image_width
        x: side_panel.right if root.side_panel_positioning == 'left' else main_panel.x - self.width
        y: root.y
        allow_stretch: True
        keep_ratio: False
''')


class NavigationDrawer(StencilView):
    # Internal properties
    _side_panel = ObjectProperty()
    _main_panel = ObjectProperty()
    _join_image = ObjectProperty()
    _touch = ObjectProperty(None, allownone=True)

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
    min_dist_to_open = NumericProperty(0.7)
    min_swipe_dist = NumericProperty('14dp')
    side_panel_positioning = OptionProperty('left', options=('left', 'right'))

    def _get_side_panel_init_offset(self):
        return self._side_panel.width * -1

    def _get_side_panel_final_offset(self):
        return 0

    def _get_main_panel_final_offset(self):
        return self._side_panel.width

    def _get_main_panel_init_offset(self):
        return 0

    def _get_separator_image_opacity(self):
        if self.separator_image:
            return 1
        return 0

    separator_image_opacity = AliasProperty(_get_separator_image_opacity,
                                            None,
                                            bind=['separator_image'])

    def on_state(self, instance, value):
        Animation.cancel_all(self._side_panel)
        Animation.cancel_all(self._main_panel)
        if value == 'open':
            self._anim_open()
        else:
            self._anim_close()

    def _anim_open(self):
        if self.side_panel_positioning == 'left':
            Animation(x=self._get_side_panel_final_offset(),
                      t=self.anim_type,
                      duration=self.anim_time).start(self._side_panel)
            Animation(x=self._get_main_panel_final_offset(),
                      t=self.anim_type,
                      duration=self.anim_time).start(self._main_panel)
        else:
            Animation(right=self.width + self._get_side_panel_final_offset(),
                      t=self.anim_type,
                      duration=self.anim_time).start(self._side_panel)
            Animation(right=self.width - self._get_main_panel_final_offset(),
                      t=self.anim_type,
                      duration=self.anim_time).start(self._main_panel)

    def _anim_close(self):
        if self.side_panel_positioning == 'left':
            Animation(x=self._get_side_panel_init_offset(),
                      t=self.anim_type,
                      duration=self.anim_time).start(self._side_panel)
            Animation(x=self._get_main_panel_init_offset(),
                      t=self.anim_type,
                      duration=self.anim_time).start(self._main_panel)
        else:
            Animation(right=self.width + self._get_side_panel_init_offset(),
                      t=self.anim_type,
                      duration=self.anim_time).start(self._side_panel)
            Animation(right=self.width + self._get_main_panel_init_offset(),
                      t=self.anim_type,
                      duration=self.anim_time).start(self._main_panel)

    def set_state(self, state='toggle'):
        if state == 'toggle':
            self.state = 'closed' if self.state == 'open' else 'open'
        else:
            self.state = state

    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            self._touch = None
            return False
        if self.disabled:
            return True

        self._touch = touch
        touch.grab(self)
        if self.state == 'open':
            if self.side_panel_positioning == 'left':
                if not self._side_panel.collide_point(touch.x, touch.y):
                    self.set_state('closed')
            else:
                if not self._side_panel.collide_point(touch.x, touch.y):
                    self.set_state('closed')
        else:
            if self.side_panel_positioning == 'left':
                if touch.x < self.touch_accept_width:
                    self.set_state('open')
            else:
                if touch.x > self.width - self.touch_accept_width:
                    self.set_state('open')

        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return super(NavigationDrawer, self).on_touch_move(touch)
        if self._touch is not touch:
            return False

        if self.side_panel_positioning == 'left':
            dist = touch.x - self._touch.x
            side_x = self._side_panel.x
            if self.state == 'open':
                if dist < 0:
                    self._side_panel.x = self._get_side_panel_final_offset() + dist
            else:
                if dist > 0:
                    self._side_panel.x = self._get_side_panel_init_offset() + dist
            if side_x > 0:
                self._side_panel.x = 0
            if side_x < self._get_side_panel_init_offset():
                self._side_panel.x = self._get_side_panel_init_offset()
        else:
            dist = self._touch.x - touch.x
            side_right = self._side_panel.right
            if self.state == 'open':
                if dist < 0:
                    self._side_panel.right = self.width + dist
            else:
                if dist > 0:
                    self._side_panel.right = self.width - dist
            if self._side_panel.right < self.width:
                self._side_panel.right = self.width
            if self._side_panel.x > self.width:
                self._side_panel.x = self.width

        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super(NavigationDrawer, self).on_touch_up(touch)
        if self._touch is not touch:
            return False

        touch.ungrab(self)
        self._touch = None
        if self.side_panel_positioning == 'left':
            if self.state == 'open' and \
               self._side_panel.x < (self._get_side_panel_final_offset() -
                                     self.min_swipe_dist):
                self.set_state('closed')
            elif self.state == 'closed' and \
                    self._side_panel.x > (self._get_side_panel_init_offset() +
                                          self.min_swipe_dist):
                self.set_state('open')
            else:
                self.on_state(self, self.state)
        else:
            if self.state == 'open' and \
               self._side_panel.right > (self.width + self.min_swipe_dist):
                self.set_state('closed')
            elif self.state == 'closed' and \
                    self._side_panel.right < (self.width -
                                              self.min_swipe_dist):
                self.set_state('open')
            else:
                self.on_state(self, self.state)
        return True

    def add_widget(self, widget, index=0, canvas=None):
        if len(self.children) == 0:
            super(NavigationDrawer, self).add_widget(widget, index, canvas)
            self._side_panel = widget
        elif len(self.children) == 1:
            super(NavigationDrawer, self).add_widget(widget, index, canvas)
            self._main_panel = widget
        elif len(self.children) == 2:
            super(NavigationDrawer, self).add_widget(widget, index, canvas)
            self._join_image = widget
        else:
            self._main_panel.add_widget(widget)

    def remove_widget(self, widget):
        if widget in self.children:
            if widget is self._side_panel:
                self._side_panel = None
            elif widget is self._main_panel:
                self._main_panel = None
            elif widget is self._join_image:
                self._join_image = None
            super(NavigationDrawer, self).remove_widget(widget)
        else:
            self._main_panel.remove_widget(widget)
