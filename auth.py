"""
Authentication module for FitCoach AI.

Uses Supabase Auth with OAuth providers (Google, GitHub).
Auth is optional — disabled when SUPABASE_URL is not set.

Flow (PKCE):
  1. User clicks "Sign in with Google/GitHub"
  2. supabase-py generates code_verifier, stores in FileStorage (persists to disk)
  3. Browser redirects to Supabase → provider → back with ?code=
  4. Python exchanges code + stored code_verifier for a session
  5. Session is persisted in FileStorage — survives page refreshes
"""

import json
import os

import streamlit as st
from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions
from supabase_auth import SyncSupportedStorage

AUTH_STORAGE_PATH = os.path.join(os.path.dirname(__file__), ".auth_storage.json")


class _FileStorage(SyncSupportedStorage):
    """Persist auth state to disk — survives both OAuth redirects and page refreshes."""

    def __init__(self):
        self._data: dict = {}
        if os.path.exists(AUTH_STORAGE_PATH):
            try:
                with open(AUTH_STORAGE_PATH) as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}

    def _flush(self):
        with open(AUTH_STORAGE_PATH, "w") as f:
            json.dump(self._data, f)

    def get_item(self, key: str) -> str | None:
        return self._data.get(key)

    def set_item(self, key: str, value: str):
        self._data[key] = value
        self._flush()

    def remove_item(self, key: str):
        self._data.pop(key, None)
        self._flush()


def _auth_enabled() -> bool:
    return bool(os.environ.get("SUPABASE_URL")) and bool(os.environ.get("SUPABASE_ANON_KEY"))


def _get_client() -> Client:
    if "supabase_client" not in st.session_state:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_ANON_KEY", "")
        st.session_state["supabase_client"] = create_client(
            url, key,
            options=SyncClientOptions(
                storage=_FileStorage(),
                flow_type="pkce",
            ),
        )
    return st.session_state["supabase_client"]


def _redirect_url() -> str:
    return os.environ.get("AUTH_REDIRECT_URL", "http://localhost:8501")


def _extract_user(user) -> dict:
    """Extract user info dict from a Supabase User object."""
    meta = user.user_metadata or {}
    return {
        "id": user.id,
        "email": user.email or "",
        "name": (
            meta.get("full_name")
            or meta.get("name")
            or meta.get("user_name")
            or user.email
            or "User"
        ),
        "avatar": meta.get("avatar_url", ""),
        "provider": (user.app_metadata or {}).get("provider", "unknown"),
    }


def _get_oauth_url(provider: str) -> str:
    client = _get_client()
    options = {"redirect_to": _redirect_url()}
    if provider == "google":
        options["query_params"] = {"prompt": "select_account"}
    response = client.auth.sign_in_with_oauth({
        "provider": provider,
        "options": options,
    })
    return response.url


# ── Session recovery & callback ───────────────────────────────────────────────

def _try_recover_session() -> bool:
    """Try to recover an existing session from FileStorage (survives refreshes)."""
    if st.session_state.get("auth_user"):
        return True

    try:
        client = _get_client()
        response = client.auth.get_session()
        if response and response.user:
            st.session_state["auth_user"] = _extract_user(response.user)
            return True
    except Exception:
        pass

    return False


def _try_consume_callback() -> bool:
    """Check URL for PKCE auth code, exchange for session. Returns True if consumed."""
    code = st.query_params.get("code")
    if not code:
        return False

    try:
        client = _get_client()
        response = client.auth.exchange_code_for_session({"auth_code": code})
        if response.user:
            st.session_state["auth_user"] = _extract_user(response.user)
            st.query_params.clear()
            return True
    except Exception as e:
        st.query_params.clear()
        st.error(f"Authentication failed: {e}")

    return False


# ── Public API ────────────────────────────────────────────────────────────────

def is_authenticated() -> bool:
    if not _auth_enabled():
        return True
    return _try_recover_session()


def render_login_page():
    """Full-page login screen with Google and GitHub buttons. Calls st.stop()."""
    if _try_consume_callback():
        st.rerun()

    st.markdown("""
    <style>
        .login-hero {
            max-width: 440px;
            margin: 3rem auto 1.5rem auto;
            text-align: center;
        }
        .login-hero h1 {
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.4rem;
        }
        .login-hero p {
            color: #888;
            font-size: 1rem;
            margin-bottom: 0;
        }
        .login-divider {
            display: flex;
            align-items: center;
            margin: 1rem 0;
            color: rgba(150,150,150,0.5);
            font-size: 0.8rem;
        }
        .login-divider::before, .login-divider::after {
            content: "";
            flex: 1;
            border-bottom: 1px solid rgba(150,150,150,0.2);
        }
        .login-divider::before { margin-right: 0.8rem; }
        .login-divider::after  { margin-left:  0.8rem; }
        .oauth-btn {
            display: inline-block;
            width: 100%;
            padding: 0.65rem 1rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.95rem;
            text-align: center;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        .oauth-btn:hover { opacity: 0.9; }
        .oauth-btn-google {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white !important;
        }
        .oauth-btn-github {
            background: linear-gradient(135deg, #2b3137, #24292e);
            color: white !important;
            border: 1px solid #555;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .oauth-btn-github:hover {
            background: linear-gradient(135deg, #3a4149, #2b3137);
            border-color: #777;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="login-hero">
            <h1>FitCoach AI</h1>
            <p>Sign in to access your personalized fitness coach</p>
        </div>
        """, unsafe_allow_html=True)

        pending = st.session_state.get("_auth_provider")

        if pending:
            provider_label = pending.title()
            url = _get_oauth_url(pending)
            st.session_state.pop("_auth_provider", None)

            st.markdown(
                f'<meta http-equiv="refresh" content="0;url={url}">'
                f'<p style="text-align:center;color:#888;margin:2rem 0 1rem">'
                f'Redirecting to {provider_label}...</p>'
                f'<a href="{url}" class="oauth-btn oauth-btn-google">'
                f'Click here if not redirected</a>',
                unsafe_allow_html=True,
            )
        else:
            if st.button("Continue with Google", use_container_width=True, type="primary"):
                st.session_state["_auth_provider"] = "google"
                st.rerun()

            st.markdown('<div class="login-divider">or</div>', unsafe_allow_html=True)

            if st.button("Continue with GitHub", use_container_width=True):
                st.session_state["_auth_provider"] = "github"
                st.rerun()

    st.stop()


def render_user_badge():
    """Show logged-in user info and logout button in the sidebar."""
    if not _auth_enabled():
        return

    user = st.session_state.get("auth_user")
    if not user:
        return

    with st.sidebar:
        avatar = user.get("avatar")
        name = user.get("name", "User")

        if avatar:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.3rem">'
                f'<img src="{avatar}" width="32" height="32" style="border-radius:50%">'
                f'<strong style="color:#fff">{name}</strong>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f"**{name}**")

        if user.get("email"):
            st.caption(user["email"])

        if st.button("Log out", use_container_width=True):
            try:
                _get_client().auth.sign_out()
            except Exception:
                pass
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            if os.path.exists(AUTH_STORAGE_PATH):
                os.remove(AUTH_STORAGE_PATH)
            st.rerun()

        st.divider()
