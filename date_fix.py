import csv
import sys
from datetime import datetime, timedelta


def from_excel(ordinal, _epoch0=datetime(1899, 12, 31)):
    if ordinal > 59:
        ordinal -= 1  # Excel leap year bug, 1900 is not a leap year!
    d = (_epoch0 + timedelta(days=ordinal)).replace(microsecond=0)
    datestring = d.date().strftime("%d %B %Y")
    return datestring.lstrip('01 ')


def date_check(date, edate, ldate):
    if date.isnumeric():
        if edate == ldate:
            if date != edate:
                print(date, edate, ldate)
                return False
    else:
        return True


rows = []
headings = set()
with open(sys.argv[1], newline='', encoding='utf8') as f:
    reader = csv.DictReader(f)
    for count, row in enumerate(reader):
        headings.update(row.keys())
        if not date_check(
            row['EADUnitDate'], row['EADUnitDateEarliest'], row['EADUnitDateLatest']):
            fixed = from_excel(int(row['EADUnitDate']))
            print(count, row['EADUnitDate'], '->', fixed)
            row['EADUnitDate'] = fixed
            rows.append(row)

with open(sys.argv[2], 'w', newline='', encoding='utf8') as f:
    writer = csv.DictWriter(f, fieldnames=headings)
    writer.writerows(rows)
