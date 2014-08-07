#!/usr/bin/python
# -*- coding: utf-8 -*-

import calendar
from datetime import date, timedelta
from collections import defaultdict

import requests

from icalendar import Calendar

from config import calendars, goals, start

TAX_RATE = 0.2

def goal_on(goals, day):
    total = 0.0
    for g in goals:
        if g.start <= day < (g.end or date.max):
            total += g.monthly_amount / calendar.monthrange(day.year, day.month)[1]
    return total


def incoming(calendars):
    net_by_day = defaultdict(int)
    tax_bill = 0.0
    for c in calendars:
        r = requests.get(c.url)
        ical = Calendar.from_ical(r.text)
        for event in ical.walk(name="VEVENT"):
            if event['description'].startswith(u'£'):
                gross = int(event['description'].replace(u'£', ''))
                if c.taxed:
                    net = gross
                else:
                    net = gross * (1 - TAX_RATE)
                    tax_bill += gross - net
                net_by_day[day] += net
        for event in ical.walk(name="VFREEBUSY"):
            start = event['dtstart'].dt
            end = event['dtend'].dt
            day = start.date()
            hours = (end - start).seconds / (60.0 * 60)
            gross = hours * c.hourly_rate
            if c.taxed:
                net = gross
            else:
                net = gross * (1 - TAX_RATE)
                tax_bill += gross - net
            net_by_day[day] += net
    return net_by_day, tax_bill

def main():
    net_by_day, tax_bill = incoming(calendars)
    
    today = [date.today(), 0, 0]
    week = [today[0] - timedelta(days=today[0].weekday()), 0, 0]
    month = [today[0].replace(day=1), 0, 0]
    year = [today[0].replace(month=4, day=6), 0, 0]

    overunder = 0.0
    d = start
    while d <= today[0]:
        earned = net_by_day[d]
        goal = goal_on(goals, d)
        overunder += earned - goal
        for t in [today, week, month, year]:
            if t[0] <= d <= today[0]:
                t[1] += earned
                t[2] += goal
        d = d + timedelta(days=1)
        
    print '        Today: £%.2f (of £%.2f)' % (today[1], today[2])
    print '    This Week: £%.2f (of £%.2f)' % (week[1], week[2])
    print '   This Month: £%.2f (of £%.2f)' % (month[1], month[2])
    print 'This Tax Year: £%.2f (of £%.2f)' % (year[1], year[2])
    print '        Extra: £%.2f' % overunder
    print '     Tax Bill: £%.2f' % tax_bill
    

def main2():
    total_gross = {
        'today': 0.0,
        'yesterday': 0.0,
        'week': 0.0,
        'month': 0.0,
        'year': 0.0
    }
    total_net = {
        'today': 0.0,
        'yesterday': 0.0,
        'week': 0.0,
        'month': 0.0,
        'year': 0.0
    }
    tax_savings = 0.0

    today = date.today()
    yesterday = today - timedelta(days=1)
    week = today - timedelta(days=today.weekday())
    month = today.replace(day=1)
    year = today.replace(month=4, day=6)
    if year > today:
        year = year - timedelta(years=1)

    for url, hourly_rate, tax_rate in calendars:
        r = requests.get(url)
        c = Calendar.from_ical(r.text)

        for event in c.walk(name="VFREEBUSY"):
            start = event['dtstart'].dt
            end = event['dtend'].dt
            hours = (end - start).seconds / (60.0 * 60)
            gross = hours * hourly_rate
            tax = gross * tax_rate
            net = gross - tax
            tax_savings += tax
            d = start.date()

            if d <= today:
                if d >= year:
                    total_gross['year'] += gross
                    total_net['year'] += net
                if d >= month:
                    total_gross['month'] += gross
                    total_net['month'] += net
                if d >= week:
                    total_gross['week'] += gross
                    total_net['week'] += net
                if d == yesterday:
                    total_gross['yesterday'] += gross
                    total_net['yesterday'] += net
                if d == today:
                    total_gross['today'] += gross
                    total_net['today'] += net

    projected_gross = total_gross['year'] * 365.25 / ((today - year).days - 60)
    tax_estimate = max(0, projected_gross - 10000) * 0.2

    print 'This Month: £%.2f (of £%.2f)' % (total_net['month'], quotas['month'])
    print ' This Week: £%.2f (of £%.2f)' % (total_net['week'], quotas['week'])
    print ' Yesterday: £%.2f (of £%.2f)' % (total_net['yesterday'], quotas['yesterday'])
    print '     Today: £%.2f (of £%.2f)' % (total_net['today'], quotas['today'])
    print ''
    print 'Projected Earnings: £%.2f' % projected_gross
    print 'Estimated Tax Bill: £%.2f' % tax_estimate
    print '       Tax Savings: £%.2f' % tax_savings

if __name__ == '__main__':
    main()
