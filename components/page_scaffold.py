# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import mesop as me

from common.analytics import log_page_view
from components.side_nav import sidenav
from state.state import AppState
from components.styles import (
    MAIN_COLUMN_STYLE,
    PAGE_BACKGROUND_PADDING_STYLE,
    PAGE_BACKGROUND_STYLE,
    SIDENAV_MAX_WIDTH,
    SIDENAV_MIN_WIDTH,
)
from components.theme_manager.theme_manager import theme_manager

def on_theme_load(e: me.WebEvent):
    s = me.state(AppState)
    s.theme_mode = e.value["theme"]
    me.set_theme_mode(s.theme_mode)
    yield


@me.content_component
def page_scaffold(page_name: str):
    """page scaffold component"""

    app_state = me.state(AppState)
    app_state.current_page = page_name
    log_page_view(page_name=page_name, session_id=app_state.session_id)

    theme_manager(theme=app_state.theme_mode, on_theme_load=on_theme_load)

    sidenav("")

    with me.box(
        style=me.Style(
            display="flex",
            flex_direction="column",
            height="100%",
            margin=me.Margin(
                left=SIDENAV_MAX_WIDTH if app_state.sidenav_open else SIDENAV_MIN_WIDTH,
            ),
        ),
    ):
        with me.box(
            style=me.Style(
                background=me.theme_var("background"),
                height="100%",
                overflow_y="scroll",
                margin=me.Margin(bottom=20),
            )
        ):
            from state.state import is_route_allowed
            if is_route_allowed(me.state(AppState).current_page):
                me.slot()
            else:
                with me.box(
                    style=me.Style(
                        display="flex",
                        flex_direction="column",
                        align_items="center",
                        justify_content="center",
                        height="100%",
                        padding=me.Padding.all(40),
                        gap=16
                    )
                ):
                    me.icon("lock", style=me.Style(font_size="48px", color=me.theme_var("error")))
                    me.text("Access Denied", type="headline-4", style=me.Style(color=me.theme_var("on-background")))
                    me.text(
                        "You do not have permission to view this feature or your access has expired. Please contact an administrator.",
                        style=me.Style(color=me.theme_var("on-surface-variant"), text_align="center")
                    )


@me.content_component
def page_frame():
    """Page Frame"""
    with me.box(style=MAIN_COLUMN_STYLE):
        with me.box(style=PAGE_BACKGROUND_STYLE):
            with me.box(style=PAGE_BACKGROUND_PADDING_STYLE):
                me.slot()
