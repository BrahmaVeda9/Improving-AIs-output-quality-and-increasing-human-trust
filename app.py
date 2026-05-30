import os
import uuid
import streamlit as st
import streamlit.components.v1 as components
import urllib.parse
from core.seam_db import save_message, get_chat_history, get_sessions, clear_session
from core.seam_llm import chat_completion, parse_signals_seam, get_signal_style_rules

# Page configuration
st.set_page_config(
    page_title="Seam AI — See what the AI isn't telling you",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Obsidian Dark Theme CSS overrides (worth $5000+ elegant ChatGPT style layout)
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global Font Override */
html, body, [class*="css"], .stMarkdown {
    font-family: 'Inter', sans-serif !important;
}

/* Base Body Dark Styling */
.stApp {
    background-color: #171717 !important;
    color: #ececec !important;
}

/* Hide Streamlit default headers, decoration, and footers */
[data-testid="stHeader"] {
    display: none !important;
}
footer {
    visibility: hidden !important;
    height: 0px !important;
    padding: 0px !important;
}
[data-testid="stDecoration"] {
    display: none !important;
}

/* Custom Obsidian Scrollbar */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-track {
    background: #171717;
}
::-webkit-scrollbar-thumb {
    background: #2f2f2f;
    border-radius: 99px;
}
::-webkit-scrollbar-thumb:hover {
    background: #424242;
}

/* Force main container to use full viewport width and ignore sidebar layout shifting */
[data-testid="stAppViewContainer"] {
    padding: 0 !important;
    margin: 0 !important;
    width: 100vw !important;
    max-width: 100vw !important;
}

[data-testid="stMain"] {
    position: absolute !important;
    left: 0 !important;
    top: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
    margin-left: 0 !important;
    padding-left: 0 !important;
}

/* Main Container margins and alignment - centered relative to stable full-width viewport */
div.block-container {
    padding-top: 8.5rem !important; /* Space below fixed top bar */
    padding-bottom: 11rem !important; /* Space above input bar and toggle */
    max-width: 680px !important; /* exact ChatGPT content width */
    margin: 0 auto !important; /* Centers perfectly inside full-width main view */
    background-color: #171717 !important;
    overflow: visible !important;
}

/* Sidebar styling overrides - Minimalist deep dark overlay */
[data-testid="stSidebar"] {
    background-color: #0d0d0d !important;
    border-right: 1px solid #2f2f2f !important;
    position: fixed !important;
    z-index: 100000 !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: #94a3b8 !important;
}

/* Top bar - fixed top center, glassmorphic */
.topbar-seam {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 88px; /* Taller, prominent top bar */
    background-color: rgba(23, 23, 23, 0.85) !important;
    border-bottom: 1px solid #2f2f2f;
    display: flex;
    align-items: center;
    justify-content: center; /* Center horizontally! */
    padding: 0 24px;
    z-index: 9999;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
}

.logo-container-seam {
    display: flex;
    align-items: center;
    gap: 16px;
}

.logo-icon-seam {
    width: 32px; /* Bigger logo icon */
    height: 32px; /* Bigger logo icon */
    background-color: #ffffff;
    clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%); /* Split diamond icon */
    box-shadow: 0 0 16px rgba(255, 255, 255, 0.4);
}

