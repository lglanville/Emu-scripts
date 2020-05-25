from datetime import datetime
import calendar
import re
import argparse
from pathlib import Path


MONTHS = list(calendar.month_name)[1:]
MONTHS.extend(list(calendar.month_abbr)[1:])
MONTHGROUP = "(" + '|'.join([m for m in MONTHS]) + r")"
MONTH_NUMS = [str(m) for m in list(range(1, 13, 1))]
MONTHNUM_GROUP = "(" + '|'.join([m for m in MONTH_NUMS]) + ")"
DAY = r"([0-3]?\d)"
DELIM = "[ ,./]{1,3}"
YEAR = r"([12][890]\d{2})"
CIRCA = r"(c\.? ?|circa ?)?"

DAY_RANGE_RE = re.compile('('+DAY+'?'+DELIM+DAY+DELIM+MONTHGROUP+DELIM+YEAR+')', flags=re.IGNORECASE)
REV_DAY_RANGE_RE = re.compile('('+MONTHGROUP+'('+DELIM+DAY+')?'+DELIM+DAY+DELIM+YEAR+')', flags=re.IGNORECASE)
MONTH_RANGE_RE = re.compile('(('+DAY+DELIM+MONTHGROUP+DELIM+')?'+DAY+DELIM+MONTHGROUP+DELIM+YEAR+')', flags=re.IGNORECASE)
DELIM_RE = re.compile('('+DAY+DELIM+MONTHNUM_GROUP+DELIM+YEAR+')', flags=re.IGNORECASE)
MDELIM_RE = re.compile('('+CIRCA+MONTHNUM_GROUP+DELIM+YEAR+')', flags=re.IGNORECASE)
MONTH_RE = re.compile('('+CIRCA+'('+MONTHGROUP+DELIM+')?'+MONTHGROUP+DELIM+YEAR+')', flags=re.IGNORECASE)
YEAR_RE = re.compile(r"("+CIRCA+YEAR+"(s)?)", flags=re.IGNORECASE)

FD_REGEX = re.compile(
    r"(((\d{1,2}) "+MONTHGROUP+"?[., ]{1,3})?(\d{1,2})[,. ]{1,2}?" + MONTHGROUP + r"[,-. ]{1,2}?(\d{2,4}))",
    flags=re.IGNORECASE)

FDREV_REGEX = re.compile(
    r"(("+MONTHGROUP+" (\d{1,2})[ -,]{1,3})?"+MONTHGROUP+" (\d{1,2})([ -,]{1,3}(\d{1,2}))?,? (\d{2,4}))",
    flags=re.IGNORECASE)
DELIM_REGEX = re.compile(r"((\d{1,2})[/\.]("+ '|'.join([m for m in MONTH_NUMS]) + ")[-/\.](\d{2,4}))")
MDELIM_REGEX = re.compile(r"("+CIRCA+"(" + '|'.join([m for m in MONTH_NUMS]) + ")[/\.](\d{2,4}))")
MDATE_REGEX = MDATE_REGEX = re.compile("(("+CIRCA+MONTHGROUP+"[ -]{1,3})?"+CIRCA + MONTHGROUP + r",? (\d{2,4}))", flags=re.IGNORECASE)
YEAR_REGEX = re.compile(r"("+CIRCA+"([12][567890]\d{2})('?s)?)", flags=re.IGNORECASE)
DAYS = calendar.day_name[:]
DAYS.extend(calendar.day_abbr[:])

class circadate(datetime):
    """Class to express fudgy dates"""

    def __new__(cls, year, month=1, day=1, hour=0, minute=0, second=0, circa=False, no_day=False, no_month=False):
        new = super().__new__(cls, year, month, day)
        new.circa = circa
        new.no_day = no_day
        new.no_month = no_month
        return new

    def __str__(self):
        if self.no_day:
            ds = self.strftime("%B %Y")
        elif self.no_month:
            ds = self.strftime("%Y")
        else:
            ds = self.strftime("%d %B %Y").lstrip('0')
        if self.circa:
            ds = 'c.'+ds
        return ds

    def __repr__(self):
        return f"<circadate {str(self)}>"

    @classmethod
    def strptime(cls, date_string, format, circa=False, no_day=False, no_month=False):
        import _strptime
        try:
            new = _strptime._strptime_datetime(cls, date_string, format)
            new.circa = circa
            new.no_day = no_day
            new.no_month = no_month
            return new
        except Exception:
            print("Failed to convert", date_string, "to date")
            return None


