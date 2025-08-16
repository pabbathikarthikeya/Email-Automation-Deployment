import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()
USERNAME = os.getenv('EMAIL_USER')
PASSWORD = os.getenv('EMAIL_PASS')
IMAP_SERVER = os.getenv('IMAP_SERVER')

def get_email_body(msg):
    """Parses the email message to find the plain text body."""
    if msg.is_multipart():
        # Iterate over email parts
        for part in msg.walk():
            # Extract content type
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if "text/plain" in content_type and "attachment" not in content_disposition:
                # Decode the body and return it
                try:
                    body = part.get_payload(decode=True).decode()
                    return body
                except:
                    return None
    else:
        # Not a multipart message, just get the payload
        try:
            body = msg.get_payload(decode=True).decode()
            return body
        except:
            return None


def fetch_unread_emails():
    """Connects to the IMAP server and fetches unread emails."""
    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        # Login
        mail.login(USERNAME, PASSWORD)
        print("✅ Login successful!")

        # Select the inbox
        mail.select("inbox")

        # Search for all unread emails
        status, messages = mail.search(None, "(UNSEEN)")

        if status == "OK":
            email_ids = messages[0].split()
            if not email_ids:
                print("No new unread emails.")
                return

            print(f"Found {len(email_ids)} unread emails.")

            # Fetch and process each email
            for e_id in email_ids:
                _, msg_data = mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])

                        # Decode email subject
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        
                        # Get sender
                        sender = msg.get("From")
                        
                        # Get the email body
                        body = get_email_body(msg)

                        print("="*30)
                        print(f"From: {sender}")
                        print(f"Subject: {subject}")
                        print("Body:")
                        print(body)
                        print("="*30)

        # Logout
        mail.logout()

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    fetch_unread_emails()