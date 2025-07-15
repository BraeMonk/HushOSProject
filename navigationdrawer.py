# -*- coding: utf-8 -*-
"""
Navigation Drawer
=================
This file now only contains the Python logic. The visual layout is handled
by the corresponding navigationdrawer.kv file, which Kivy loads automatically.
This prevents the indentation errors that were causing the crash.
"""
__all__ = ('NavigationDrawer', )

from kivy.properties import ObjectProperty, AliasProperty, OptionProperty, \
    NumericProperty, StringProperty, BooleanProperty, ListProperty
from kivy.uix.stencilview import StencilView
from kivy.uix.relativelayout import RelativeLayout
from kivy.animation import Animation
# Builder is no longer needed here, as the kv file is loaded automatically
# from kivy.lang import Builder


class NavigationDrawer(StencilView):

    _main_panel = ObjectProperty()
    _side_panel = ObjectProperty()
    _join_image = ObjectProperty()
    _anim_alpha = NumericProperty(0)
    _touch_started_in_panel = BooleanProperty(False)

    side_panel = ObjectProperty(None, allownone=True)
    main_panel = ObjectProperty(None, allownone=True)
    join_image = ObjectProperty(None, allownone=True)

    state = OptionProperty('closed', options=('open', 'closed'))
    touch_accept_width = NumericProperty('14dp')
    side_panel_width = NumericProperty('250dp')
    side_panel_init_offset = NumericProperty(1)
    side_panel_positioning = OptionProperty('left', options=('left', 'right'))
    separator_image = StringProperty('')
    separator_image_width = NumericProperty('10dp')
    separator_color = ListProperty([0, 0, 0, 0])
    fade_max_opacity = NumericProperty(1)
    anim_time = NumericProperty(0.3)
    anim_type = StringProperty('linear')

    def __init__(self, **kwargs):
        super(NavigationDrawer, self).__init__(**kwargs)
        self.bind(state=self._state_change,
                  side_panel_width=self._set_side_panel_width,
                  _anim_alpha=self._set_alpha)

    def _get_main_panel_final_x(self):
        if self.side_panel_positioning == 'left':
            return self.x + self.side_panel_width
        else:
            return self.x - self.side_panel_width

    def _get_side_panel_final_x(self):
        if self.side_panel_positioning == 'left':
            return self.x
        else:
            return self.right - self.side_panel_width

    def _set_side_panel_width(self, *args):
        if self.state == 'closed':
            if self.side_panel_positioning == 'left':
                self.side_panel.x = self.x - \
                    (1 - self.side_panel_init_offset) * self.side_panel_width
            else:
                self.side_panel.x = self.right - \
                    self.side_panel_init_offset * self.side_panel_width
        else:
            self.side_panel.x = self._get_side_panel_final_x()


    def _set_alpha(self, *args):
        self.side_panel.opacity = self._anim_alpha

    def _state_change(self, *args):
        Animation.cancel_all(self)
        if self.state == 'open':
            self._anim_alpha = self.fade_max_opacity
            anim = Animation(
                x=self._get_main_panel_final_x(),
                _anim_alpha=self.fade_max_opacity,
                side_panel_x=self._get_side_panel_final_x(),
                t=self.anim_type,
                duration=self.anim_time)
            anim.start(self)
        else:
            self._anim_alpha = 0
            anim = Animation(
                x=self.x,
                _anim_alpha=0,
                side_panel_x=self._get_side_panel_final_x(),
                t=self.anim_type,
                duration=self.anim_time)
            anim.start(self)

    def on_side_panel(self, *args):
        if self.side_panel:
            self.remove_widget(self.side_panel)
        if self.ids.side_panel:
            self.add_widget(self.ids.side_panel)

    def on_main_panel(self, *args):
        if self.main_panel:
            self.remove_widget(self.main_panel)
        if self.ids.main_panel:
            self.add_widget(self.ids.main_panel)

    def on_join_image(self, *args):
        if self.join_image:
            self.remove_widget(self.join_image)
        if self.ids.join_image:
            self.add_widget(self.ids.join_image)

    def set_state(self, state='toggle'):
        if state == 'toggle':
            if self.state == 'open':
                self.state = 'closed'
            else:
                self.state = 'open'
        else:
            self.state = state

    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            self._touch_started_in_panel = False
            return False
        if self.disabled:
            return True
        if self.state == 'open':
            if self.main_panel.collide_point(touch.x, touch.y):
                self.set_state('closed')
                self._touch_started_in_panel = True
                return True
        else:
            if self.side_panel_positioning == 'left':
                if touch.x < self.touch_accept_width:
                    self.set_state('open')
                    self._touch_started_in_panel = True
                    return True
            else:
                if touch.x > self.width - self.touch_accept_width:
                    self.set_state('open')
                    self._touch_started_in_panel = True
                    return True
        self._touch_started_in_panel = False
        return super(NavigationDrawer, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._touch_started_in_panel:
            return True
        return super(NavigationDrawer, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._touch_started_in_panel:
            self._touch_started_in_panel = False
            return True
        return super(NavigationDrawer, self).on_touch_up(touch)

    def add_widget(self, widget, index=0, canvas=None):
        if self.main_panel is None:
            if 'main_panel' in self.ids:
                self.main_panel = self.ids.main_panel
            else:
                self.main_panel = RelativeLayout()
        if self.side_panel is None:
            if 'side_panel' in self.ids:
                self.side_panel = self.ids.side_panel
            else:
                self.side_panel = RelativeLayout()

        if widget not in [self.main_panel, self.side_panel, self.join_image]:
            self.main_panel.add_widget(widget)
        else:
            super(NavigationDrawer, self).add_widget(widget, index, canvas)

    def remove_widget(self, widget):
        if widget not in [self.main_panel, self.side_panel, self.join_image]:
            if self.main_panel:
                self.main_panel.remove_widget(widget)
            if self.side_panel:
                self.side_panel.remove_widget(widget)
        else:
            super(NavigationDrawer, self).remove_widget(widget)

    def _get_separator_pos(self):
        if self.side_panel_positioning == 'left':
            return (self.side_panel.x + self.side_panel_width -
                    self.separator_image_width, self.y)
        else:
            return (self.side_panel.x, self.y)

    separator_pos = AliasProperty(_get_separator_pos, None,
                                  bind=('_side_panel', 'x', 'y',
                                        'side_panel_width',
                                        'separator_image_width'))
