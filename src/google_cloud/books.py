from .service import ServiceFactory


class BooksClient:
    def __init__(self, token_file, secrets_file, scopes):
        self.token_file = token_file
        self.secrets_file = secrets_file
        self.factory = ServiceFactory(self.token_file, self.secrets_file, scopes=scopes)

    def get_service(self, refresh=False):
        return self.factory.books_api_service(refresh=refresh)

    def search(self, q, print_type="BOOKS", start_index=0, max_results=10):
        service = self.get_service()
        return (
            service.volumes()
            .list(
                q=q,
                printType=print_type,
                startIndex=start_index,
                maxResults=max_results,
            )
            .execute()
        )
