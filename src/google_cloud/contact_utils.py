def find_group_by_name(groups, name):
    search_name = name.lower()
    for group in groups:
        if group["name"].lower() == search_name:
            return group


def filter_contacts_by_group(contacts, group):
    ret = []
    for contact in contacts:
        memberships = contact.get("memberships", [])
        for membership in memberships:
            if (
                membership.get("contactGroupMembership", {}).get(
                    "contactGroupResourceName"
                )
                == group["resourceName"]
            ):
                ret.append(contact)
                break
    return ret


def contacts_as_email_lookup(contacts):
    ret = {}
    for contact in contacts:
        for email_address in contact.get("emailAddresses", []):
            ret[email_address["value"].lower()] = contact
    return ret


def ensure_groups_exist(client, group_names):
    groups = client.groups()
    for name in group_names:
        group = find_group_by_name(groups, name)
        if group is None:
            client.create_group(name)


def ensure_group_exists(client, group_name):
    groups = client.groups()
    group = find_group_by_name(groups, group_name)
    if group is None:
        client.create_group(group_name)


def create_contacts(client, objs):
    """Objs expected to be a list of dataclass type objects with fields:
    given_name: mandatory
    family_name: mandatory
    email -- or -- email_addresses (both optional)
    phone: optional
    """

    def build_contact_payload(obj):
        ret = {"names": {"givenName": obj.given_name, "familyName": obj.family_name}}
        if hasattr(obj, "email"):
            if obj.email:
                ret["emailAddresses"] = [{"type": "work", "value": obj.email}]
        elif hasattr(obj, "email_addresses"):
            if obj.email_addresses:
                ret["emailAddresses"] = [
                    {"type": "work", "value": ea} for ea in obj.email_addresses
                ]
        if hasattr(obj, "phone"):
            if obj.phone:
                ret["phoneNumbers"] = {"type": "mobile", "value": obj.phone}
        return ret

    batch_requests = []

    for obj in objs:
        request_body = {"contactPerson": build_contact_payload(obj)}
        batch_requests.append(request_body)

    if batch_requests:
        batch_request = {"contacts": batch_requests, "read_mask": "names"}
        return client.batch_create_contacts(batch_request)
