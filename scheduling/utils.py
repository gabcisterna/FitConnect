from datetime import datetime, timedelta
from django.utils import timezone
from .models import ClassSession

def get_or_create_session_for_date(schedule, target_date, tz=None):
    tzinfo = tz or timezone.get_current_timezone()
    # Ajustar target_date al weekday del schedule (si no coincide)
    delta = (schedule.weekday - target_date.weekday()) % 7
    d = target_date + timedelta(days=delta)
    start_naive = datetime.combine(d, schedule.start_time)
    start_at = timezone.make_aware(start_naive, tzinfo)
    end_at = start_at + schedule.duration

    session, created = ClassSession.objects.get_or_create(
        schedule=schedule,
        start_at=start_at,
        defaults={
            "end_at": end_at,
            "capacity": schedule.capacity,  # min(sala, tipo)
            "status": "scheduled",
        },
    )
    return session, created