.logo-text-seam {
    font-size: 36px; /* Larger logo text */
    font-weight: 800; /* Extra bold */
    color: #ffffff;
    letter-spacing: 0.8px;
    background: linear-gradient(135deg, #ffffff 0%, #a5b4fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Floating st.toggle overlay positioning - aligned right above the send button */
div[data-testid="stCheckbox"] {
    position: fixed !important;
    bottom: 152px !important; /* Floats just above the capsule top edge (24px bottom + 120px height + 8px gap) */
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: calc(100% - 40px) !important;
    max-width: 680px !important;
    display: flex !important;
    justify-content: flex-end !important;
    z-index: 100000 !important;
    pointer-events: none !important;
}

div[data-testid="stCheckbox"] label {
    pointer-events: auto !important;
    background-color: rgba(33, 33, 33, 0.85) !important;
    border: 1px solid #2f2f2f !important;
    padding: 6px 14px !important;
    border-radius: 14px !important;
    backdrop-filter: blur(8px) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    margin: 0 !important;
}

/* Style Streamlit toggle globally */
div[data-testid="stCheckbox"] label p {
    font-size: 11.5px !important;
    font-weight: 600 !important;
    color: #94a3b8 !important;
    margin: 0 !important;
}

/* Override Streamlit toggle base-web switch style */
div[role="switch"] {
    background-color: #2f2f2f !important; /* Dark track when off */
    border: 1px solid #424242 !important;
    border-radius: 99px !important;
}

div[role="switch"][aria-checked="true"] {
    background-color: #10b981 !important; /* Green track when on */
    border-color: #10b981 !important;
}

/* Custom logo tagline in topbar */
.logo-tagline-seam {
    font-size: 11px !important;
    font-weight: 400 !important;
    color: #94a3b8 !important;
    opacity: 0.6 !important;
    letter-spacing: 0.5px !important;
    text-transform: none !important;
    margin-top: 4px !important;
}

/* Hide Streamlit default Ctrl+Enter helper instructions inside forms */
[data-testid="InputInstructions"] {
    display: none !important;
}

/* Sidebar Custom elements */
.sidebar-title-seam {
    font-size: 11px;
    font-weight: 600;
    color: #555555;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 24px;
    margin-bottom: 8px;
    padding-left: 8px;
}

/* Global button override - light-colored labels, clean lines */
.stButton button, [data-testid="stSidebar"] .stButton button {
    background-color: #212121 !important;
    color: #ececec !important;
    border: 1px solid #2f2f2f !important;
    border-radius: 99px !important; /* Pill shaped example prompts */
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 6px 14px !important;
    width: auto !important;
    transition: all 150ms ease !important;
    box-shadow: none !important;
    text-align: center !important;
}

.stButton button:hover, [data-testid="stSidebar"] .stButton button:hover {
    background-color: #2f2f2f !important;
    border-color: #424242 !important;
    color: #ffffff !important;
}

/* Sidebar buttons overrides - square rounded */
[data-testid="stSidebar"] .stButton button {
    border-radius: 8px !important;
    width: 100% !important;
}

/* Recent Session Items in sidebar */
.session-item {
    display: block;
    padding: 10px 12px;
    border-radius: 8px;
    text-decoration: none;
    color: #b4b4b4 !important;
    font-size: 13px !important;
    margin-bottom: 4px;
    transition: all 150ms ease;
    border-left: 3px solid transparent;
}

.session-item:hover {
    background-color: #212121;
    color: #ffffff !important;
}

.session-item.active {
    background-color: #212121;
    color: #60a5fa !important;
    border-left: 3px solid #3b82f6 !important;
}

.session-title {
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 100%;
}

/* Chat convo area */
.msg-container {
    display: flex;
    flex-direction: column;
    gap: 28px;
    overflow: visible !important;
}

.bubble-row-seam {
    display: flex;
    gap: 16px;
    align-items: flex-start;
    animation: slideIn-seam 200ms ease-out forwards;
    opacity: 0;
    transform: translateY(8px);
    overflow: visible !important;
    margin-bottom: 36px !important;
}

@keyframes slideIn-seam {
    to { opacity: 1; transform: translateY(0); }
}

.bubble-row-seam.user-row {
    justify-content: flex-end;
}

/* User Message bubble - aligned right, dark gray capsule */
.bub-seam-user {
    background-color: #2f2f2f;
    color: #ececec;
    padding: 10px 16px;
    border-radius: 20px;
    font-size: 14.5px;
    line-height: 1.6;
    max-width: 70%;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    border: 1px solid #3c3c3c;
}

/* Assistant Message bubble - aligned left, transparent, avatar next to it */
.bub-seam-ai {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    max-width: 100%;
    overflow: visible !important;
}

.ai-avatar-seam {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background-color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #171717;
    flex-shrink: 0;
}

.ai-avatar-icon-seam {
    width: 10px;
    height: 10px;
    background-color: #171717;
    clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
}

.bub-seam-content {
    background-color: transparent !important;
    color: #ececec;
    padding: 2px 0px;
    font-size: 14.5px;
    line-height: 1.65;
    flex-grow: 1;
    overflow: visible !important;
}

.bub-seam-content p {
    margin-bottom: 12px;
}
.bub-seam-content p:last-child {
    margin-bottom: 0;
}
.bub-seam-content ul, .bub-seam-content ol {
    margin: 8px 0 8px 18px;
}

/* Dynamic Highlights selector classes */
.sig-text-highlight {
    transition: all 150ms ease;
}

/* Inline transparency pills */
.chip-container {
    position: relative;
    display: inline-block;
    vertical-align: middle;
    overflow: visible !important;
}

.chip {
    display: inline-flex;
    align-items: center;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    margin: 0 3px;
    vertical-align: middle;
    line-height: 1.4;
    transition: all 150ms ease;
    border: 0.5px solid transparent;
    user-select: none;
}

.chip:hover {
    filter: brightness(1.15);
}

/* Color specifications for pills */
.c-assumed { background-color: #f59e0b !important; color: #78350f !important; border-color: rgba(245, 158, 11, 0.4) !important; }
.c-uncertain { background-color: #fee2e2 !important; color: #991b1b !important; border-color: rgba(248, 113, 113, 0.4) !important; }
.c-outdated { background-color: #ffedd5 !important; color: #9a3412 !important; border-color: rgba(251, 146, 60, 0.4) !important; }
.c-context { background-color: #dbeafe !important; color: #1e40af !important; border-color: rgba(96, 165, 250, 0.4) !important; }
.c-conflict { background-color: #d1fae5 !important; color: #065f46 !important; border-color: rgba(52, 211, 153, 0.4) !important; }
.c-unverifiable { background-color: #ede9fe !important; color: #5b21b6 !important; border-color: rgba(167, 139, 250, 0.4) !important; }
.c-tradeoff { background-color: #fce7f3 !important; color: #9d174d !important; border-color: rgba(244, 114, 182, 0.4) !important; }

/* Popover card tooltip */
.popup {
    display: none;
    position: absolute;
    bottom: calc(100% + 12px);
    left: 0;
    width: 340px;
    background-color: #2f2f2f;
    border: 1px solid #424242;
    border-radius: 12px;
    padding: 12px;
    z-index: 99999 !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    color: #ececec;
    text-align: left;
    animation: popFade-seam 150ms ease-out;
}

.popup::after {
    content: "";
    position: absolute;
    top: var(--arrow-top, 100%);
    bottom: var(--arrow-bottom, auto);
    left: var(--arrow-left, 24px);
    border-width: 6px;
    border-style: solid;
    border-color: var(--arrow-color, #2f2f2f transparent transparent transparent);
}
.popup::before {
    content: "";
    position: absolute;
    top: var(--arrow-top, 100%);
    bottom: var(--arrow-bottom, auto);
    left: calc(var(--arrow-left, 24px) - 1px);
    border-width: 7px;
    border-style: solid;
    border-color: var(--arrow-border-color, #424242 transparent transparent transparent);
}

@keyframes popFade-seam {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
}

.popup h4 {
    font-size: 12px;
    font-weight: 600;
    margin: 0 0 6px 0;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 6px;
}

.popup p {
    font-size: 13px;
    color: #b4b4b4;
    line-height: 1.5;
    margin: 0 0 12px 0;
}

.pact {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
}

.pbtn {
    display: inline-block;
    font-size: 11px;
    padding: 5px 10px;
    border-radius: 6px;
    border: 1px solid #424242;
    background: #212121;
    color: #cbd5e1;
    cursor: pointer;
    text-decoration: none;
    font-family: inherit;
    text-align: center;
    font-weight: 500;
    transition: all 150ms ease;
}

.pbtn.green {
    background: #ffffff;
    color: #171717;
    border-color: #ffffff;
}

.pbtn:hover {
    background: #2f2f2f;
    color: #ffffff;
}

.pbtn.green:hover {
    background: #10b981;
    border-color: #10b981;
    color: #ffffff;
}

/* Popups are displayed on hover via JavaScript. Clicking signal chips toggles highlights only. */

/* Streamlit Form Column styling overrides to support absolute positioned send button */
div[data-testid="stForm"] [data-testid="column"],
div[data-testid="stForm"] [data-testid="stHorizontalBlock"],
div[data-testid="stForm"] [data-testid="element-container"],
div[data-testid="stForm"] .stButton,
div[data-testid="stForm"] [data-testid="stFormSubmitButton"] {
    position: static !important;
}

/* Floating bottom capsule styled like ChatGPT with extra padding right to hold st.toggle and button side-by-side */
div[data-testid="stForm"] {
    position: fixed !important;
    bottom: 24px !important;
    left: calc(50vw - 340px) !important; /* Stable centering relative to viewport */
    transform: none !important;
    width: 680px !important;
    max-width: calc(100vw - 40px) !important;
    background-color: #212121 !important; /* Dark input container */
    border: 1px solid #2f2f2f !important;
    border-radius: 20px !important; /* Slightly rounded corners */
    padding: 12px 16px 56px 16px !important; /* Room at bottom for send button */
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4) !important;
    z-index: 9999 !important;
    transition: box-shadow 150ms ease !important;
    height: 120px !important; /* Tall box layout */
}
div[data-testid="stForm"]:focus-within {
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4) !important;
    border-color: #2f2f2f !important;
}

/* Force dark theme input overrides - completely suppress all blue/focus styling */
div[data-testid="stForm"] div[data-baseweb="input"],
div[data-testid="stForm"] div[data-baseweb="input"]:focus-within,
div[data-testid="stForm"] div[data-baseweb="input"]:hover,
div[data-testid="stForm"] div[data-baseweb="input"] > div,
div[data-testid="stForm"] div[data-baseweb="base-input"],
div[data-testid="stForm"] div[data-baseweb="base-input"]:focus-within,
div[data-testid="stForm"] div[data-baseweb="base-input"] > div {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    padding: 0 !important;
}
div[data-testid="stForm"] input[type="text"],
div[data-testid="stForm"] input {
    background-color: transparent !important;
    border: none !important;
    color: #ececec !important;
    font-size: 14.5px !important;
    height: 52px !important;
    padding: 0 !important;
    outline: none !important;
    box-shadow: none !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-testid="stForm"] input::placeholder {
    color: #6b7280 !important;
}
div[data-testid="stForm"] input:focus,
div[data-testid="stForm"] input:focus-visible {
    box-shadow: none !important;
    outline: none !important;
    border: none !important;
}

/* Send circle button - blue circle with white right arrow icon */
div[data-testid="stForm"] button {
    position: absolute !important;
    right: 16px !important;
    bottom: 14px !important; /* Positioned at bottom right inside the taller box */
    top: auto !important;
    transform: none !important;
    background: #0084ff !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 50% !important;
    width: 36px !important;
    height: 36px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 18px !important;
    cursor: pointer !important;
    transition: all 150ms ease !important;
    box-shadow: 0 2px 8px rgba(0, 132, 255, 0.3) !important;
}
div[data-testid="stForm"] button:hover {
    background: #0076e4 !important;
    color: #ffffff !important;
    transform: scale(1.05) !important;
}

/* Example Prompts container */
.example-container {
    display: flex;
    gap: 12px;
    justify-content: center;
    margin-top: 24px;
}

/* Loading animations inside transparent bubble */
.loading-bubble {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 6px 0px;
}
.loading-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: #9ca3af;
    animation: dotPulse-seam 1.2s infinite ease-in-out;
}
.loading-dot:nth-child(2) { animation-delay: 0.2s; }
.loading-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes dotPulse-seam {
    0%, 100% { transform: scale(0.6); opacity: 0.4; }
    50% { transform: scale(1.2); opacity: 1; }
}

/* Error message bubble */
.error-bubble {
    background-color: #2a1111;
    border: 1px solid #4a1c1c;
    color: #fca5a5;
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 13.5px;
    line-height: 1.5;
    margin: 12px 0;
    width: 100%;
}

/* Interactive click press scale effect */
.stButton button:active {
    transform: scale(0.97) !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# URL query parameter handler
query_params = st.query_params

# Initialize session states
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "signals_on" not in st.session_state:
    st.session_state.signals_on = True

if "signals_toggle" not in st.session_state:
    st.session_state.signals_toggle = True

if "chat_input_val" not in st.session_state:
    st.session_state.chat_input_val = ""

# Handle session parameter reload from sidebar links
if "session_id" in query_params:
    st.session_state.session_id = query_params["session_id"][0]
    st.session_state.chat_input_val = ""
    st.query_params.clear()
    st.rerun()

# ----------------- Ask about this Trigger Handler -----------------
# If a query is loaded in parameters, save it, make Groq request directly, and rerun.
# Appends it to the active session_id thread context!
if "query" in query_params:
    q_val = urllib.parse.unquote_plus(query_params["query"])
    sess_val = st.session_state.session_id
    
    # Save the follow-up message to continue the chat thread!
    save_message(sess_val, "user", q_val)
    history = get_chat_history(sess_val)
    
    try:
        llm_result = chat_completion(history)
        response_text = llm_result.get("response", "")
        signals_array = llm_result.get("signals", [])
        save_message(sess_val, "assistant", response_text, signals_array)
    except Exception as e:
        save_message(sess_val, "assistant", f'<div class="error-bubble">Groq API Error: {str(e)}</div>', [])
        
    st.query_params.clear()
    st.rerun()

# Sidebar logic
with st.sidebar:
    # New chat button
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.chat_input_val = ""
        st.rerun()

    st.markdown('<div class="sidebar-title-seam">Recent</div>', unsafe_allow_html=True)
    sessions = get_sessions()
    
    if sessions:
        for idx, sess in enumerate(sessions[:10]):
            history = get_chat_history(sess)
            first_user_msg = "New Conversation"
            for m in history:
                if m["role"] == "user":
                    first_user_msg = m["content"]
                    break
            
            trunc_title = (first_user_msg[:42] + "...") if len(first_user_msg) > 45 else first_user_msg
            is_active = sess == st.session_state.session_id
            active_class = "active" if is_active else ""
            
            session_item_html = f"""
            <a href="?session_id={sess}" target="_self" class="session-item {active_class}">
              <div class="session-title">{trunc_title}</div>
            </a>
            """
            st.markdown(session_item_html, unsafe_allow_html=True)
    else:
        st.write("No recent chats.")

    # Clear history button
    st.markdown("---")
    if st.button("🗑️ Clear Sessions", use_container_width=True):
        clear_session(st.session_state.session_id)
        st.session_state.chat_input_val = ""
        st.rerun()

# --- Main Interface ---

# Render the Seam Top Bar structure (centered and larger SEAM logo with faded tagline)
topbar_html = """
<div class="topbar-seam">
  <div class="logo-container-seam" style="flex-direction: column; gap: 4px; display: flex; align-items: center;">
    <div style="display: flex; align-items: center; gap: 16px;">
      <div class="logo-icon-seam"></div>
      <span class="logo-text-seam">SEAM</span>
    </div>
    <span class="logo-tagline-seam">See what the AI isn't telling you</span>
  </div>
</div>
"""
st.markdown(topbar_html, unsafe_allow_html=True)

# Render native Streamlit toggle — default ON, positioned in bottom bar via CSS
if "signals_toggle" not in st.session_state:
    st.session_state.signals_toggle = True
signals_checked = st.toggle("Illuminate", key="signals_toggle", label_visibility="visible")
st.session_state.signals_on = signals_checked  # always sync immediately after widget render


# Check for API Key Configuration
api_key_configured = True
api_error_msg = ""
try:
    from core.seam_llm import get_groq_client
    get_groq_client()
except ValueError as ve:
    api_key_configured = False
    api_error_msg = str(ve)

# Retrieve current chat history
chat_history = get_chat_history(st.session_state.session_id)

# Collect and inject dynamic highlight style rules (including hover tooltips) globally
all_style_rules = ""
for idx, msg in enumerate(chat_history):
    if msg["role"] == "assistant":
        all_style_rules += get_signal_style_rules(msg.get("signals", []), idx)

if all_style_rules:
    st.markdown(f"<style>{all_style_rules}</style>", unsafe_allow_html=True)

# Render Chat list or Empty state
if not chat_history:
    # 3 example prompts
    example_prompts = [
        ("🔮 Next World Cup", "Who will win the next World Cup?"),
        ("💰 Invest in Crypto", "Should I invest in cryptocurrency right now?"),
        ("📄 Online Business Taxes", "Detail the current tax regulations for online businesses.")
    ]
    
    # Render example pills and handle DIRECT triggers
    st.markdown('<div class="example-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    selected_prompt = None
    with col1:
        if st.button(example_prompts[0][0], key="ex_1", use_container_width=True):
            selected_prompt = example_prompts[0][1]
    with col2:
        if st.button(example_prompts[1][0], key="ex_2", use_container_width=True):
            selected_prompt = example_prompts[1][1]
    with col3:
        if st.button(example_prompts[2][0], key="ex_3", use_container_width=True):
            selected_prompt = example_prompts[2][1]
    st.markdown('</div>', unsafe_allow_html=True)

    # If any example prompt was clicked, submit it DIRECTLY to Groq
    if selected_prompt:
        save_message(st.session_state.session_id, "user", selected_prompt)
        history = get_chat_history(st.session_state.session_id)
        
        # Show animated loading dots
        loading_placeholder = st.empty()
        loading_html = """
        <div class="bubble-row-seam">
          <div class="ai-avatar-seam"><div class="ai-avatar-icon-seam"></div></div>
          <div class="bub-seam-content">
            <div class="loading-bubble">
              <span class="loading-dot"></span>
              <span class="loading-dot"></span>
              <span class="loading-dot"></span>
            </div>
          </div>
        </div>
        """
        loading_placeholder.markdown(loading_html, unsafe_allow_html=True)
        
        try:
            llm_result = chat_completion(history)
            loading_placeholder.empty()
            save_message(
                st.session_state.session_id, 
                "assistant", 
                llm_result.get("response", ""), 
                llm_result.get("signals", [])
            )
        except Exception as e:
            loading_placeholder.empty()
            save_message(st.session_state.session_id, "assistant", f'<div class="error-bubble">Groq API Error: {str(e)}</div>', [])
            
        st.session_state.chat_input_val = ""
        st.rerun()

else:
    # Render convo container
    st.markdown('<div class="msg-container">', unsafe_allow_html=True)
    for idx, msg in enumerate(chat_history):
        role = msg["role"]
        content = msg["content"]
        signals = msg.get("signals", [])
        
        if role == "user":
            user_html = f"""
            <div class="bubble-row-seam user-row">
              <div class="bub-seam-user">{content}</div>
            </div>
            """
            st.markdown(user_html, unsafe_allow_html=True)
        else:
            # Parse signals using the new selector and highlight mechanism
            parsed_content = parse_signals_seam(content, signals, st.session_state.signals_on, idx)
            ai_html = f"""
            <div class="bubble-row-seam">
              <div class="ai-avatar-seam">
                <div class="ai-avatar-icon-seam"></div>
              </div>
              <div class="bub-seam-content">{parsed_content}</div>
            </div>
            """
            st.markdown(ai_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Floating Input Form block
if not api_key_configured:
    st.markdown(f'<div class="error-bubble">🔒 API Error: {api_error_msg}</div>', unsafe_allow_html=True)
else:
    with st.form("chat_form", clear_on_submit=True):
        # st.text_input natively submits on Enter key — no JavaScript needed
        user_input_val = st.text_input(
            "Ask Seam anything...",
            value=st.session_state.chat_input_val,
            placeholder="Ask Seam anything...",
            label_visibility="collapsed"
        )
        # Classy right arrow icon inside blue circle
        submit_clicked = st.form_submit_button("→")

    # Chat execution logic on submit (submits on Enter key automatically!)
    if submit_clicked and user_input_val.strip():
        user_query = user_input_val.strip()
        
        # Save user message to database wrapper
        save_message(st.session_state.session_id, "user", user_query)
        
        # Reload history to keep context context-aware
        history = get_chat_history(st.session_state.session_id)
        
        # Show animated loading dots inside assistant bubble
        loading_placeholder = st.empty()
        loading_html = """
        <div class="bubble-row-seam">
          <div class="ai-avatar-seam"><div class="ai-avatar-icon-seam"></div></div>
          <div class="bub-seam-content">
            <div class="loading-bubble">
              <span class="loading-dot"></span>
              <span class="loading-dot"></span>
              <span class="loading-dot"></span>
            </div>
          </div>
        </div>
        """
        loading_placeholder.markdown(loading_html, unsafe_allow_html=True)
        
        try:
            # Query Groq JSONCompletion API
            llm_result = chat_completion(history)
            
            # Clear loading bubble
            loading_placeholder.empty()
            
            # Retrieve values
            response_text = llm_result.get("response", "")
            signals_array = llm_result.get("signals", [])
            
            # Save assistant response
            save_message(st.session_state.session_id, "assistant", response_text, signals_array)
        except Exception as e:
            # Clear loading bubble and insert error bubble into thread
            loading_placeholder.empty()
            error_msg = f"Groq API Error: {str(e)}"
            save_message(st.session_state.session_id, "assistant", f'<div class="error-bubble">{error_msg}</div>', [])
            
        # Reset text area states and rerun UI
        st.session_state.chat_input_val = ""
        st.rerun()

    # JS: signal popup dedup + Ask Seam button handler (onclick is stripped by Streamlit sanitizer,
    # so we bind handlers from components.html which runs in a same-origin iframe with parent access)
    popup_js = """
    <script>
    (function() {
        var P = window.parent;
        var D = P.document;

        P.__seamOnSignalLabelClick = function(label) {
            var toggleId = label.getAttribute('for');
            var cb = D.getElementById(toggleId);
            if (!cb) return;
            var wasChecked = cb.checked;
            
            cb.checked = !wasChecked;
            cb.dispatchEvent(new P.Event('change', { bubbles: true }));
        };
        
        P.__seamOnAskSeam = function(btn) {
            var query = btn.getAttribute('data-ask-seam');
            var sigId = btn.getAttribute('data-sig-id');

            // Set input value via native React-compatible setter
            var inp = D.querySelector('div[data-testid="stForm"] input');
            if (inp && query) {
                var setter = Object.getOwnPropertyDescriptor(P.HTMLInputElement.prototype, 'value').set;
                setter.call(inp, query);
                inp.dispatchEvent(new P.InputEvent('input', { bubbles: true, cancelable: true }));
                inp.dispatchEvent(new P.Event('change', { bubbles: true }));
                
                // Submit the form!
                var form = inp.closest('form');
                if (form) {
                    var submitBtn = form.querySelector('button[type="submit"]') || form.querySelector('button[data-testid="stFormSubmitButton"]');
                    if (submitBtn) {
                        submitBtn.click();
                    } else {
                        form.submit();
                    }
                }
            }

            // Close the popup
            if (P.__seamHideTooltip) P.__seamHideTooltip();

            // Uncheck the toggle to reset highlight state
            if (sigId) {
                var toggle = D.getElementById(sigId);
                if (toggle) {
                    toggle.checked = false;
                    toggle.dispatchEvent(new P.Event('change', { bubbles: true }));
                }
            }
        };

        P.__seamOnDismiss = function(btn) {
            var toggleId = btn.getAttribute('data-close-toggle');
            
            // Toggle the dismiss checkbox
            var dismissToggleId = toggleId.replace('sig-toggle-', 'sig-dismiss-');
            var dismissToggle = D.getElementById(dismissToggleId);
            if (dismissToggle) {
                dismissToggle.checked = true;
                dismissToggle.dispatchEvent(new P.Event('change', { bubbles: true }));
            }
            
            // Close the toggle checkbox
            var toggle = D.getElementById(toggleId);
            if (toggle) {
                toggle.checked = false;
                toggle.dispatchEvent(new P.Event('change', { bubbles: true }));
            }
            
            // Close the popup
            if (P.__seamHideTooltip) P.__seamHideTooltip();
        };

        // Hover Tooltip logic
        var activePopup = null;
        var hoverTimeout = null;

        P.__seamShowTooltip = function(target, groupId) {
            if (hoverTimeout) clearTimeout(hoverTimeout);
            
            var popup = target.querySelector('.popup');
            if (!popup) return;
            
            // If another popup is active, hide it first (unless it is this one!)
            if (activePopup && activePopup !== popup) {
                activePopup.style.display = 'none';
            }
            
            // 1. Show the popup first to ensure it has valid layout dimensions
            popup.style.display = 'block';
            popup.style.position = 'absolute';
            popup.style.bottom = 'auto';
            popup.style.zIndex = '999999';
            
            // 2. Measure coordinates
            var rect = target.getBoundingClientRect();
            var popupRect = popup.getBoundingClientRect();
            
            // 3. Compute relative positioning
            var top = -popupRect.height - 8;
            var left = (rect.width - popupRect.width) / 2;
            
            // Fallback for top screen edge (rect.top is viewport relative)
            if (rect.top - popupRect.height - 8 < 10) {
                top = rect.height + 8;
                // Reverse the arrow pointer to point upwards!
                popup.style.setProperty('--arrow-top', 'auto');
                popup.style.setProperty('--arrow-bottom', '100%');
                popup.style.setProperty('--arrow-color', 'transparent transparent #2f2f2f transparent');
                popup.style.setProperty('--arrow-border-color', 'transparent transparent #424242 transparent');
            } else {
                popup.style.setProperty('--arrow-top', '100%');
                popup.style.setProperty('--arrow-bottom', 'auto');
                popup.style.setProperty('--arrow-color', '#2f2f2f transparent transparent transparent');
                popup.style.setProperty('--arrow-border-color', '#424242 transparent transparent transparent');
            }
            
            // Keep on screen horizontally (rect.left is viewport relative)
            var absoluteLeft = rect.left + left;
            if (absoluteLeft < 10) {
                left = 10 - rect.left;
            } else if (absoluteLeft + popupRect.width > D.documentElement.clientWidth - 10) {
                left = D.documentElement.clientWidth - 10 - rect.left - popupRect.width;
            }
            
            // Calculate arrow left position relative to popup
            var arrowLeft = (rect.width / 2) - left;
            if (arrowLeft < 15) arrowLeft = 15;
            if (arrowLeft > popupRect.width - 15) arrowLeft = popupRect.width - 15;
            popup.style.setProperty('--arrow-left', arrowLeft + 'px');
            
            popup.style.top = top + 'px';
            popup.style.left = left + 'px';
            
            activePopup = popup;
        };

        P.__seamHideTooltip = function() {
            if (activePopup) {
                activePopup.style.display = 'none';
                activePopup = null;
            }
        };

        // Remove old listener if it exists to avoid dead references
        if (P.__seamClickEventHandler) {
            D.removeEventListener('click', P.__seamClickEventHandler);
        }
        if (P.__seamMouseOverHandler) {
            D.removeEventListener('mouseover', P.__seamMouseOverHandler);
        }
        if (P.__seamMouseOutHandler) {
            D.removeEventListener('mouseout', P.__seamMouseOutHandler);
        }

        // Define click handler
        P.__seamClickEventHandler = function(e) {
            // 1. Signal label click (only toggles highlight, does NOT show popup)
            var label = e.target.closest('div.seam-signals-list label');
            if (label) {
                e.preventDefault();
                P.__seamOnSignalLabelClick(label);
                return;
            }
            
            // 2. Ask Seam click
            var askBtn = e.target.closest('button[data-ask-seam]');
            if (askBtn) {
                e.preventDefault();
                P.__seamOnAskSeam(askBtn);
                return;
            }
            
            // 3. Got It click
            var dismissBtn = e.target.closest('button[data-dismiss-chip]');
            if (dismissBtn) {
                e.preventDefault();
                P.__seamOnDismiss(dismissBtn);
                return;
            }
        };

        // Define hover handlers
        P.__seamMouseOverHandler = function(e) {
            // Ignore mouseover events inside an active popup
            if (e.target.closest('.popup')) {
                if (hoverTimeout) clearTimeout(hoverTimeout);
                return;
            }

            var current = e.target.closest('.sig-text-highlight');
            while (current) {
                var groupId = current.getAttribute('data-group-id');
                if (groupId) {
                    // Only show if the toggle is checked (meaning highlights are visible!)
                    var toggle = D.getElementById('sig-toggle-' + groupId);
                    if (toggle && toggle.checked) {
                        if (hoverTimeout) clearTimeout(hoverTimeout);
                        P.__seamShowTooltip(current, groupId);
                        return;
                    }
                }
                current = current.parentElement ? current.parentElement.closest('.sig-text-highlight') : null;
            }
        };

        P.__seamMouseOutHandler = function(e) {
            if (!activePopup) return;
            
            var toElement = e.relatedTarget;
            if (toElement && (toElement.closest('.sig-text-highlight') || toElement.closest('.popup'))) {
                // Mouse moved inside the highlight or the popup, do not hide!
                if (hoverTimeout) clearTimeout(hoverTimeout);
                return;
            }
            
            if (hoverTimeout) clearTimeout(hoverTimeout);
            hoverTimeout = setTimeout(function() {
                P.__seamHideTooltip();
            }, 200);
        };

        // Bind all listeners
        D.addEventListener('click', P.__seamClickEventHandler);
        D.addEventListener('mouseover', P.__seamMouseOverHandler);
        D.addEventListener('mouseout', P.__seamMouseOutHandler);
    })();
    </script>
    """
    components.html(popup_js, height=0, width=0)
