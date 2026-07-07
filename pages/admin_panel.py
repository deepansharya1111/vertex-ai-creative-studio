import json
import mesop as me
from state.state import AppState
from config.default import Default
from components.header import header
from components.page_scaffold import page_frame, page_scaffold
from services.access_service import get_user_access, set_user_access, list_all_users_access

config = Default()

@me.stateclass
class AdminState:
    is_authenticated: bool = False
    password_input: str = ""
    error_message: str = ""
    users_json: str = "[]"
    
    # Form State
    edit_email: str = ""
    edit_expiration: str = ""
    edit_is_admin: bool = False
    
    # Feature Toggles
    f_image: bool = False
    f_video: bool = False
    f_audio: bool = False
    f_text: bool = False
    f_vto: bool = False
    f_games: bool = False
    
    # Quotas
    q_image: str = "0"
    q_video: str = "0"
    q_audio: str = "0"

def on_password_blur(e: me.InputBlurEvent):
    me.state(AdminState).password_input = e.value

import os

def on_password_enter(e: me.InputEnterEvent):
    state = me.state(AdminState)
    state.password_input = e.value
    yield from login_admin(None)

def login_admin(e: me.ClickEvent | None):
    state = me.state(AdminState)
    from dotenv import load_dotenv
    load_dotenv(override=True)
    expected_password = os.environ.get("ADMIN_PANEL_PASSWORD", "").strip()
    
    # Strip the input password as well to be safe
    input_pass = state.password_input.strip()
    
    if input_pass == expected_password and expected_password != "":
        state.is_authenticated = True
        state.error_message = ""
        load_users()
    else:
        state.error_message = "Invalid password or admin password not configured."
        state.password_input = ""
    yield

def load_users():
    state = me.state(AdminState)
    users = list_all_users_access()
    state.users_json = json.dumps(users)

def on_email_blur(e: me.InputBlurEvent):
    me.state(AdminState).edit_email = e.value

def on_expiration_blur(e: me.InputBlurEvent):
    me.state(AdminState).edit_expiration = e.value

def on_is_admin_change(e: me.CheckboxChangeEvent):
    me.state(AdminState).edit_is_admin = e.checked

def toggle_f_image(e: me.CheckboxChangeEvent):
    me.state(AdminState).f_image = e.checked
def toggle_f_video(e: me.CheckboxChangeEvent):
    me.state(AdminState).f_video = e.checked
def toggle_f_audio(e: me.CheckboxChangeEvent):
    me.state(AdminState).f_audio = e.checked
def toggle_f_text(e: me.CheckboxChangeEvent):
    me.state(AdminState).f_text = e.checked
def toggle_f_vto(e: me.CheckboxChangeEvent):
    me.state(AdminState).f_vto = e.checked
def toggle_f_games(e: me.CheckboxChangeEvent):
    me.state(AdminState).f_games = e.checked

def save_user(e: me.ClickEvent):
    state = me.state(AdminState)
    if not state.edit_email:
        state.error_message = "Email is required."
        yield
        return
        
    features = []
    if state.f_image: features.append("image")
    if state.f_video: features.append("video")
    if state.f_audio: features.append("audio")
    if state.f_text: features.append("text")
    if state.f_vto: features.append("vto")
    if state.f_games: features.append("games")
    
    def parse_quota(q: str) -> int:
        try:
            return int(q)
        except ValueError:
            return 0

    try:
        from services.access_service import set_user_access
        set_user_access(
            email=state.edit_email,
            allowed_features=features,
            expiration_date=state.edit_expiration.replace("T", " "),
            is_admin=state.edit_is_admin,
            image_quota=parse_quota(state.q_image),
            video_quota=parse_quota(state.q_video),
            audio_quota=parse_quota(state.q_audio),
        )
        state.error_message = "User saved successfully."
        load_users()
    except Exception as ex:
        state.error_message = f"Error saving user: {ex}"
    yield

def select_user(e: me.ClickEvent):
    state = me.state(AdminState)
    users = json.loads(state.users_json)
    
    # Simple search to populate form
    for user in users:
        if user.get("email") == e.key:
            state.edit_email = user.get("email", "")
            exp = user.get("expiration_date", "")
            state.edit_expiration = exp.replace(" ", "T") if " " in exp else exp
            state.edit_is_admin = user.get("is_admin", False)
            
            features = user.get("allowed_features", [])
            state.f_image = "image" in features
            state.f_video = "video" in features
            state.f_audio = "audio" in features
            state.f_text = "text" in features
            state.f_vto = "vto" in features
            state.f_games = "games" in features
            
            state.q_image = str(user.get("image_quota", 0))
            state.q_video = str(user.get("video_quota", 0))
            state.q_audio = str(user.get("audio_quota", 0))
            break
    yield


