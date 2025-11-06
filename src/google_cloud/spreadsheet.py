from dataclasses import dataclass

from .service import ServiceFactory
from .utils import column_number_to_name
from .utils import address_to_coordinates


@dataclass
class GoogleSpreadsheet:
    id: str
    title: str
    sheets: list
    service_factory: ServiceFactory

    def __str__(self):
        return self.title

    @classmethod
    def for_id(cls, id, token_file, secrets_file, scopes=None):
        service_factory = ServiceFactory(token_file, secrets_file, scopes=scopes)
        service = service_factory.sheets_api_service()

        response = service.get(spreadsheetId=id).execute()
        title = response["properties"]["title"]
        sheets = GoogleSheet.from_response(response["sheets"])

        # do a batchGet api call to get data for all the sheets at once
        ranges = [sheet.encompassing_range() for sheet in sheets]
        response = service.values().batchGet(spreadsheetId=id, ranges=ranges).execute()
        for sheet, value_range in zip(sheets, response["valueRanges"]):
            if "values" not in value_range:
                # its an empty sheet, continue
                continue
            sheet.set_values(value_range["values"])
        return cls(id, title, sheets, service_factory)

    def get_sheet(self, title):
        for sheet in self.sheets:
            if sheet.title.lower() == title.lower():
                return sheet

    def update_range(self, range, values, input_option="RAW"):
        data = [{"range": range, "values": values}]
        batch_update_values_request_body = {
            "valueInputOption": input_option,
            "data": data,
        }
        self.service_factory.sheets_api_service().values().batchUpdate(
            spreadsheetId=self.id, body=batch_update_values_request_body
        ).execute()

    def add_sheet(self, name):
        data = {"requests": [{"addSheet": {"properties": {"title": name}}}]}
        self.service_factory.sheets_api_service().batchUpdate(
            spreadsheetId=self.id, body=data
        ).execute()

    def update_single_cells(self, cells, values, input_option="RAW"):
        data = []
        for cell, value in zip(cells, values):
            data.append({"range": cell, "values": [[value]]})
        batch_update_values_request_body = {
            "valueInputOption": input_option,
            "data": data,
        }
        self.service_factory.sheets_api_service().values().batchUpdate(
            spreadsheetId=self.id, body=batch_update_values_request_body
        ).execute()


@dataclass
class GoogleSheet:
    id: str
    title: str
    index: int
    hidden: bool
    sheet_type: str
    meta_row_count: int
    meta_col_count: int
    _values: list = None

    @classmethod
    def from_response(cls, response):
        sheets = []
        for item in response:
            props = item["properties"]
            sheets.append(
                cls(
                    id=props["sheetId"],
                    title=props["title"],
                    index=props["index"],
                    hidden=props.get("hidden", False),
                    sheet_type=props["sheetType"],
                    meta_row_count=props["gridProperties"]["rowCount"],
                    meta_col_count=props["gridProperties"]["columnCount"],
                )
            )
        return sheets

    def set_values(self, values):
        self._values = values
        self.row_count = len(values)
        self.col_count = max(len(_) for _ in values)

    def encompassing_range(self):
        last_col_letter = column_number_to_name(self.meta_col_count)
        return f"{self.title}!A1:{last_col_letter}{self.meta_row_count}"

    @property
    def rows(self):
        return self._values

    def get(self, row_idx, col_idx):
        try:
            return self._values[row_idx - 1][col_idx - 1]
        except IndexError:
            pass

    def __getitem__(self, address):
        row, col = address_to_coordinates(address)
        return self.get(row, col)