class daterange(object):
    """Class to express a date range"""

    def __init__(self, *dates):
        self.earliest = min(dates)
        self.latest = max(dates)

    def __str__(self):
        if str(self.earliest) == str(self.latest):
            return str(self.earliest)
        else:
            if str(self.earliest) in str(self.latest):
                return str(self.latest)
            elif str(self.latest) in str(self.earliest):
                return str(self.earliest)
            else:
                return str(self.earliest)+'-'+str(self.latest)

    def latestcolumn(self, circa_margin=5):
        if self.latest.circa and self.latest.no_month:
            return self.latest.year+circa_margin
        else:
            return self.latest.year

    def earliestcolumn(self, circa_margin=5):
        if self.earliest.circa and self.earliest.no_month:
            return self.earliest.year-circa_margin
        else:
            return self.earliest.year

    def columns(self, circa_margin=5):
        return (
            str(self), self.earliestcolumn(circa_margin),
            self.latestcolumn(circa_margin))


def strip_days(text):
    for day in DAYS:
        text = text.replace(day, '')
    while '  ' in text:
        text = text.replace('  ', ' ')
    text = text.replace(b'\xe2\x80\x93'.decode(), '-')
    return text


def pull_dates(text, circa=False):
    """Extract all potential dates from a block of text and return a
    daterange object.
    """
    dates = []
    d, text = dayrange_extract(text)
    dates.extend(d)
    d, text = reverse_dayrange_extract(text)
    dates.extend(d)
    d, text = monthrange_extract(text)
    dates.extend(d)
    d, text = month_extract(text)
    dates.extend(d)
    d, text = delimited_extract(text)
    dates.extend(d)
    d, text = monthdelimited_extract(text)
    dates.extend(d)
    d, text = year_extract(text)
    dates.extend(d)
    dates = [d for d in dates if d is not None]
    if dates != []:
        return daterange(*dates)


def dayrange_extract(text):
    """Extracts dates from text in the form of  1 January 1982, 1 Jan, 1982,
    etc"""
    dates = []
    matches = REV_DAY_RANGE_RE.findall(text)
    for date in matches:
        if len(date[3]) == 3:
            fstring = "%d %b %Y"
        else:
            fstring = "%d %B %Y"
        dstring = f"{'0'*(2-len(date[1]))+date[1]} {date[3].title()} {date[4]}"
        dates.append(circadate.strptime(dstring, fstring))
        dstring = f"{'0'*(2-len(date[2]))+date[2]} {date[3].title()} {date[4]}"
        dates.append(circadate.strptime(dstring, fstring))
        text = text.replace(date[0], '')
    return dates, text


def reverse_dayrange_extract(text):
    """Extracts dates in  the form of jan 6 1978, aug 8-9 1876 etc."""
    dates = []
    matches = REV_DAY_RANGE_RE.findall(text)
    for date in matches:
        if len(date[1]) == 3:
            fstring = "%d %b %Y"
        else:
            fstring = "%d %B %Y"
        dstring = f"{'0'*(2-len(date[4]))+date[4]} {date[1].title()} {date[5]}"
        dates.append(circadate.strptime(dstring, fstring))
        if date[3] != '':
            dstring = f"{'0'*(2-len(date[3]))+date[3]} {date[1].title()} {date[4]}"
            dates.append(circadate.strptime(dstring, fstring))
            text = text.replace(date[0], '')
    return dates, text


def monthrange_extract(text):
    """Extracts dates from text in the form of  January 1982, Jan, 1982,
    aug-sep 1765 etc"""
    dates = []
    matches = MONTH_RANGE_RE.findall(text)
    for date in matches:
        if len(date[5]) == 3:
            fstring = "%d %b %Y"
        else:
            fstring = "%d %B %Y"
        dstring = f"{'0'*(2-len(date[4]))+date[4]} {date[5].title()} {date[6]}"
        dates.append(circadate.strptime(dstring, fstring))
        if date[3] != '':
            if len(date[3]) == 3:
                fstring = "%d %b %Y"
            else:
                fstring = "%d %B %Y"
            dstring = f"{'0'*(2-len(date[2]))+date[2]} {date[3].title()} {date[6]}"
            dates.append(circadate.strptime(dstring, fstring))
        text = text.replace(date[0], '')
    return dates, text


