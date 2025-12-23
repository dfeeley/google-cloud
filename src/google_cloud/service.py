from dataclasses import dataclass, field
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@dataclass
class ServiceFactory:
    token_file: str
    secrets_file: str
    scopes: List = field(default_factory=list)

    def __post_init__(self):
        if not self.scopes:
            self.scopes = DEFAULT_SCOPES

    def _get_service(self, name, version, attr=None, refresh=False):
        service = _get_generic_api_service(
            name=name,
            version=version,
            scopes=self.scopes,
            token_file=self.token_file,
            secrets_file=self.secrets_file,
            refresh=refresh,
        )
        if attr:
            return getattr(service, attr)()
        return service

    def docs_api_service(self, refresh=False):
        return self._get_service("docs", "v1", attr="documents", refresh=refresh)

    def sheets_api_service(self, refresh=False):
        return self._get_service("sheets", "v4", attr="spreadsheets", refresh=refresh)

    def drive_api_service(self, refresh=False):
        return self._get_service("drive", "v3", refresh=refresh)

    def tasks_api_service(self, refresh=False):
        return self._get_service("tasks", "v1", refresh=refresh)

    def calendar_api_service(self, refresh=False):
        return self._get_service("calendar", "v3", refresh=refresh)

    def books_api_service(self, refresh=False):
        return self._get_service("books", "v1", refresh=refresh)

    def people_api_service(self, refresh=False):
        return self._get_service("people", "v1", refresh=refresh)


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
