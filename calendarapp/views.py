import calendar
from datetime import date

from django.shortcuts import render

from meetings.models import Meeting
from tasks.models import Task


def month_view(request, year, month):
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.itermonthdates(year, month)

    tasks = Task.objects.filter(deadline__year=year, deadline__month=month)
    meetings = Meeting.objects.filter(start_at__year=year, start_at__month=month)

    day_events = {}

    for task in tasks:
        if task.deadline:
            day_events.setdefault(task.deadline.date(), []).append(("tasks", task))

    for meeting in meetings:
        day_events.setdefault(meeting.start_at.date(), []).append(("meeting", meeting))

    context = {
        "year": year,
        "month": month,
        "month_days": month_days,
        "day_events": day_events,
    }
    return render(request, "calendarapp/month.html", context)


def day_view(request, year, month, day):
    day_date = date(year, month, day)

    tasks = Task.objects.filter(deadline=day_date)
    meetings = Meeting.objects.filter(start_at__date=day_date)

    context = {
        "day_date": day_date,
        "tasks": tasks,
        "meetings": meetings,
    }
    return render(request, "calendarapp/day.html", context)
