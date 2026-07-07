# Admin Panel Implementation Plan

## 1. Overview
The goal is to implement an Administrative Panel for the **Vertex AI GenMedia Creative Studio** application. This panel will allow administrators to control which users (by email) have access to specific features (e.g., image generation, video generation, text generation, audio/TTS, virtual try-on, retro games) and limit the duration of their access. The admin panel itself will be protected by a designated administrative password.

## 2. Technology Stack
The application currently uses the following stack, which we will leverage for this feature to avoid introducing unnecessary dependencies:
- **Frontend / UI**: [Mesop](https://google.github.io/mesop/) (Google's Python-based UI framework, already heavily used in the app).
- **Backend**: FastAPI (serves the Mesop application and API routes).
- **Database**: Google Cloud Firestore (via `firebase-admin`, which is already included in `pyproject.toml` and used for metadata).
- **Authentication**: Existing Google Identity-Aware Proxy (IAP) flow which provides the `X-Goog-Authenticated-User-Email` header, combined with a custom password check for the admin area.

## 3. Data Model (Firestore)
We will create a new Firestore collection named `user_access_controls`.
Each document in this collection will represent a user.
- **Document ID**: User's Email Address (e.g., `user@example.com`)
- **Fields**:
  - `email` (String): The user's email address.
  - `allowed_features` (Array of Strings): Features the user can access (e.g., `["image", "video", "audio", "text", "vto", "games"]`).
  - `expiration_date` (Timestamp/Datetime): The exact date and time when the user's access expires.
  - `is_admin` (Boolean, Optional): Flag to grant admin rights to specific emails instead of just relying on a shared password.

## 4. Implementation Flow

### Phase 1: Configuration & Database Utilities
1. **Config Update (`config/default.py`)**: Add an environment variable `ADMIN_PANEL_PASSWORD` to store the shared administrative password securely.
2. **Database Service (`services/access_service.py`)**: Create a new service file with helper functions to interact with Firestore:
   - `get_user_access(email: str)`
   - `set_user_access(email: str, features: list, expiration: datetime)`
   - `list_all_users_access()`

### Phase 2: Application State Updates
1. **Update `state/state.py`**: Add new attributes to the `AppState` class to store the current user's permissions:
   - `allowed_features: list[str] = []`
   - `access_expiration: str = ""` (Stored as ISO string due to Mesop serialization constraints).
2. **Hydration**: During app initialization (when the user logs in and the email is captured from headers), fetch their permissions from Firestore using `get_user_access()` and populate the `AppState`.

### Phase 3: The Admin Panel UI (`pages/admin_panel.py`)
1. **Admin Login View**: Create a Mesop view that asks for the Administrative Password before displaying any controls. This state will be tracked in a new `AdminState` class.
2. **Dashboard View**:
   - **User List**: Display a table or list of all users currently configured in Firestore, showing their email, allowed features, and expiration dates.
   - **Add/Edit User Form**: A form with inputs for:
     - Email address (Text input).
     - Allowed Features (Checkbox group covering all features: Image, Video, Audio/TTS, Text, Virtual Try-On, Retro Games, etc.).
     - Access Duration (Date picker or Days input).
   - **Submit Action**: Calls `set_user_access()` to update Firestore in real-time.

### Phase 4: Enforcing Access Controls on Feature Pages
1. **Access Check Utility**: Create a reusable Mesop component or decorator `require_feature_access(feature_name: str)`.
2. **Page Updates**: On every major feature page (e.g., `pages/veo.py` for video, `pages/imagen.py` for images, `pages/gemini_tts.py` for audio, `pages/vto.py` for virtual try-on):
   - Wrap the main UI block in the access check utility.
   - If the user's email is not in the database, or their `expiration_date` has passed, or they lack the required feature string in `allowed_features`, render an "Access Denied / Subscription Expired" message instead of the generation controls.

## 5. Code Change Effort & Scope
- **Effort Estimate**: Low to Medium (approx. 2-3 days for a single developer familiar with Mesop and Firestore).
- **New Files**:
  - `pages/admin_panel.py` (Admin UI)
  - `state/admin_state.py` (State management for the Admin UI)
  - `services/access_service.py` (Firestore DB operations)
- **Modified Files**:
  - `main.py` (To register the new `/admin` route)
  - `state/state.py` (To hold user permission state)
  - `config/default.py` (To add admin password configuration)
  - Various `pages/*.py` files (To apply the access checks)

## 6. Security Considerations
- **Password Protection**: The admin password should be injected via environment variables and NEVER hardcoded in the repository.
- **Direct API Access**: Ensure that the FastAPI routes (`/api/...`) also verify the user's permissions before executing expensive GCP backend calls, as a tech-savvy user might try to bypass the Mesop UI and hit the API directly.
