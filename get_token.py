import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# The exact, correct YouTube scopes your bot needs.
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly'
]

def generate_token():
    creds = None

    # Check if an old token file exists and remove it if it contains bad scopes
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception:
            os.remove('token.json')
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("Initiating authentication flow...")

            if not os.path.exists('client_secrets.json'):
                print("Error: 'client_secrets.json' not found in the current directory.")
                return

            # Forces the script to pull fresh scopes directly from this file
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)

            creds = flow.run_local_server(
                port=8080,
                prompt='consent',
                open_browser=False
            )

        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
            print("\nSuccess! 'token.json' has been generated and saved successfully.")


if __name__ == '__main__':
    generate_token()
