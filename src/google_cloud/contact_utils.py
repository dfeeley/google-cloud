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
    batch_requests = [{"contactPerson": obj} for obj in objs]
    if batch_requests:
        payload = {"contacts": batch_requests, "read_mask": "names"}
        return client.batch_create_contacts(payload)
