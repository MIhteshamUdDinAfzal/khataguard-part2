import math
import os
import openai
import streamlit as st
from backend.core import (
    create_customer, find_customer_by_name, list_customers,
    record_sale, record_payment,
)
from backend.ai.parser import parse_transaction

st.set_page_config(page_title="Transactions", page_icon="💰", layout="wide")
st.title("💰 Transactions")
st.write("Add a sale or payment using voice, Urdu, Roman Urdu, or English.")

def setting(name, default=""):
    try:
        return st.secrets.get(name) or os.getenv(name) or default
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return os.getenv(name) or default

def voice_client():
    key = setting("GROQ_API_KEY")
    if not key:
        raise ValueError("Streamlit Settings > Secrets mein GROQ_API_KEY add karein.")
    return openai.OpenAI(
        api_key=key, base_url="https://api.groq.com/openai/v1",
        timeout=45, max_retries=1,
    )

def transcribe_transaction(audio_bytes, language):
    if not audio_bytes or len(audio_bytes) <= 44:
        raise ValueError("Recording khaali hai. Dobara record karein.")
    if len(audio_bytes) > 24_000_000:
        raise ValueError("Recording bohat lambi hai. Chhoti recording karein (24 MB se kam).")
    options = {} if language == "Auto" else {"language": {"Urdu": "ur", "English": "en"}[language]}
    with voice_client() as client:
        response = client.audio.transcriptions.create(
            model=setting("GROQ_SPEECH_MODEL", "whisper-large-v3-turbo"),
            file=("transaction.wav", audio_bytes, "audio/wav"),
            response_format="json", temperature=0, **options,
        )
    text = response.text.strip()
    if not text:
        raise ValueError("Awaaz samajh nahi aayi. Dobara record karein.")
    return text

def show_voice_error(error):
    if isinstance(error, ValueError):
        st.warning(str(error))
    elif isinstance(error, openai.AuthenticationError):
        st.error("Groq API key invalid hai. Secrets mein GROQ_API_KEY check karein.")
    elif isinstance(error, openai.RateLimitError):
        st.error("Groq limit reached. Thori dair baad try karein; manual entry available hai.")
    elif isinstance(error, (openai.APIConnectionError, openai.APITimeoutError)):
        st.error("Groq se connection nahi hua. Dobara try karein ya manual details bharein.")
    else:
        st.error("Voice processing complete nahi hui. Groq model/settings check karein ya manual entry use karein.")

def clear_draft():
    for key in ("tv_result", "tv_source", "tv_sale", "tv_paid", "tv_customer", "tv_new_name"):
        st.session_state.pop(key, None)


def validate_result(result):
    if not isinstance(result, dict) or type(result.get("needs_clarification")) is not bool:
        raise ValueError("AI response invalid hai. Text edit karke dobara try karein.")
    if result["needs_clarification"]:
        question = result.get("question")
        raise ValueError(question if isinstance(question, str) and question.strip() else "Transaction ki details clear karein.")
    customer = result.get("customer")
    if not isinstance(customer, str) or not customer.strip():
        raise ValueError("Customer ka naam batayein.")
    amounts = []
    for field in ("sale", "paid"):
        raw = result.get(field)
        if isinstance(raw, bool) or raw is None:
            raise ValueError("Sale/payment amount clear nahi hai.")
        try:
            amount = float(raw)
        except (ValueError, TypeError):
            raise ValueError("Sale/payment amount valid number nahi hai.") from None
        if not math.isfinite(amount) or amount < 0:
            raise ValueError("Amount finite aur zero ya positive hona chahiye.")
        amounts.append(amount)
    sale, paid = amounts
    if sale == 0 and paid == 0:
        raise ValueError("Sale ya payment amount batayein.")
    if sale > 0 and paid > sale:
        raise ValueError("Paid amount new sale se zyada hai. New sale aur purane balance ki payment alag enter karein.")
    return {"customer": customer.strip(), "sale": sale, "paid": paid}


# Apply pending state before any corresponding widgets are instantiated.
if st.session_state.pop("tv_reset_after_save", False):
    clear_draft()
    st.session_state["tv_text"] = ""
if "tv_pending_customer" in st.session_state:
    st.session_state["tv_customer"] = st.session_state.pop("tv_pending_customer")

