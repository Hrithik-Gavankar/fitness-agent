"""
Authentication module for FitCoach AI.

Supports:
  - Google login via Streamlit's native OIDC (st.login)
  - GitHub login via streamlit-oauth (OAuth2)

Toggle auth on/off via `auth_enabled` in .streamlit/secrets.toml.
"""

import streamlit as st
from streamlit_oauth import OAuth2Component

GITHUB_AUTHORIZE_ENDPOINT = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_ENDPOINT = "https://github.com/login/oauth/access_token"
GITHUB_USER_API = "https://api.github.com/user"


def _is_auth_enabled() -> bool:
    return st.secrets.get("auth_enabled", False)


def _github_configured() -> bool:
    gh = st.secrets.get("github", {})
    return (
        gh.get("client_id", "").startswith("your_") is False
        and bool(gh.get("client_id"))
        and bool(gh.get("client_secret"))
        and gh.get("client_id") != "your_github_client_id"
    )


def _google_configured() -> bool:
    auth_google = st.secrets.get("auth", {}).get("google", {})
    return (
        bool(auth_google.get("client_id"))
        and auth_google.get("client_id") != "your_google_client_id"
    )


def _handle_github_login():
    """Render GitHub OAuth button and process the token exchange."""
    gh = st.secrets["github"]
    oauth2 = OAuth2Component(
        client_id=gh["client_id"],
        client_secret=gh["client_secret"],
        authorize_endpoint=GITHUB_AUTHORIZE_ENDPOINT,
        token_endpoint=GITHUB_TOKEN_ENDPOINT,
    )

    result = oauth2.authorize_button(
        name="Continue with GitHub",
        icon="https://github.githubassets.com/favicons/favicon-dark.svg",
        redirect_uri=st.secrets["auth"]["redirect_uri"],
        scope="read:user user:email",
        key="github_oauth",
        use_container_width=True,
    )

    if result and "token" in result:
        access_token = result["token"]["access_token"]
        import httpx
        resp = httpx.get(
            GITHUB_USER_API,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code == 200:
            user_data = resp.json()
            st.session_state["auth_user"] = {
                "name": user_data.get("name") or user_data.get("login", "User"),
                "email": user_data.get("email", ""),
                "avatar": user_data.get("avatar_url", ""),
                "provider": "github",
                "login": user_data.get("login", ""),
            }
            st.rerun()


def _handle_google_login():
    """Render Google login button using Streamlit's built-in OIDC."""
    if st.button("Continue with Google", use_container_width=True, type="primary"):
        st.login("google")


def _get_authenticated_user() -> dict | None:
    """Return the logged-in user dict, or None if not authenticated."""
    if st.session_state.get("auth_user"):
        return st.session_state["auth_user"]

    if hasattr(st, "user") and hasattr(st.user, "is_logged_in") and st.user.is_logged_in:
        st.session_state["auth_user"] = {
            "name": getattr(st.user, "name", "User"),
            "email": getattr(st.user, "email", ""),
            "avatar": "",
            "provider": "google",
        }
        return st.session_state["auth_user"]

    return None


def is_authenticated() -> bool:
    """Check if user is authenticated (or auth is disabled)."""
    if not _is_auth_enabled():
        return True
    return _get_authenticated_user() is not None


def render_login_page():
    """Show login screen. Call only when is_authenticated() returns False."""
    st.markdown("""
    <style>
        .login-container {
            max-width: 420px;
            margin: 2rem auto;
            padding: 2.5rem;
            border-radius: 20px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            text-align: center;
        }
        .login-container h1 {
            font-size: 2rem;
            margin-bottom: 0.3rem;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .login-container p {
            opacity: 0.8;
            font-size: 0.95rem;
            margin-bottom: 1.5rem;
        }
        .login-divider {
            display: flex;
            align-items: center;
            margin: 1.2rem 0;
            color: rgba(255,255,255,0.4);
            font-size: 0.8rem;
        }
        .login-divider::before, .login-divider::after {
            content: "";
            flex: 1;
            border-bottom: 1px solid rgba(255,255,255,0.15);
        }
        .login-divider::before { margin-right: 0.8rem; }
        .login-divider::after { margin-left: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="login-container">
            <h1>FitCoach AI</h1>
            <p>Sign in to access your personalized fitness coach</p>
        </div>
        """, unsafe_allow_html=True)

        google_ok = _google_configured()
        github_ok = _github_configured()

        if not google_ok and not github_ok:
            st.warning(
                "No OAuth providers configured. "
                "Set up Google and/or GitHub credentials in `.streamlit/secrets.toml`. "
                "Or set `auth_enabled = false` to skip login."
            )
            st.stop()

        if google_ok:
            _handle_google_login()

        if google_ok and github_ok:
            st.markdown('<div class="login-divider">or</div>', unsafe_allow_html=True)

        if github_ok:
            _handle_github_login()

    st.stop()


def render_user_badge():
    """Show logged-in user info and logout button in the sidebar."""
    if not _is_auth_enabled():
        return

    user = _get_authenticated_user()
    if not user:
        return

    with st.sidebar:
        provider_icon = {"google": "🔵", "github": "⚫"}.get(user.get("provider", ""), "👤")
        st.markdown(f"**{provider_icon} {user['name']}**")
        if user.get("email"):
            st.caption(user["email"])

        if st.button("Log out", use_container_width=True):
            st.session_state.pop("auth_user", None)
            for key in ["messages", "adk_session_id", "adk_runner", "adk_session_service"]:
                st.session_state.pop(key, None)
            if hasattr(st, "logout"):
                st.logout()
            st.rerun()

        st.divider()
