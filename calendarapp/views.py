import calendar
from datetime import date, timedelta

from django.shortcuts import render

from meetings.models import Meeting
from tasks.models import Task


def month_view(request, year, month):
    days_in_month = calendar.monthrange(year, month)[1]
    month_days = [date(year, month, day) for day in range(1, days_in_month + 1)]

    tasks = Task.objects.filter(deadline__year=year, deadline__month=month)
    meetings = Meeting.objects.filter(start_at__year=year, start_at__month=month)

    current = date(year, month, 1)
    prev_month = (current - timedelta(days=1)).replace(day=1)
    next_month = (current + timedelta(days=31)).replace(day=1)

    day_events = {}

    for task in tasks:
        if task.deadline:
            day_events.setdefault(task.deadline, []).append(("tasks", task))

    for meeting in meetings:
        day_events.setdefault(meeting.start_at.date(), []).append(("meeting", meeting))

    context = {
        "year": year,
        "month": month,
        "month_days": month_days,
        "day_events": day_events,
        "prev": (prev_month.year, prev_month.month),
        "next": (next_month.year, next_month.month),
    }
    return render(request, "calendarapp/month.html", context)


def day_view(request, year, month, day):
    day_date = date(year, month, day)

    tasks = Task.objects.filter(deadline=day_date)
    meetings = Meeting.objects.filter(start_at__date=day_date)

    prev_day = day_date - timedelta(days=1)
    next_day = day_date + timedelta(days=1)

    context = {
        "day_date": day_date,
        "tasks": tasks,
        "meetings": meetings,
        "prev": (prev_day.year, prev_day.month, prev_day.day),
        "next": (next_day.year, next_day.month, next_day.day),
    }
    return render(request, "calendarapp/day.html", context)
