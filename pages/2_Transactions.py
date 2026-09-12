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

st.subheader("🎙️ Voice Transaction Entry")
st.caption('Misal: "Ahmed ne 5000 ka saman liya aur 2000 de diye." Ya: "Ahmed ne purane udhaar ke 1500 rupay diye."')
st.caption("Urdu ya English mein bolein. Convert karne par recording Groq ko bheji jayegi.")
language = st.selectbox("Recording language", ["Auto", "Urdu", "English"], key="tv_language")
recording = st.audio_input("Transaction record karein", key="tv_recording")
if st.button("🎙️ Voice ko Text Mein Badlein", disabled=recording is None):
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
if st.button("Understand Transaction"):
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