def delimited_extract(text):
    """Extracts dates from text in the form of  1/1/1982, 1.1.1982 etc"""
    dates = []
    matches = DELIM_RE.findall(text)
    for date in matches:
        dates.append(circadate(int(date[3]), int(date[2]), int(date[1])))
        text = text.replace(date[0], '')
    return dates, text


def month_extract(text):

    dates = []
    matches = MONTH_RE.findall(text)
    for date in matches:
        circa = False
        if date[1] != '':
            circa = True
        if len(date[4]) == 3:
            fstring = "%b %Y"
        else:
            fstring = "%B %Y"
        dstring = f"{date[4].title()} {date[5]}"
        dates.append(circadate.strptime(dstring, fstring, no_day=True, circa=circa))
        if date[3] != '':
            if len(date[3]) == 3:
                fstring = "%b %Y"
            else:
                fstring = "%B %Y"
            dstring = f"{date[3].title()} {date[5]}"
            dates.append(circadate.strptime(dstring, fstring, no_day=True, circa=circa))
        text = text.replace(date[0], '')
    return dates, text


def monthdelimited_extract(text):
    dates = []
    matches = MDELIM_RE.findall(text)
    for date in matches:
        dates.append(circadate(int(date[3]), int(date[2])))
        text = text.replace(date[0], '')
    return dates, text


def year_extract(text):
    """Extracts a year or decade from text in the form of 1982, c.1982, 1980s
    etc"""
    dates = []
    m = YEAR_REGEX.findall(text)
    for date in m:
        circa = False
        if date[1] != '':
            circa = True
        if date[3] != '':
            earliest = int(date[2])
            latest = earliest + 10
            dates.append(circadate(earliest, no_month=True))
            dates.append(circadate(latest, no_month=True))
        else:
            dates.append(circadate(int(date[2]), no_month=True, circa=circa))
    return dates, text


def main(workbookpath, column='EADUnitDate', cmargin=5):
    try:
        import openpyxl
    except ImportError:
        print("You don't have openpyxl installed. Try 'pip install openpyxl'")
        exit()
    wb = openpyxl.open(workbookpath)
    for ws in wb.worksheets:
        date_column = None
        for cell in ws[1]:
            if cell.value == column:
                date_column = cell.column_letter
                col_index = cell.column
                break
        if date_column is not None:
            ws.insert_cols(col_index+1, 3)
            ws.cell(1, col_index+1).value = 'EADUnitDate'
            ws.cell(1, col_index+2).value = 'EADUnitDateEarliest'
            ws.cell(1, col_index+3).value = 'EADUnitDateLatest'
            for cell in ws[date_column][1:]:
                if cell.value is not None:
                    if type(cell.value) == datetime:
                        date = cell.value
                        dates = daterange(circadate(date.year, date.month, date.day))
                    else:
                        datestring = str(cell.value).replace('\n', ' ')
                        datestring = strip_days(datestring)
                        dates = pull_dates(datestring)
                    if dates is not None:
                        cols = dates.columns(circa_margin=cmargin)
                        ds = str(cell.value).replace('\n', ' ')
                        print(f"Row {cell.row}: Converted", ds, "->", *cols)
                        ws.cell(cell.row, col_index+1).value = cols[0]
                        ws.cell(cell.row, col_index+2).value = cols[1]
                        ws.cell(cell.row, col_index+3).value = cols[2]
                    else:
                        print(f"Row {cell.row}: Found no dates in ", datestring)
                        ws.cell(cell.row, col_index+1).value = 'Undated'
                else:
                    print(f"Row {cell.row}: Empty cell")
                    ws.cell(cell.row, col_index+1).value = 'Undated'

    p = Path(workbookpath)
    new_path = p.parent / (p.stem+'_datefixed.xlsx')
    print("Saving workbook to", new_path)
    wb.save(new_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Fix horrible dates in an Excel spreadsheet')
    parser.add_argument(
        'workbook', metavar='i', type=str, help='Workbook with horrible dates')
    parser.add_argument(
        '--datecolumn', '-d', default='EADUnitDate',
        help='Column to extract dates from, defaults to EADUnitDate')
    parser.add_argument(
        '--circamargin', '-c', type=int, default=5,
        help='Margin to place on earliest and latest dates where dates are circa')
    args = parser.parse_args()
    main(args.workbook, column=args.datecolumn, cmargin=args.circamargin)
