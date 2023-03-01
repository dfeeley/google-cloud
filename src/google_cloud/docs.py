from dataclasses import dataclass

from .service import ServiceFactory


@dataclass
class GoogleDocsDocument:
    id: str
    title: str

    @classmethod
    def for_id(cls, id, token_file, secrets_file, scopes=None):
        service = ServiceFactory(
            token_file, secrets_file, scopes=scopes
        ).docs_api_service()
        response = service.get(documentId=id).execute()
        title = response.get("title")
        return cls(id, title)
