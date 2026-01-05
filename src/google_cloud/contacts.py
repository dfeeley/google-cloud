import json

from .service import ServiceFactory


class ContactsClient:
    def __init__(self, token_file, secrets_file, scopes=None):
        self.token_file = token_file
        self.secrets_file = secrets_file
        self.factory = ServiceFactory(self.token_file, self.secrets_file, scopes=scopes)

    def get_service(self, refresh=False):
        return self.factory.people_api_service(refresh=refresh)

    def list(
        self,
        page_size=1000,
        include_memberships=False,
        include_phone_numbers=False,
        debug=False,
    ):
        service = self.get_service()
        contacts = []
        next_page_token = None

        fields = "names,emailAddresses"
        if include_memberships:
            fields += ",memberships"
        if include_phone_numbers:
            fields += ",phoneNumbers"

        while True:
            list_kwargs = dict(
                resourceName="people/me",
                pageSize=page_size,
                personFields=fields,
            )
            if next_page_token:
                list_kwargs["pageToken"] = next_page_token

            results = service.people().connections().list(**list_kwargs).execute()

            contacts.extend(results.get("connections", []))
            if (next_page_token := results.get("nextPageToken")) is None:
                break

        if debug:
            with open("/tmp/contacts.json", "w") as f:
                json.dump(contacts, f, indent=4)
        return contacts

    def groups(self, debug=False):
        service = self.get_service()
        groups = service.contactGroups().list().execute()["contactGroups"]
        if debug:
            with open("/tmp/groups.json", "w") as f:
                json.dump(groups, f, indent=4)
        return groups

    def batch_create(self, batch_request):
        return (
            self.get_service()
            .people()
            .batchCreateContacts(body=batch_request)
            .execute()
        )

    def delete_contact(self, contact):
        return (
            self.get_service()
            .people()
            .deleteContact(resourceName=contact["resourceName"])
            .execute()
        )
