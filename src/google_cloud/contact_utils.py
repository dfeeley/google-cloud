def find_group_by_name(groups, name):
    search_name = name.lower()
    for group in groups:
        if group["name"].lower() == search_name:
            return group


def filter_contacts_by_group_name(group_name, contacts, groups):
    ret = []
    group = find_group_by_name(groups, group_name)
    if group is None:
        return ret
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
        for email_address in contact.get("email_addresses", []):
            ret[email_address["value"].lower()] = contact
    return ret
