from datetime import date, datetime, timedelta, timezone


class DateTimeService:
    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    @staticmethod
    def today() -> date:
        return datetime.now(timezone.utc).date()

    @staticmethod
    def parse_date(value: str | None) -> date | None:
        if not value:
            return None
        return date.fromisoformat(value[:10])

    @staticmethod
    def compute_status(next_due_date: str | None, alert_days_before: int) -> str:
        due_date = DateTimeService.parse_date(next_due_date)
        if due_date is None:
            return "no_schedule"

        today = DateTimeService.today()
        if due_date < today:
            return "overdue"

        if due_date <= today + timedelta(days=alert_days_before):
            return "upcoming"

        return "ok"
