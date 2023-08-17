from dataclasses import dataclass
import datetime
import zoneinfo

from .service import ServiceFactory


@dataclass
class Calendar:
    id: str
    name: str
    time_zone: zoneinfo.ZoneInfo
    description: str = ""
    access_role: str = ""

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d["id"],
            name=d.get("summaryOverride", d.get("summary")),
            time_zone=zoneinfo.ZoneInfo(d["timeZone"]),
            description=d.get("description", ""),
            access_role=d.get("accessRole", ""),
        )


@dataclass
class Event:
    id: str
    name: str
    start: datetime.datetime
    end: datetime.datetime
    calendar: Calendar
    tz: zoneinfo.ZoneInfo
    recurrence: list

    @classmethod
    def from_dict(cls, d, calendar, tz):
        return cls(
            id=d.get("id"),
            name=d.get("summary", "Untitled Event"),
            start=parse_event_date(d.get("start"), calendar.time_zone),
            end=parse_event_date(d.get("end"), calendar.time_zone),
            calendar=calendar,
            tz=tz,
            recurrence=d.get("recurrence"),
        )

    @property
    def all_day(self):
        return self.start.time() == self.end.time() == datetime.time(0, 0)


def parse_date(raw):
    return datetime.datetime.strptime(raw, "%Y-%m-%d").date()


def parse_event_date(obj, tz):
    if date := obj.get("date"):
        return datetime.datetime.combine(parse_date(date), datetime.time(0, 0)).replace(
            tzinfo=tz
        )
    return datetime.datetime.fromisoformat(obj["dateTime"])


class CalendarClient:
    def __init__(self, token_file, secrets_file, scopes=None, tz=None):
        self.token_file = token_file
        self.secrets_file = secrets_file
        self.factory = ServiceFactory(self.token_file, self.secrets_file, scopes=scopes)
        if tz is None:
            self.tz = datetime.timezone.utc
        else:
            self.tz = zoneinfo.ZoneInfo(tz) if isinstance(tz, str) else tz

    def get_service(self, refresh=False):
        return self.factory.calendar_api_service(refresh=refresh)

    def list_calendars(self, wrapped=True):
        response = self.get_service().calendarList().list().execute()
        if wrapped:
            return [Calendar.from_dict(item) for item in response["items"]]
        return response["items"]

    def list_events(self, calendars, start, end, expand_recurring=True):
        start = self._normalize_timestamp(start)
        end = self._normalize_timestamp(end)

        service = self.get_service()
        events = []
        for calendar in calendars:
            response = (
                service.events()
                .list(
                    calendarId=calendar.id,
                    timeMax=end.isoformat(),
                    timeMin=start.isoformat(),
                )
                .execute()
            )
            events.extend(
                [
                    Event.from_dict(event, calendar, self.tz)
                    for event in response["items"]
                    if event.get("status", "") != "cancelled"
                ]
            )
        if expand_recurring:
            events = self._expand_recurring(events, start, end, service=service)
        return events

    def _expand_recurring(self, events, start, end, service=None):
        ret = []
        for event in events:
            if not event.recurrence:
                ret.append(event)
                continue
            instances = self.list_event_instances(event, start, end, service=service)
            ret.extend(instances)
        return ret

    def list_event_instances(self, parent, start, end, service=None):
        service = service or self.get_service()
        response = (
            service.events()
            .instances(
                calendarId=parent.calendar.id,
                eventId=parent.id,
                timeMax=end.isoformat(),
                timeMin=start.isoformat(),
            )
            .execute()
        )
        return [
            Event.from_dict(event, parent.calendar, self.tz)
            for event in response["items"]
            if event.get("status", "") != "cancelled"
        ]

    def _normalize_timestamp(self, timestamp):
        if is_tz_aware(timestamp):
            return timestamp
        return timestamp.replace(tzinfo=self.tz)


def is_tz_aware(dt):
    return not (dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None)