if message := st.session_state.pop("tv_saved_message", None):
    st.success(message)

def voice_panel(title, subtitle):
    """Render the shared voice design; the native recorder below stays interactive."""
    st.markdown('''
<style>
.kg-voice-panel {border:1px solid #dce9e8;border-radius:18px;padding:24px;
 background:linear-gradient(145deg,#ffffff,#f4fbfa);margin:12px 0 18px;}
.kg-voice-heading {display:flex;align-items:center;gap:16px;}
.kg-voice-badge {display:flex;align-items:center;justify-content:center;flex-shrink:0;
 width:58px;height:58px;border-radius:16px;background:#e4f6f4;color:#087f83;}
.kg-voice-heading h3 {margin:0!important;padding:0!important;color:#14263f;font-size:1.5rem;}
.kg-voice-heading p {margin:6px 0 0;color:#52657a;font-size:.95rem;}
.kg-voice-art {display:flex;align-items:center;justify-content:center;gap:28px;margin:32px 0 24px;}
.kg-voice-orb {width:92px;height:92px;display:flex;align-items:center;justify-content:center;
 border-radius:50%;background:#0b8589;color:white;box-shadow:0 0 0 10px #dff2f1,0 0 0 20px #eef8f7;}
.kg-voice-wave {display:flex;align-items:center;gap:5px;height:48px;}
.kg-voice-wave i {display:block;width:5px;border-radius:8px;background:#badedd;}
.kg-voice-hint {text-align:center;color:#52657a;font-size:.9rem;margin:0;}
.st-key-cv_convert button,.st-key-tv_convert button {background:#0b8589!important;
 color:white!important;border:1px solid #0b8589!important;border-radius:10px!important;min-height:46px;}
.st-key-cv_convert button:hover,.st-key-tv_convert button:hover {background:#076a6e!important;border-color:#076a6e!important;}
.st-key-cv_convert button:disabled,.st-key-tv_convert button:disabled {background:#e5efef!important;
 color:#627e80!important;border-color:#d3e2e2!important;}
.st-key-cv_convert button:focus-visible,.st-key-tv_convert button:focus-visible {outline:3px solid #84d3d0;outline-offset:3px;}
@media(max-width:480px) {.kg-voice-panel{padding:18px}.kg-voice-heading h3{font-size:1.2rem}
 .kg-voice-wave{gap:3px}.kg-voice-wave i{width:3px}.kg-voice-art{gap:25px}}
</style>
''', unsafe_allow_html=True)
    mic = '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8"/></svg>'
    waves = '<span class="kg-voice-wave" aria-hidden="true">' + ''.join(
        f'<i style="height:{height}px"></i>' for height in [8,18,30,44,26,16,24,36,22,12]
    ) + '</span>'
    # The title and subtitle are fixed developer strings, never customer input.
    st.markdown(
        f'<section class="kg-voice-panel"><div class="kg-voice-heading">'
        f'<span class="kg-voice-badge">{mic}</span><div><h3>{title}</h3><p>{subtitle}</p></div></div>'
        f'<div class="kg-voice-art" aria-hidden="true">{waves}<span class="kg-voice-orb">'
        f'{mic.replace("32", "48")}</span>{waves}</div>'
        '<p class="kg-voice-hint">Use the microphone control below to start and stop recording.</p></section>',
        unsafe_allow_html=True,
    )


voice_panel("Voice Transaction", "Record a sale or payment in Urdu or English.")
st.caption('Misal: "Ahmed ne 5000 ka saman liya aur 2000 de diye." Ya: "Ahmed ne purane udhaar ke 1500 rupay diye."')
st.caption("Urdu ya English mein bolein. Convert karne par recording Groq ko bheji jayegi.")
language = st.selectbox("Recording language", ["Auto", "Urdu", "English"], key="tv_language")
recording = st.audio_input("Record transaction", key="tv_recording")
if st.button("Convert to Text", icon=":material/mic:", key="tv_convert", use_container_width=True, disabled=recording is None):
    # A new conversion must never leave an earlier transaction available to save.
    clear_draft()
    try:
        with st.spinner("Awaaz ko text mein badal rahe hain..."):
            st.session_state["tv_text"] = transcribe_transaction(recording.getvalue(), language)
    except Exception as error:
        show_voice_error(error)

