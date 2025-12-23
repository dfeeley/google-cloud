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
        self, page_size=1000, include_memberships=False, include_phone_numbers=False
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

        with open("/tmp/contacts.json", "w") as f:
            json.dump(contacts, f, indent=4)
        return contacts

    def group_contacts(self, group_name="family"):
        service = self.get_service()
        groups = service.contactGroups().list().execute()
        group_id = None

        # Find 'Family' group
        for group in groups.get("contactGroups", []):
            if group["name"] == group_name.lower():
                group_id = group["resourceName"]
                break

        if not group_id:
            print(f"{group_name} group not found")
            return []

        # Get contacts in group
        results = (
            service.people()
            .connections()
            .list(
                resourceName="people/me",
                pageSize=300,
                personFields="names,emailAddresses,phoneNumbers,memberships",
            )
            .execute()
        )

        family_contacts = []
        for contact in results.get("connections", []):
            memberships = contact.get("memberships", [])
            for membership in memberships:
                if (
                    membership.get("contactGroupMembership", {}).get(
                        "contactGroupResourceName"
                    )
                    == group_id
                ):
                    family_contacts.append(contact)
                    break

        for person in family_contacts:
            # Extract name
            names = person.get("names", [])
            name = names[0]["displayName"] if names else "No name"

            # Extract emails
            emails = person.get("emailAddresses", [])
            email_list = [email["value"] for email in emails]

            # Extract phone numbers
            phones = person.get("phoneNumbers", [])
            phone_list = [phone["value"] for phone in phones]

            print(f"Name: {name}")
            if email_list:
                print(f"Email: {', '.join(email_list)}")
            if phone_list:
                print(f"Phone: {', '.join(phone_list)}")
            print("-" * 60)
