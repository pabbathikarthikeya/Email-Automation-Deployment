import smtplib
import imaplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# --- NEW AI IMPORTS ---
import spacy
from spacytextblob.spacytextblob import SpacyTextBlob

# --- Load AI Model ---
print("Loading NLP model...")
nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("spacytextblob")
print("NLP model loaded.")

# Load credentials from .env file
load_dotenv()
USERNAME = os.getenv('EMAIL_USER')
PASSWORD = os.getenv('EMAIL_PASS')
IMAP_SERVER = os.getenv('IMAP_SERVER')
SMTP_SERVER = os.getenv('SMTP_SERVER')

RESPONSE_TEMPLATES = {
    #Email template for Meeting request
    "meeting_request": """
    Hello {name},

    Thank you for reaching out to schedule a meeting. I am available to connect.

    Please let me know what time works best for you.

    Best,
    Your AI Assistant
    """,
    #Email template for Support Enquiry
    "support_inquiry": """
    Hello {name},

    Thank you for your message. We have received your support request.

    Our team will review it and get back to you within 24 hours.

    Best,
    Your AI Assistant
    """,
    #Email template for Invoice Question
    "invoice_question": """
    Hello {name},

    Thank you for your email regarding an invoice.

    We have received your query and will have our billing department look into it right away.

    Best,
    Your AI Assistant
    """,
    #Email template for Negative feedback
    "negative_feedback": """
    Hello {name},

    We are very sorry to hear you've had a negative experience. 
    
    Your feedback is important, and we are looking into the issue you raised immediately. A member of our team will reach out to you personally to resolve this.

    Sincerely,
    Your AI Assistant
    """
}

# --- REWRITTEN AI-ASSISTED ANALYSIS FUNCTION ---
def analyze_email_with_ai(subject, body):
    """
    Analyzes email using spaCy for sentiment and entities, 
    then falls back to keyword matching.
    """
    text_to_analyze = subject + " " + (body if body else "")
    doc = nlp(text_to_analyze)
    
    # 1. AI-Based Sentiment Analysis
    sentiment = doc._.blob.polarity
    # Polarity is between -1 (negative) and 1 (positive)
    if sentiment < -0.2: # If sentiment is clearly negative
        print(f"AI Insight: Detected negative sentiment ({sentiment:.2f}).")
        return "negative_feedback"

    # 2. AI-Based Entity Recognition (Example)
    # Checks if the email talks about dates or money, which can imply intent
    has_date = any(ent.label_ == "DATE" for ent in doc.ents)
    has_money = any(ent.label_ == "MONEY" for ent in doc.ents)

    if has_date and any(k in text_to_analyze.lower() for k in ["meet", "call", "schedule"]):
        print("AI Insight: Detected DATE entity, likely a meeting request.")
        return "meeting_request"
    
    if has_money and any(k in text_to_analyze.lower() for k in ["invoice", "payment", "bill"]):
        print("AI Insight: Detected MONEY entity, likely an invoice question.")
        return "invoice_question"

    # 3. Fallback to Simple Rule-Based Matching
    print("AI analysis inconclusive, falling back to keyword matching...")
    subject_lower = subject.lower()
    body_lower = body.lower() if body else ""
    if any(k in subject_lower or k in body_lower for k in ["schedule", "meeting", "call"]):
        return "meeting_request"
    if any(k in subject_lower or k in body_lower for k in ["help", "support", "issue", "problem"]):
        return "support_inquiry"
    if any(k in subject_lower or k in body_lower for k in ["invoice", "billing", "payment"]):
        return "invoice_question"
        
    return None

def send_reply(to_email, subject, intent, original_sender_name):
    msg = MIMEMultipart()
    msg['From'] = USERNAME
    msg['To'] = to_email
    msg['Subject'] = f"Re: {subject}"
    template = RESPONSE_TEMPLATES.get(intent, "Thank you for your email. We will get back to you shortly.")
    body = template.format(name=original_sender_name.split()[0] if original_sender_name else "there")
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, 465) as smtp_server:
            smtp_server.login(USERNAME, PASSWORD)
            smtp_server.send_message(msg)
            print(f"Reply successfully sent to {to_email}")
    except Exception as e:
        print(f"Failed to send reply: {e}")

def get_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if "text/plain" in part.get_content_type() and "attachment" not in str(part.get("Content-Disposition")):
                return part.get_payload(decode=True).decode(errors='ignore')
    else:
        return msg.get_payload(decode=True).decode(errors='ignore')

def process_emails():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(USERNAME, PASSWORD)
        mail.select("inbox")
        status, messages = mail.search(None, '(UNSEEN)')
        if status != "OK" or not messages[0]:
            print("No new unread emails.")
            mail.logout()
            return
        
        email_ids = messages[0].split()
        for e_id in email_ids:
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes): subject = subject.decode()
                    sender_name, sender_email = email.utils.parseaddr(msg.get("From"))
                    body = get_email_body(msg)
                    
                    print("="*30)
                    print(f"Processing email from: {sender_email}")
                    print(f"Subject: {subject}")

                    intent = analyze_email_with_ai(subject, body)
                    if intent:
                        print(f"Intent Detected: {intent}. Sending reply...")
                        send_reply(sender_email, subject, intent, sender_name)
                    else:
                        print("No matching rule found. Ignoring.")
                    print("="*30)
        mail.logout()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    process_emails()