transaction_text = st.text_area(
    "Enter transaction — voice ka text yahan edit kar sakte hain",
    placeholder="Ahmed ne 5000 ka saman liya aur 2000 de diye.",
    height=120, key="tv_text", on_change=clear_draft,
)
if st.button("Understand Transaction", icon=":material/description:", use_container_width=True):
    clear_draft()
    try:
        if not transaction_text.strip():
            raise ValueError("Pehle voice convert karein ya transaction likhein.")
        key = setting("GROQ_API_KEY")
        if not key:
            raise ValueError("Streamlit Settings > Secrets mein GROQ_API_KEY add karein.")
        with st.spinner("Transaction samajh rahe hain..."):
            result = validate_result(parse_transaction(
                transaction_text, api_key=key,
                model=setting("GROQ_MODEL", "openai/gpt-oss-20b"),
            ))
        st.session_state["tv_result"] = result
        st.session_state["tv_source"] = transaction_text
        st.session_state["tv_sale"] = result["sale"]
        st.session_state["tv_paid"] = result["paid"]
        st.session_state["tv_new_name"] = result["customer"]
        try:
            st.session_state["tv_customer"] = find_customer_by_name(result["customer"])["id"]
        except ValueError:
            st.session_state["tv_customer"] = None
    except Exception as error:
        show_voice_error(error)

if "tv_result" in st.session_state and st.session_state.get("tv_source") == transaction_text:
    result = st.session_state["tv_result"]
    st.subheader("Review & Save Transaction")
    st.write(f"Recognized customer: {result['customer']}")
    st.caption("Sahi customer select karein aur amounts check/edit karein. Sirf Save Transaction par entry save hogi.")
    try:
        customers = list_customers()
        labels = {row["id"]: f"{row['name']} — {row['phone'] or 'No phone'} (ID: {row['id']})" for row in customers}
        if st.session_state.get("tv_customer") not in labels:
            st.session_state["tv_customer"] = None
        customer_id = st.selectbox(
            "Customer account", [None] + list(labels),
            format_func=lambda value: "Select existing customer" if value is None else labels[value],
            key="tv_customer",
        )
        if customer_id is None:
            st.info("Existing customer select karein. Naya customer ho to neeche create karein.")
            new_name = st.text_input("New customer name", key="tv_new_name")
            if st.button("➕ Create Customer"):
                try:
                    # Avoid adding an exact duplicate; duplicate-name ambiguity must be resolved by ID.
                    try:
                        existing = find_customer_by_name(new_name)
                    except ValueError as error:
                        if str(error) != "Customer not found.":
                            raise
                        new_id = create_customer(name=new_name)
                    else:
                        new_id = existing["id"]
                    # Set selection before widget creation on the next run.
                    st.session_state["tv_pending_customer"] = new_id
                    st.rerun()
                except Exception as error:
                    st.error(f"Customer create nahi hua: {error}")
        left, right = st.columns(2)
        with left:
            sale = st.number_input("Sale (Rs.)", min_value=0.0, step=100.0, key="tv_sale")
        with right:
            paid = st.number_input("Paid / Received (Rs.)", min_value=0.0, step=100.0, key="tv_paid")
        st.metric("Is entry se balance mein tabdeeli", f"Rs. {sale - paid:,.2f}")
        st.caption("Positive amount udhaar barhata hai; negative amount purana udhaar kam karta hai.")
        if st.button("💾 Save Transaction", key="save_transaction", disabled=customer_id is None):
            try:
                checked = validate_result({"customer": result["customer"], "sale": sale, "paid": paid, "needs_clarification": False})
                if checked["sale"] > 0:
                    saved = record_sale(customer_id=customer_id, sale_amount=sale, paid_amount=paid, description=transaction_text)
                else:
                    saved = record_payment(customer_id=customer_id, amount=paid, description=transaction_text)
                st.session_state["tv_saved_message"] = (
                    f"Transaction saved: {saved['customer_name']} | "
                    f"Outstanding balance: Rs. {saved['outstanding']:,.2f}"
                )
                st.session_state["tv_reset_after_save"] = True
                st.rerun()
            except Exception as error:
                st.error(f"Transaction save nahi hua: {error}")
    except Exception as error:
        st.error(f"Customers load nahi hue: {error}")
