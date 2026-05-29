import os
import json
import re
import urllib.parse
import streamlit as st
from dotenv import load_dotenv

# Load configuration from env.txt or .env
if os.path.exists("env.txt"):
    load_dotenv("env.txt")
else:
    load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_groq_client():
    """Initializes and returns the Groq client, raising a ValueError if key is missing."""
    if os.path.exists("env.txt"):
        load_dotenv("env.txt", override=True)
    else:
        load_dotenv(override=True)
        
    key = os.getenv("GROQ_API_KEY")
    if not key or not key.strip() or key.startswith("your-groq"):
        raise ValueError("GROQ_API_KEY is missing. Please set it in env.txt or your system environment variables.")
    
    from groq import Groq
    return Groq(api_key=key.strip())

SYSTEM_PROMPT = (
    "You are Seam, a transparent AI assistant. For every user message, respond with ONLY a "
    "valid JSON object — no markdown, no backticks, no preamble, nothing outside the JSON. "
    "The object has exactly two keys. Key one: response — your full helpful answer as a plain string. "
    "Key two: signals — an array of signal objects identifying specific parts of your response "
    "that fall into these categories: assumed (you filled a gap the user did not explicitly provide), "
    "uncertain (you are pattern-completing rather than drawing from reliable specific data), "
    "outdated (this information may have changed since your training), "
    "context_dependent (this is generally true but may not apply to the user's specific situation), "
    "conflicting (genuine disagreement exists and you picked one side), "
    "unverifiable (this is a prediction, opinion, or contested claim that cannot be verified), "
    "tradeoff (you made a consequential choice between constraints without being asked). "
    "Each signal object must have: signal_type, exact_text (copy the exact phrase from your response), "
    "explanation (one sentence). Maximum 4 signals. "
    "Flag a phrase only when it genuinely fits one of the above categories — for example: a date or statistic "
    "that may have changed, a claim where sources disagree, a prediction about the future, an assumption you "
    "made about the user's context, or a tradeoff you made silently. "
    "Do NOT flag phrases just because they are important. Do not flag something merely to reach a count. "
    "Quality over quantity — two precise signals beat four vague ones. If nothing warrants flagging, return signals as []."
)

def clean_json_text(text: str) -> str:
    """Extracts raw JSON content if the model wrapped it in markdown code blocks."""
    text = text.strip()
    # Strip markdown block wrappers like ```json ... ```
    text = re.sub(r"^```(?:json|xml)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    return text.strip()

def chat_completion(messages: list) -> dict:
    """Calls Groq API in JSON mode and returns parsed dictionary with response and signals."""
    client = get_groq_client()
    
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in messages:
        api_messages.append({"role": m["role"], "content": m["content"]})
        
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    
    try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=api_messages,
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=2048
            )
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate_limit" in error_str.lower() or "limit reached" in error_str.lower():
                fallback_model = "llama-3.1-8b-instant" if model_name != "llama-3.1-8b-instant" else "llama3-8b-8192"
                print(f"Seam LLM: Rate limit hit on {model_name}. Falling back to {fallback_model}...")
                response = client.chat.completions.create(
                    model=fallback_model,
                    messages=api_messages,
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=2048
                )
            else:
                raise e

        raw_text = clean_json_text(response.choices[0].message.content)
        parsed_data = json.loads(raw_text)
        
        if "response" not in parsed_data:
            parsed_data["response"] = raw_text
        if "signals" not in parsed_data:
            parsed_data["signals"] = []
            
        return parsed_data
    except json.JSONDecodeError as je:
        print(f"JSON parsing error: {je}")
        match = re.search(r'"response"\s*:\s*"((?:[^"\\]|\\.)*)"', raw_text)
        if match:
            try:
                extracted_text = match.group(1).encode().decode('unicode-escape')
                return {"response": extracted_text, "signals": []}
            except Exception:
                pass
        return {"response": raw_text, "signals": []}
    except Exception as e:
        raise e

