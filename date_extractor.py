import re
from datetime import datetime
import sys
import csv


def find_dates(text):
    dpattern = re.compile(r'\d{2} \w+ \d{4}')
    dates = dpattern.findall(text)
    d = set()
    for date in dates:
        try:
            dt = datetime.strptime(date, '%d %B %Y')
            d.add(dt)
        except Exception as e:
            print(e)
    if len(d) == 1:
        return (min(d).strftime('%d %B %Y'))
    elif len(d) > 1:
        return(min(d).strftime('%d %B %Y')+'-'+max(d).strftime('%d %B %Y'))


headings = set()
rows = []
with open(sys.argv[1], newline='', encoding='utf8') as f:
    reader = csv.DictReader(f)
    for count, row in enumerate(reader):
        headings.update(row.keys())
        dates = find_dates(row['EADScopeAndContent'])
        if dates is not None:
            row['EADUnitDate'] = dates
        rows.append(row)

with open(sys.argv[2], 'w', newline='', encoding='utf8') as f:
    writer = csv.DictWriter(f, fieldnames=headings)
    writer.writeheader()
    writer.writerows(rows)
