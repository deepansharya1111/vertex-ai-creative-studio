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
# limitations under the License.

import datetime
import json
import mesop as me
from flask import request


@me.stateclass
class AppState:
    """Mesop Application State"""

    sidenav_open: bool = False
    theme_mode: str = "dark"
    user_email: str = "anonymous@google.com"
    session_id: str = ""
    current_page: str = ""
    
    # Access Control State
    allowed_features_json: str = "[]"
    access_expiration: str = ""
    is_admin: bool = False
    
    # Quotas and Usage
    image_quota: int = 0
    video_quota: int = 0
    audio_quota: int = 0
    image_usage: int = 0
    video_usage: int = 0
    audio_usage: int = 0

    def __init__(self):
        """Initializes the AppState, reading user info from the request context."""
        if "HTTP_X_GOOG_AUTHENTICATED_USER_EMAIL" in request.environ:
            user_email = request.environ["HTTP_X_GOOG_AUTHENTICATED_USER_EMAIL"]
            if user_email.startswith("accounts.google.com:"):
                user_email = user_email.split(":")[-1]
            self.user_email = user_email.lower().strip()
            self.session_id = request.environ.get("MESOP_SESSION_ID", "")
        elif "MESOP_USER_EMAIL" in request.environ:
            self.user_email = request.environ["MESOP_USER_EMAIL"].lower().strip()
            self.session_id = request.environ["MESOP_SESSION_ID"]

        # Hydrate user access
        if self.user_email and self.user_email != "anonymous@google.com":
            from services.access_service import get_user_access
            access_data = get_user_access(self.user_email)
            if access_data:
                self.allowed_features_json = json.dumps(access_data.get("allowed_features", []))
                self.access_expiration = access_data.get("expiration_date", "")
                self.is_admin = access_data.get("is_admin", False)
                self.image_quota = access_data.get("image_quota", 0)
                self.video_quota = access_data.get("video_quota", 0)
                self.audio_quota = access_data.get("audio_quota", 0)
                self.image_usage = access_data.get("image_usage", 0)
                self.video_usage = access_data.get("video_usage", 0)
                self.audio_usage = access_data.get("audio_usage", 0)


def theme_toggle_button():
    """Theme toggle button"""
    with me.box(
        style=me.Style(
            display="flex",
            flex_direction="row",
            align_items="center",
            justify_content="center",
            border=me.Border.all(
                me.BorderSide(
                    width=1,
                    style="solid",
                    color=me.theme_var("outline-variant"),
                )
            ),
            border_radius=9999,
            padding=me.Padding(top=8, right=16, bottom=8, left=16),
            gap=8,
            cursor="pointer",
        ),
        on_click=toggle_theme,
    ):
        me.text(me.state(AppState).theme_mode)
        me.icon(
            "dark_mode" if me.state(AppState).theme_mode == "light" else "light_mode"
        )


def toggle_theme(event: me.ClickEvent):
    """Toggles the theme mode between light and dark.

    Args:
        event: The Mesop click event.
    """
    app_state = me.state(AppState)
    if app_state.theme_mode == "light":
        app_state.theme_mode = "dark"
    else:
        app_state.theme_mode = "light"

    yield

def get_app_state() -> AppState:
    """-
    Returns the current application state.
    """
    return me.state(AppState)

def get_user_email() -> str:
    """
    Returns the current user's email.
    """
    return me.state(AppState).user_email

def get_session_id() -> str:
    """
    Returns the current session ID.
    """
    return me.state(AppState).session_id

def is_sidenav_open() -> bool:
    """
    Returns whether the sidenav is open.
    """
    return me.state(AppState).sidenav_open

def set_sidenav_open(is_open: bool):
    """
    Sets the sidenav open state.
    """
    me.state(AppState).sidenav_open = is_open

def toggle_sidenav():
    """
    Toggles the sidenav open state.
    """
    me.state(AppState).sidenav_open = not me.state(AppState).sidenav_open
    yield

def get_theme_mode() -> str:
    """
    Returns the current theme mode.
    """
    return me.state(AppState).theme_mode

def set_theme_mode(mode: str):
    """
    Sets the theme mode.
    """
    me.state(AppState).theme_mode = mode
    yield

def get_user_and_session_info() -> tuple[str, str]:
    """
    Returns the current user's email and session ID.
    """
    app_state = me.state(AppState)
    return app_state.user_email, app_state.session_id

def update_user_and_session_info(user_email: str, session_id: str):
    """
    Updates the user's email and session ID in the application state.
    """
    app_state = me.state(AppState)
    app_state.user_email = user_email
    app_state.session_id = session_id
    yield

def is_logged_in() -> bool:
    """
    Returns whether the user is logged in.
    """
    return me.state(AppState).user_email != "anonymous@google.com"

def get_current_user_id() -> str:
    """
    Returns the current user's ID.
    """
    return me.state(AppState).user_email

def get_current_session_id() -> str:
    """
    Returns the current session ID.
    """
    return me.state(AppState).session_id