def get_signal_style_rules(signals: list, message_index: int) -> str:
    """Generates the CSS style rules string for a message's signals, to be loaded globally in app.py."""
    if not signals:
        return ""
        
    class_map = {
        "assumed": "c-assumed",
        "uncertain": "c-uncertain",
        "outdated": "c-outdated",
        "context_dependent": "c-context",
        "conflicting": "c-conflict",
        "unverifiable": "c-unverifiable",
        "tradeoff": "c-tradeoff"
    }
    
    highlight_styles = {
        "assumed": "background-color: rgba(245, 158, 11, 0.25) !important; border-bottom: 2px solid #f59e0b !important; color: #fbbf24 !important;",
        "uncertain": "background-color: rgba(239, 68, 68, 0.25) !important; border-bottom: 2px solid #ef4444 !important; color: #f87171 !important;",
        "outdated": "background-color: rgba(249, 115, 22, 0.25) !important; border-bottom: 2px solid #f97316 !important; color: #fb923c !important;",
        "context_dependent": "background-color: rgba(59, 130, 246, 0.25) !important; border-bottom: 2px solid #3b82f6 !important; color: #60a5fa !important;",
        "conflicting": "background-color: rgba(16, 185, 129, 0.25) !important; border-bottom: 2px solid #10b981 !important; color: #34d399 !important;",
        "unverifiable": "background-color: rgba(139, 92, 246, 0.25) !important; border-bottom: 2px solid #8b5cf6 !important; color: #a78bfa !important;",
        "tradeoff": "background-color: rgba(236, 72, 153, 0.25) !important; border-bottom: 2px solid #ec4899 !important; color: #f472b6 !important;"
    }
    
    # Sort signals descending to align with search counts
    sorted_signals = sorted(signals, key=lambda x: len(x.get("exact_text", "")), reverse=True)
    signals_by_type = {k: [] for k in class_map}
    for sig in sorted_signals:
        exact_text = sig.get("exact_text", "")
        if not exact_text or not exact_text.strip():
            continue
        sig_type = sig.get("signal_type", "uncertain").lower()
        if sig_type not in class_map:
            sig_type = "uncertain"
        signals_by_type[sig_type].append(sig)
        
    style_rules = ""
    
    for sig_type, sig_list in signals_by_type.items():
        if not sig_list:
            continue
            
        group_id = f"msg_{message_index}_{sig_type}"
        style_rule = highlight_styles[sig_type]
        
        selectors = []
        for k in range(1, len(sig_list) + 1):
            sig_class_id = f"msg_{message_index}_{sig_type}_{k}"
            selectors.append(f'#sig-toggle-{group_id}:checked ~ .seam-message-body .sig-text-{sig_class_id}')
            
        combined_selectors = ", ".join(selectors)
        
        style_rules += f"""
        /* Highlight all text spans in this group when toggle checked */
        {combined_selectors} {{
            {style_rule}
            border-radius: 4px;
            padding: 0 4px;
            position: relative;
            cursor: help;
        }}
        
        /* Highlight active/checked chip label - overrides dismiss opacity */
        #sig-toggle-{group_id}:checked ~ .seam-signals-list label[for="sig-toggle-{group_id}"] {{
            opacity: 1.0 !important;
            filter: brightness(1.2) !important;
            border-color: #ffffff !important;
            box-shadow: 0 0 8px rgba(255, 255, 255, 0.2) !important;
        }}
        
        /* When the dismiss checkbox is checked, fade the chip label to 30% */
        #sig-dismiss-{group_id}:checked ~ .seam-signals-list label[for="sig-toggle-{group_id}"] {{
            opacity: 0.3 !important;
        }}
        """
        
    return style_rules

