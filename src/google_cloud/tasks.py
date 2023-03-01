from .service import ServiceFactory


class TaskClient:
    def __init__(self, token_file, secrets_file, scopes=None):
        self.token_file = token_file
        self.secrets_file = secrets_file
        self.factory = ServiceFactory(self.token_file, self.secrets_file, scopes=scopes)
        self.service = self.get_service()

    def get_service(self, refresh=False):
        return self.factory.tasks_api_service(refresh=refresh)

    def list_tasklists(self):
        response = self.service.tasklists().list().execute()
        return response["items"]

    def get_tasklist(self, title):
        for tasklist in self.list_tasklists():
            if tasklist["title"] == title:
                return tasklist
        raise ValueError(f"Tasklist {title!r} not found")

    def clear_tasklist(self, tasklist_id):
        # google tasks().clear method seems to have no effect, so iterate over items
        # and delete one-by-one
        # self.service.tasks().clear(tasklist=id).execute()
        for task in self.list_tasks(tasklist_id):
            self.delete_task(tasklist_id, task["id"])

    def create_tasklist(self, title):
        return self.service.tasklists().insert(body=title)

    def list_tasks(self, tasklist_id):
        response = self.service.tasks().list(tasklist=tasklist_id).execute()
        return response["items"]

    def insert_task(self, tasklist_id, task):
        return (
            self.service.tasks()
            .insert(
                tasklist=tasklist_id,
                body={"title": task},
            )
            .execute()
        )

    def delete_task(self, tasklist_id, task_id):
        return self.service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()