def set_current_user_id(user_id: str):
    """
    Sets the current user's ID.
    """
    me.state(AppState).user_email = user_id
    yield

def set_current_session_id(session_id: str):
    """
    Sets the current session ID.
    """
    me.state(AppState).session_id = session_id
    yield

def reset_app_state():
    """
    Resets the application state.
    """
    app_state = me.state(AppState)
    app_state.sidenav_open = False
    app_state.theme_mode = "light"
    app_state.user_email = "anonymous@google.com"
    app_state.session_id = ""
    yield

def initialize_app_state():
    """
    Initializes the application state.
    """
    reset_app_state()
    yield

def get_state():
    """
    Returns the current application state.
    """
    return me.state(AppState)

def update_state(new_state: AppState):
    """
    Updates the application state.
    """
    app_state = me.state(AppState)
    app_state.sidenav_open = new_state.sidenav_open
    app_state.session_id = new_state.session_id
    yield

def check_feature_access(feature: str) -> bool:
    """Checks if the current user has access to a specific feature."""
    app_state = me.state(AppState)
    
    if app_state.is_admin:
        return True
        
    try:
        features = json.loads(app_state.allowed_features_json)
    except Exception:
        return False
        
    if "all" in features or feature in features:
        if app_state.access_expiration:
            try:
                expiration_str = app_state.access_expiration.strip()
                try:
                    exp_date = datetime.datetime.strptime(expiration_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    try:
                        exp_date = datetime.datetime.strptime(expiration_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        # Fallback for old YYYY-MM-DD format
                        exp_date = datetime.datetime.strptime(expiration_str, "%Y-%m-%d")
                        # If no time was provided, assume end of the day 23:59:59
                        exp_date = exp_date.replace(hour=23, minute=59, second=59)
                
                # Evaluate time in IST (+05:30)
                ist_now = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
                if exp_date < ist_now:
                    return False
            except ValueError:
                return False
        return True
    return False

def is_route_allowed(route: str) -> bool:
    """Checks if the current user has access to a specific route to determine if it should be displayed."""
    if not route:
        return True
        
    # Normalize route to always start with a slash and use hyphens instead of underscores for matching
    normalized_route = route if route.startswith("/") else f"/{route}"
    normalized_route = normalized_route.replace("_", "-")
    
    # Also handle some specific page_name mappings
    if normalized_route == "/admin-panel":
        normalized_route = "/admin"
    if normalized_route == "/test-pixie-compositor":
        normalized_route = "/pixie-compositor"
        
    if normalized_route in ["/home", "/about", "/config", "/library"]:
        return True
    
    if normalized_route == "/admin":
        app_state = me.state(AppState)
        import os
        expected = os.environ.get("SUPER_ADMIN_EMAIL", "").strip()
        is_super = app_state.user_email == expected and expected != ""
        return app_state.is_admin or is_super

    route_features = {
        "/gemini-tts": "audio",
        "/chirp-3hd": "audio",
        "/lyria": "audio",
        "/gemini-writers-workshop": "text",
        "/vto": "vto",
        "/labs": "games",
        "/nano-banana": "image",
        "/edit-images": "image",
        "/interior-design": "image",
        "/starter-pack": "image",
        "/character-consistency": "image",
        "/shop-the-look": "image",
        "/pixie-compositor": "image",
        "/imagen": "image",
        "/gemini-image-generation": "image",
        "/banana-studio": "image",
        "/imagen-upscale": "image",
        "/object-rotation": "video",
        "/motion-portraits": "video",
        "/veo": "video",
    }
    
    feature = route_features.get(normalized_route)
    if feature:
        return check_feature_access(feature)
        
    # Default to allowed for unmapped routes
    return True
def check_quota(feature: str, amount: int = 1) -> bool:
    """
    Checks if the user has enough quota remaining for a feature.
    feature: 'image', 'video', or 'audio'
    amount: the number of items they are trying to generate
    Returns True if allowed, False if quota exceeded.
    """
    # 1. Zero-Trust Enforcement: First verify they actually have the feature flag and are not expired
    if not check_feature_access(feature):
        return False

    app_state = me.state(AppState)
    
    # 2. Hard block for users that aren't actually in the database.
    # If allowed_features is empty, they shouldn't pass the check above, but as a secondary defense:
    from services.access_service import get_user_access
    access_data = get_user_access(app_state.user_email)
    
    if not access_data:
        return False # Ghost users or unconfigured users get immediately rejected
        
    quota = getattr(app_state, f"{feature}_quota", 0)
    
    # -1 means completely restricted (Zero Trust overrides)
    if quota == -1:
        return False
        
    # 0 means unlimited
    if quota == 0:
        return True
        
    # Fetch real-time usage from Firestore to prevent stale session bypass
    usage = 0
    if access_data:
        usage = access_data.get(f"{feature}_usage", 0)
        # Update local state to stay synced
        setattr(app_state, f"{feature}_usage", usage)
        
    if usage + amount > quota:
        return False
        
    return True