def parse_signals_seam(text: str, signals: list, signals_on: bool, message_index: int) -> str:
    """Parses text, wrapping exact substrings with CSS selectors and outputting chips at the bottom."""
    if not signals or not signals_on:
        return text.replace("\n", "<br>")

    class_map = {
        "assumed": "c-assumed",
        "uncertain": "c-uncertain",
        "outdated": "c-outdated",
        "context_dependent": "c-context",
        "conflicting": "c-conflict",
        "unverifiable": "c-unverifiable",
        "tradeoff": "c-tradeoff"
    }

    # Sort signals by length descending to prevent nesting collision issues
    sorted_signals = sorted(signals, key=lambda x: len(x.get("exact_text", "")), reverse=True)
    
    L = len(text)
    covered = [False] * L
    matches = []
    
    # Group non-empty signals by type
    signals_by_type = {k: [] for k in class_map}
    for sig in sorted_signals:
        exact_text = sig.get("exact_text", "")
        if not exact_text or not exact_text.strip():
            continue
        sig_type = sig.get("signal_type", "uncertain").lower()
        if sig_type not in class_map:
            sig_type = "uncertain"
        signals_by_type[sig_type].append(sig)
        
    # Match exact substrings using the alphanumeric-only coverage algorithm
    group_counters = {k: 0 for k in class_map}
    for sig in sorted_signals:
        exact_text = sig.get("exact_text", "")
        if not exact_text or not exact_text.strip():
            continue
        
        sig_type = sig.get("signal_type", "uncertain").lower()
        if sig_type not in class_map:
            sig_type = "uncertain"
            
        clean_exact = exact_text.strip().replace("\\'", "'").replace('\\"', '"')
        norm_exact = "".join(c.lower() for c in clean_exact if c.isalnum())
        if not norm_exact:
            continue
            
        # Collect uncovered alphanumeric characters
        norm_text_chars = []
        for idx in range(L):
            if not covered[idx] and text[idx].isalnum():
                norm_text_chars.append((text[idx].lower(), idx))
                
        norm_text = "".join(item[0] for item in norm_text_chars)
        
        # Find all occurrences of norm_exact in norm_text to find a contiguous uncovered match
        start_search = 0
        while True:
            match_idx = norm_text.find(norm_exact, start_search)
            if match_idx == -1:
                break
                
            start_orig = norm_text_chars[match_idx][1]
            end_orig = norm_text_chars[match_idx + len(norm_exact) - 1][1] + 1
            
            if not any(covered[i] for i in range(start_orig, end_orig)):
                # Mark as covered
                for i in range(start_orig, end_orig):
                    covered[i] = True
                
                group_counters[sig_type] += 1
                k = group_counters[sig_type]
                sig_id = f"msg_{message_index}_{sig_type}_{k}"
                
                matches.append((start_orig, end_orig, sig_id, sig))
                break
                
            start_search = match_idx + 1
            
    # Emoji mappings for inline popups
    emoji_map = {
        "assumed": "🤔",
        "uncertain": "🤷",
        "outdated": "📅",
        "context_dependent": "💡",
        "conflicting": "⚔️",
        "unverifiable": "🔍",
        "tradeoff": "⚖️"
    }

    display_name_map = {
        "assumed": "I Assumed",
        "uncertain": "I'm Not Certain",
        "outdated": "My Context May Be Outdated",
        "context_dependent": "This Depends on Your Context",
        "conflicting": "There's Conflicting Information",
        "unverifiable": "This Can't Be Verified",
        "tradeoff": "I Made a Tradeoff"
    }

    import html as _html

    # Sort matches by start index descending to insert spans right-to-left
    matches.sort(key=lambda x: x[0], reverse=True)
    temp_text = text
    for start, end, sig_id, sig in matches:
        sig_type = sig.get("signal_type", "uncertain").lower()
        if sig_type not in class_map:
            sig_type = "uncertain"
        exact_text = sig.get("exact_text", "")
        explanation = sig.get("explanation", "")
        
        # Build query
        if sig_type == "assumed":
            query = f"You assumed '{exact_text}'—what other possibilities exist?"
        elif sig_type == "uncertain":
            query = f"What specific evidence or data sources support the claim: '{exact_text}'?"
        elif sig_type == "outdated":
            query = f"What is the most recent status of '{exact_text}'?"
        elif sig_type == "context_dependent":
            query = f"How does '{exact_text}' change depending on my industry or context?"
        elif sig_type == "conflicting":
            query = f"What are the conflicting viewpoints surrounding '{exact_text}'?"
        elif sig_type == "unverifiable":
            query = f"Why is '{exact_text}' considered unverifiable or speculative?"
        elif sig_type == "tradeoff":
            query = f"What were the alternative choices to the tradeoff you made in '{exact_text}'?"
        else:
            query = f"Can you elaborate on your comment about '{exact_text}'?"
            
        data_query = _html.escape(query, quote=True)
        emoji = emoji_map.get(sig_type, "🤷")
        display_name = display_name_map.get(sig_type, "I'm Not Certain")
        group_id = f"msg_{message_index}_{sig_type}"
        
        # Inline popup nested inside the highlight span
        popup_html = (
            f'<span class="popup" onclick="event.stopPropagation()">'
            f'<span style="font-size:13px; line-height:1.5; color:#ececec; display:block;">'
            f'{emoji} <strong>{display_name}</strong>: {explanation}'
            f'</span>'
            f'<span class="pact" style="margin-top:8px; display:flex; gap:8px; justify-content:flex-end;">'
            f'<button type="button" class="pbtn" data-dismiss-chip="chip-wrap-{group_id}" data-close-toggle="sig-toggle-{group_id}">Got it</button>'
            f'<button type="button" class="pbtn green" data-ask-seam="{data_query}" data-sig-id="sig-toggle-{group_id}">Ask Seam</button>'
            f'</span>'
            f'</span>'
        )
        
        temp_text = temp_text[:start] + f'<span class="sig-text-highlight sig-text-{sig_id}" data-group-id="{group_id}">{temp_text[start:end]}{popup_html}</span>' + temp_text[end:]
        
    temp_text = temp_text.replace("\n", "<br>")
        
    checkboxes_html = ""
    chips_html = ""
    
    for sig_type, sig_list in signals_by_type.items():
        if not sig_list:
            continue
            
        sig_class = class_map[sig_type]
        display_name = display_name_map[sig_type]
        group_id = f"msg_{message_index}_{sig_type}"
        
        checkboxes_html += f'<input type="checkbox" id="sig-toggle-{group_id}" class="sig-selector-check" style="display:none;">'
        checkboxes_html += f'<input type="checkbox" id="sig-dismiss-{group_id}" class="sig-dismiss-check" style="display:none;">'
        
        chips_html += (
            f'<span class="chip-container" id="chip-wrap-{group_id}">'
            f'<label for="sig-toggle-{group_id}" class="chip {sig_class}">{display_name}</label>'
            f'</span>'
        )
        
    final_html = (
        f'<div class="seam-interactive-message">'
        f'{checkboxes_html}'
        f'<div class="seam-message-body">{temp_text}</div>'
        f'<div class="seam-signals-list" style="margin-top:28px; display:flex; flex-wrap:wrap; gap:6px;">{chips_html}</div>'
        f'</div>'
    )
    
    return final_html
