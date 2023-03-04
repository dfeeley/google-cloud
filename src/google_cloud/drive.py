from dataclasses import dataclass

from googleapiclient.http import MediaFileUpload

from .service import ServiceFactory

VALID_PERMISSION_TYPES = ("user", "group", "domain", "anyone")
VALID_PERMISSION_ROLES = (
    "owner",
    "organizer",
    "fileOrganizer",
    "writer",
    "commenter",
    "reader",
)


def mimetype_for_path(path):
    ext = path.suffix.replace(".", "").lower()
    if ext in ("jpg", "jpeg"):
        return "image/jpeg"
    elif ext == "png":
        return "image/png"
    else:
        raise ValueError(f"No mimetype known for {path}")


@dataclass
class FileWithId:
    name: str
    id: str


class DriveClient:
    def __init__(self, token_file, secrets_file, scopes=None):
        self.token_file = token_file
        self.secrets_file = secrets_file
        self.factory = ServiceFactory(self.token_file, self.secrets_file, scopes=scopes)

    def get_service(self, refresh=False):
        return self.factory.drive_api_service(refresh=refresh)

    def list_folders(self, parent=None, fields=None):
        return self._list_files(
            parent=parent, mimetype="application/vnd.google-apps.folder", fields=fields
        )

    def list_files(self, parent=None, fields=None):
        return self._list_files(parent=parent, fields=fields)

    def upload_file(self, path, name=None, mimetype=None, parent=None):
        name = name or path.name
        mimetype = mimetype or mimetype_for_path(path)

        file_metadata = {
            "name": name,
            "mimeType": mimetype,
        }
        if parent:
            file_metadata["parents"] = [parent]

        media = MediaFileUpload(path, mimetype=mimetype, resumable=True)
        file = (
            self.get_service()
            .files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        return FileWithId(name, file.get("id"))

    def create_folder(self, name, parent=None):
        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent:
            file_metadata["parents"] = [parent]

        file = (
            self.get_service().files().create(body=file_metadata, fields="id").execute()
        )
        return FileWithId(name, file.get("id"))

    def list_permissions(self, file_id):
        perms = []
        page_token = None
        service = self.get_service()
        while True:
            response = (
                service.permissions()
                .list(
                    fileId=file_id,
                    fields="nextPageToken,permissions(id, role, emailAddress)",
                    pageToken=page_token,
                )
                .execute()
            )
            for perm in response.get("permissions", []):
                perms.append(perm)
            page_token = response.get("nextPageToken", None)
            if page_token is None:
                break
        return perms

    def create_permission(
        self, file_id, role, type, email_address, send_notification=False
    ):
        validate_permission_role(role)
        validate_permission_type(type)
        meta_data = {
            "role": role,
            "type": type,
            "emailAddress": email_address,
        }
        response = (
            self.get_service()
            .permissions()
            .create(
                fileId=file_id, sendNotificationEmail=send_notification, body=meta_data
            )
            .execute()
        )
        return response["id"]

    def update_permission(self, file_id, permission_id, role):
        validate_permission_role(role)
        body = {"role": role}
        response = (
            self.get_service()
            .permissions()
            .update(fileId=file_id, permissionId=permission_id, body=body)
            .execute()
        )
        return response["id"]

    def delete_permission(self, file_id, permission_id):
        return (
            self.get_service()
            .permissions()
            .delete(fileId=file_id, permissionId=permission_id)
            .execute()
        )

    def _list_files(self, parent=None, mimetype=None, fields=None):
        if fields is None:
            custom_fields = False
            fields = ("id", "name")
        else:
            custom_fields = True
        fields_str = ", ".join(fields)
        files = []
        page_token = None
        q_terms = ["trashed=false"]
        if mimetype:
            q_terms.append(f"mimeType='{mimetype}'")
        if parent:
            q_terms.append(f"'{parent}' in parents")
        service = self.get_service()
        while True:
            response = (
                service.files()
                .list(
                    q=" and ".join(q_terms),
                    spaces="drive",
                    fields=f"nextPageToken, files({fields_str})",
                    pageToken=page_token,
                )
                .execute()
            )
            for file in response.get("files", []):
                # if the caller does not specify fields, return FileWithId objects, otherwise just the native obj
                if custom_fields:
                    obj = file
                else:
                    obj = FileWithId(file.get("name"), file.get("id"))
                files.append(obj)
            page_token = response.get("nextPageToken", None)
            if page_token is None:
                break
        return files


def validate_permission_role(role):
    if role not in VALID_PERMISSION_ROLES:
        raise ValueError(
            f"{role!r} is not a valid role, must be one of {VALID_PERMISSION_ROLES}"
        )


def validate_permission_type(_type):
    if _type not in VALID_PERMISSION_TYPES:
        raise ValueError(
            f"{_type!r} is not a valid type, must be one of {VALID_PERMISSION_TYPES}"
        )
