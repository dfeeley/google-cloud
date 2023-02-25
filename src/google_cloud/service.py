from dataclasses import dataclass

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google sheets API documentation is: https://developers.google.com/sheets/api


@dataclass
class ServiceFactory:
    token_file: str
    secrets_file: str

    def docs_api_service(self, refresh=False):
        return _get_generic_api_service(
            name="docs",
            version="v1",
            scopes=["https://www.googleapis.com/auth/documents.readonly"],
            token_file=self.token_file,
            secrets_file=self.secrets_file,
            refresh=refresh,
        ).documents()

    def sheets_api_service(self, refresh=False):
        return _get_generic_api_service(
            name="sheets",
            version="v4",
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
            token_file=self.token_file,
            secrets_file=self.secrets_file,
            refresh=refresh,
        ).spreadsheets()

    def drive_api_service(self, refresh=False):
        return _get_generic_api_service(
            name="drive",
            version="v3",
            scopes=["https://www.googleapis.com/auth/drive"],
            token_file=self.token_file,
            secrets_file=self.secrets_file,
            refresh=refresh,
        )


def _get_generic_api_service(
    name, version, scopes, token_file, secrets_file, refresh=False
):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if token_file.exists() and refresh is False:
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    try:
        return build(name, version, credentials=creds, cache_discovery=False)
    except HttpError as err:
        print(err)