def delete_user(e: me.ClickEvent):
    from services.access_service import delete_user_access
    state = me.state(AdminState)
    email_to_delete = e.key
    try:
        delete_user_access(email_to_delete)
        
        # Remove from local list
        users = json.loads(state.users_json)
        users = [u for u in users if u.get("email") != email_to_delete]
        state.users_json = json.dumps(users)
        
        # If deleted user is currently being edited, clear form
        if state.edit_email == email_to_delete:
            state.edit_email = ""
            state.edit_expiration = ""
            state.edit_is_admin = False
            state.f_image = False
            state.f_video = False
            state.f_audio = False
            state.f_text = False
            state.f_vto = False
            state.f_games = False
            
        state.error_message = f"User {email_to_delete} deleted successfully."
    except Exception as ex:
        state.error_message = f"Failed to delete user: {ex}"
    yield

def clear_user(e: me.ClickEvent):
    state = me.state(AdminState)
    state.edit_email = ""
    state.edit_expiration = ""
    state.edit_is_admin = False
    state.f_image = False
    state.f_video = False
    state.f_audio = False
    state.f_text = False
    state.f_vto = False
    state.f_games = False
    state.q_image = "0"
    state.q_video = "0"
    state.q_audio = "0"
    state.error_message = ""
    yield



def render_feature_chip(feature_name: str):
    with me.box(
        style=me.Style(
            background=me.theme_var("secondary-container"),
            border_radius=16,
            padding=me.Padding.symmetric(horizontal=12, vertical=4),
            margin=me.Margin(right=8, bottom=4),
            display="inline-block" # inline-flex isn't standard in mesop properties sometimes, we just use inline-block
        )
    ):
        me.text(feature_name, style=me.Style(color=me.theme_var("on-secondary-container"), font_size="0.85rem"))


def on_q_image_blur(e: me.InputBlurEvent):
    me.state(AdminState).q_image = e.value
def on_q_video_blur(e: me.InputBlurEvent):
    me.state(AdminState).q_video = e.value
def on_q_audio_blur(e: me.InputBlurEvent):
    me.state(AdminState).q_audio = e.value
