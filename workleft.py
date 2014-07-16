#!/usr/bin/python
# -*- coding: utf-8 -*-

import pprint
from datetime import date, timedelta

import requests

from icalendar import Calendar

from calendars import calendars

quotas = {
    'month': 1300 + 714.0
}
quotas['year'] = quotas['month'] * 12.0
quotas['week'] = quotas['year'] / 52.0
quotas['today'] = quotas['yesterday'] = quotas['week'] / 5.0

earnings = {
    'today': 0.0,
    'yesterday': 0.0,
    'week': 0.0,
    'month': 0.0,
    'year': 0.0
}


def main():
    today = date.today()
    yesterday = today - timedelta(days=1)
    week = today - timedelta(days=today.weekday())
    month = today.replace(day=1)
    year = today.replace(month=4, day=6)
    if year > today:
        year = year - timedelta(years=1)

    for url, hourly_rate in calendars:
        r = requests.get(url, verify='/Users/william/Projects/workleft/cacert.pem')
        c = Calendar.from_ical(r.text)

        for event in c.walk(name="VFREEBUSY"):
            start = event['dtstart'].dt
            end = event['dtend'].dt
            hours = (end - start).seconds / (60.0 * 60)
            earned = hours * hourly_rate
            d = start.date()

            if d <= today:
                if d >= year:
                    earnings['year'] += earned
                if d >= month:
                    earnings['month'] += earned
                if d >= week:
                    earnings['week'] += earned
                if d == yesterday:
                    earnings['yesterday'] += earned
                if d == today:
                    earnings['today'] += earned

    projected_earnings = earnings['year'] * 365.25 / ((today - year).days - 60)
    tax_estimate = max(0, projected_earnings - 10000) * 0.2

    print 'This Month: £%.2f (of £%.2f)' % (earnings['month'], quotas['month'])
    print ' This Week: £%.2f (of £%.2f)' % (earnings['week'], quotas['week'])
    print ' Yesterday: £%.2f (of £%.2f)' % (earnings['yesterday'], quotas['yesterday'])
    print '     Today: £%.2f (of £%.2f)' % (earnings['today'], quotas['today'])
    print ''
    print 'Projected Earnings: £%.2f' % projected_earnings
    print 'Estimated Tax Bill: £%.2f' % tax_estimate

if __name__ == '__main__':
    main()