def admin_panel_content():
    state = me.state(AdminState)
    app_state = me.state(AppState)
    
    with page_frame():
        header("Admin Panel", "admin_panel_settings")
        
        expected_super_admins = [e.strip() for e in os.environ.get("SUPER_ADMIN_EMAILS", os.environ.get("SUPER_ADMIN_EMAIL", "")).split(",") if e.strip()]
        is_super_admin_env = app_state.user_email in expected_super_admins
        
        # Dual Auth: Must be in env list OR already be an explicit admin in the database
        if not app_state.is_admin and not is_super_admin_env:
            with me.box(style=me.Style(padding=me.Padding.all(32))):
                me.text("Access Denied", type="headline-4", style=me.Style(color=me.theme_var("error")))
                me.text("You do not have permission to view the Admin Panel.")
            return
        
        with me.box(style=me.Style(padding=me.Padding.all(24))):
            if not state.is_authenticated:
                # Login View
                me.text("Admin Authentication Required", type="headline-5")
                me.input(
                    label="Admin Password",
                    type="password",
                    value=state.password_input,
                    on_blur=on_password_blur,
                    on_enter=on_password_enter,
                    style=me.Style(width=300)
                )
                with me.box(style=me.Style(margin=me.Margin(top=16))):
                    me.button("Login", on_click=login_admin, type="raised")
                
                if state.error_message:
                    me.text(state.error_message, style=me.Style(color=me.theme_var("error"), margin=me.Margin(top=16)))
            else:
                # Dashboard View
                me.text("User Access Management", type="headline-5")
                
                if state.error_message:
                    me.text(state.error_message, style=me.Style(color=me.theme_var("primary"), margin=me.Margin(bottom=16)))
                
                with me.box(style=me.Style(display="flex", flex_direction="row", gap=32, flex_wrap="wrap")):
                    # Left Column: User Form
                    with me.box(style=me.Style(
                        flex_basis="350px", 
                        flex_grow=0, 
                        flex_shrink=0,
                        background=me.theme_var("surface-container-low"),
                        padding=me.Padding.all(24),
                        border_radius=12,
                        border=me.Border.all(me.BorderSide(width=1, color=me.theme_var("outline-variant"), style="solid"))
                    )):
                        me.text("User Details", type="subtitle-1", style=me.Style(margin=me.Margin(bottom=16), font_weight="bold"))
                        
                        me.input(label="User Email", value=state.edit_email, on_blur=on_email_blur, style=me.Style(width="100%", margin=me.Margin(bottom=8)))
                        me.input(label="Expiration", type="datetime-local", value=state.edit_expiration, on_blur=on_expiration_blur, style=me.Style(width="100%", margin=me.Margin(bottom=16)))
                        
                        me.checkbox(label="Is Super Admin (All Access)", checked=state.edit_is_admin, on_change=on_is_admin_change)
                        
                        me.text("Allowed Features:", style=me.Style(margin=me.Margin(top=24, bottom=12), font_weight="bold"))
                        with me.box(style=me.Style(display="flex", flex_wrap="wrap", gap=8)):
                            me.checkbox(label="Image", checked=state.f_image, on_change=toggle_f_image)
                            me.checkbox(label="Video", checked=state.f_video, on_change=toggle_f_video)
                            me.checkbox(label="Audio/TTS", checked=state.f_audio, on_change=toggle_f_audio)
                            me.checkbox(label="Text", checked=state.f_text, on_change=toggle_f_text)
                            me.checkbox(label="Virtual Try-On", checked=state.f_vto, on_change=toggle_f_vto)
                            me.checkbox(label="Labs", checked=state.f_games, on_change=toggle_f_games)
                        
                        me.text("Quotas (0 = Unlimited):", style=me.Style(margin=me.Margin(top=24, bottom=12), font_weight="bold"))
                        with me.box(style=me.Style(display="flex", gap=16)):
                            me.input(label="Image", value=state.q_image, on_blur=on_q_image_blur, style=me.Style(width="100px"))
                            me.input(label="Video", value=state.q_video, on_blur=on_q_video_blur, style=me.Style(width="100px"))
                            me.input(label="Audio", value=state.q_audio, on_blur=on_q_audio_blur, style=me.Style(width="100px"))

                        with me.box(style=me.Style(margin=me.Margin(top=32), display="flex", gap=12)):
                            me.button("Save User", on_click=save_user, type="flat", color="primary")
                            me.button("Clear Form", on_click=clear_user, type="stroked")
                    
                    # Right Column: User List
                    with me.box(style=me.Style(flex_grow=1)):
                        me.text("Existing Users", type="subtitle-1", style=me.Style(margin=me.Margin(bottom=16)))
                        
                        users = json.loads(state.users_json)
                        if not users:
                            me.text("No users found.")
                        else:
                            for user in users:
                                with me.box(
                                    style=me.Style(
                                        background=me.theme_var("surface-container-low"),
                                        border=me.Border.all(me.BorderSide(width=1, color=me.theme_var("outline-variant"), style="solid")),
                                        padding=me.Padding.all(16),
                                        margin=me.Margin(bottom=16),
                                        border_radius=12,
                                        display="flex",
                                        flex_direction="row",
                                        justify_content="space-between",
                                        align_items="flex-start",
                                    )
                                ):
                                    with me.box(style=me.Style(display="flex", flex_direction="row", gap=16, align_items="flex-start")):
                                        # Avatar/Icon
                                        with me.box(style=me.Style(
                                            background=me.theme_var("primary-container"),
                                            border_radius=24,
                                            width=48,
                                            height=48,
                                            display="flex",
                                            justify_content="center",
                                            align_items="center"
                                        )):
                                            me.icon("person", style=me.Style(color=me.theme_var("on-primary-container")))
                                        
                                        # Details
                                        with me.box(style=me.Style(display="flex", flex_direction="column")):
                                            me.text(user.get("email", ""), style=me.Style(font_weight="bold", font_size="1.1rem", margin=me.Margin(bottom=8)))
                                            
                                            # Features
                                            with me.box(style=me.Style(display="flex", flex_wrap="wrap", margin=me.Margin(bottom=8))):
                                                features_list = user.get('allowed_features', [])
                                                if not features_list:
                                                    me.text("No features", style=me.Style(color=me.theme_var("on-surface-variant"), font_style="italic", font_size="0.85rem"))
                                                else:
                                                    for feat in features_list:
                                                        render_feature_chip(feat.capitalize())
                                            
                                            with me.box(style=me.Style(display="flex", flex_direction="row", gap=4, align_items="center")):
                                                me.icon("schedule", style=me.Style(font_size="1rem", color=me.theme_var("on-surface-variant")))
                                                me.text(f"Expires: {user.get('expiration_date', 'Never')}", style=me.Style(color=me.theme_var("on-surface-variant"), font_size="0.9rem"))
                                                
                                                me.box(style=me.Style(width=16)) # Spacer
                                                me.icon("bar_chart", style=me.Style(font_size="1rem", color=me.theme_var("on-surface-variant")))
                                                iq = user.get("image_quota", 0)
                                                vq = user.get("video_quota", 0)
                                                aq = user.get("audio_quota", 0)
                                                iu = user.get("image_usage", 0)
                                                vu = user.get("video_usage", 0)
                                                au = user.get("audio_usage", 0)
                                                quota_text = f"Usage: Img {iu}/{'∞' if iq == 0 else iq} | Vid {vu}/{'∞' if vq == 0 else vq} | Aud {au}/{'∞' if aq == 0 else aq}"
                                                me.text(quota_text, style=me.Style(color=me.theme_var("on-surface-variant"), font_size="0.9rem"))
                                                
                                    
                                    with me.box(style=me.Style(padding=me.Padding(top=8), display="flex", gap=8)):
                                        me.button("Edit", key=user.get("email", ""), on_click=select_user, type="stroked")
                                        me.button("Delete", key=user.get("email", ""), on_click=delete_user, type="stroked", color="warn")


@me.page(
    path="/admin",
    title="Admin Panel - GenMedia Creative Studio",
    security_policy=me.SecurityPolicy(
        allowed_script_srcs=[
            "https://cdn.jsdelivr.net",
        ]
    )
)
def page():
    with page_scaffold(page_name="admin_panel"):
        admin_panel_content()
