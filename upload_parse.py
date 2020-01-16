import csv
import re
import calendar
import logging
import argparse
import os
from io import StringIO
from collections import Counter
FORMAT = '[%(levelname)s] Row %(rownum)s,  Field %(field)s - %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('fieldhelp')

man_heads = [
    'EADUnitID', 'EADUnitTitle', 'EADUnitDate', 'EADUnitDateEarliest',
    'EADUnitDateLatest', 'AssParentObjectRef.EADUnitID',
    'LocCurrentLocationRef.LocHolderName',
    'EADLevelAttribute']

opt_heads = [
    'EADExtent_tab', 'EADAccessRestrictions', 'EADUseRestrictions',
    'EADAppraisalInformation', 'EADPhysicalDescription_tab',
    'EADGenreForm_tab', 'NotNotes', 'ObjectType', 'ConConditionDetails',
    'ConHandlingInstructions', 'EADPhysicalTechnical',
    'AdmPublishWebNoPassword', 'SecDepartment_tab', 'EADPreviousID_tab',
    'EADDimensions', 'ConConditionStatus', 'EADScopeAndContent']

mult_heads = [
    'Multimedia', 'MulTitle', 'DetResourceType',
    'DetSource', 'AdmPublishWebNoPassword']

all_heads = man_heads+opt_heads

holder_heads = [
    'LocHolderName', 'LocLocationType', 'LocStorageType',
    'LocHolderLocationRef.LocLocationCode']


class multimedia(dict):
    def __init__(self, row, rownum):
        super(multimedia, self).__init__(row)
        self.rownum = rownum
        self.pref = list(self.keys())[0].split('.')[0]
        self.d = {'rownum': self.rownum}
        self.resource = self.get_value('Multimedia')
        if not os.path.exists(self.resource):
            self.d['field'] = self.field_name('Multimedia')
            logger.error(
                'Cannot find resource: %s',
                self.resource, extra=self.d)
        if self.get_value('AdmPublishWebNoPassword') not in ('yes', 'no'):
            self.d['field'] = self.field_name('AdmPublishWebNoPassword')
            logger.error(
                'Invalid value: %s',
                self.get_value('AdmPublishWebNoPassword'), extra=self.d)

        for field in mult_heads:
            if self.get(field) == '':
                self.d['field'] = field
                logger.warning(
                    'Missing mandatory value', extra=self.d)

    def get_value(self, suffix):
        field = [field for field in self.keys() if field.endswith(suffix)]
        if field != []:
            return(self.get(field[0]))
        else:
            return None

    def field_name(self, suffix):
        return(self.pref+'.'+suffix)


class holder(dict):
    def __init__(self, row, rownum):
        super(holder, self).__init__(row)
        self.rownum = rownum
        self.d = {'rownum': self.rownum}
        self.loc = self.get('LocHolderLocationRef.LocLocationCode')
        self.name = self.get('LocHolderName')
        self.loc_check()
        self.field_check()

    def loc_check(self):
        if re.fullmatch(r'[A-Z]{1,2}\d{1,2}/\d{1,2}', self.loc) is None:
            self.d['field'] = 'LocHolderLocationRef.LocLocationCode'
            logger.warning(
                'Invalid location attribute: %s',
                self.loc, extra=self.d)

    def field_check(self):
        for field in holder_heads:
            if self.get(field) == '':
                self.d['field'] = field
                logger.warning(
                    'Missing mandatory value', extra=self.d)


class record(dict):
    '''subclass of dict that validates incoming data on initialisation
    according to UMA standards and EMu upload requirements'''

    def __init__(self, row, rownum, mandatory=True):
        super(record, self).__init__(row)
        self.rownum = rownum
        self.date = self.get_value('EADUnitDate')
        self.edate = self.get_value('EADUnitDateEarliest')
        self.ldate = self.get_value('EADUnitDateLatest')
        self.parent = self.get_value('AssParentObjectRef.EADUnitID')
        self.ident = self.get_value('EADUnitID')
        self.location = self.get_value('LocCurrentLocationRef.LocHolderName')
        self.level = self.get_value('EADLevelAttribute')
        self.reg_id = re.compile(r'\d{4}\.\d{4}\.\d{5}')
        self.reg_pid = re.compile(r'\d{4}\.\d{4}(\.\d{5})?')
        self.d = {'rownum': self.rownum}
        self.check_multimedia()
        if list(row.values()) == ['' for x in range(len(row.values()))]:
            self.d['field'] = 'ALL'
            logger.error(
                'Blank row', extra=self.d)
            raise Exception()
        self.date_check()
        if mandatory:
            self.man_check()

        if self.level not in ('Item', 'Sub-item', 'Unit') and self.level != '':
            self.d['field'] = 'EADLevelAttribute'
            logger.warning(
                'Invalid level attribute: %s',
                self.level, extra=self.d)

        if self.reg_id.fullmatch(self.ident) is None:
            self.d['field'] = 'EADUnitID'
            logger.warning(
                'Invalid identifier: %s',
                self.ident, extra=self.d)
        if self.reg_pid.fullmatch(self.parent) is None and self.parent != '':
            self.d['field'] = 'AssParentObjectRef.EADUnitID'
            logger.warning(
                'Invalid parent identifier: %s',
                self.parent, extra=self.d)

        if self.parent not in self.location:
            self.d['field'] = 'LocCurrentLocationRef.LocHolderName'
            logger.info(
                'Holder name does not match '
                'AssParentObjectRef.EADUnitID: %s, %s',
                self.location, self.parent, extra=self.d)
        if self.parent not in self.ident and self.level == 'Item':
            self.d['field'] = 'EADUnitID'
            logger.warning(
                'EADUnitID does not match '
                'AssParentObjectRef.EADUnitID: %s, %s',
                self.ident, self.parent, extra=self.d)

    def check_multimedia(self):
        for m in self.get_multimedia().values():
            multi = multimedia(m, rownum)
            if multi.get_value('MulTitle') is not None:
                if multi.get_value('MulTitle') not in self.get('EADUnitTitle'):
                    self.d['field'] = multi.field_name('MulTitle')
                    logger.warning(
                        'MulTitle does not match EadUnitTitle: %s, %s',
                        multi.field_name('MulTitle'), self.get('EADUnitTitle'),
                        extra=self.d)

    def get_value(self, field):
        if self.get(field) is not None:
            return(self.get(field))
        else:
            return('')

    def date_check(self):
        self.d = {'rownum': self.rownum}
        if '/' in self.date or 'circa' in self.date.lower():
            self.d['field'] = 'EADUnitDate'
            logger.warning(
                'Invalid date format: %s', self.date, extra=self.d)
        else:
            months = re.findall('[a-z,A-Z]+', self.date)
            excepts = ['c', 'Undated']+list(calendar.month_name)
            for month in months:
                if month not in excepts:
                    self.d['field'] = 'EADUnitDate'
                    logger.warning(
                        'Invalid date format: %s', self.date, extra=self.d)
        try:
            if int(self.edate) > int(self.ldate):
                self.d['field'] = 'EADUnitDateEarliest'
                logger.warning(
                    'Earliest date later than latest: %s, %s',
                    self.edate, self.ldate, extra=self.d)
        except (ValueError, TypeError):
            pass

    def man_check(self):
        self.d = {'rownum': self.rownum}
        for field in man_heads:
            if self.get_value(field) == '':
                if field in ('EADUnitDateEarliest', 'EADUnitDateLatest') and self.date == 'Undated':
                    pass
                else:
                    self.d['field'] = field
                    logger.error(
                        'Missing mandatory value', extra=self.d)

    def get_multimedia(self):
        multi = {}
        for k, v in self.items():
            if k.startswith('MulMultiMediaRef_tab') and v != '':
                ind = re.findall(r'\((\d+)\)', k)
                if ind != []:
                    ind = int(ind[0])
                else:
                    ind = 1
                if multi.get(ind) is None:
                    multi.update({ind: {k: v}})
                else:
                    multi[ind].update({k: v})
        return(multi)


def get_reader(path):
    with open(path, encoding='utf-8') as f:
        text = f.read()
        text = text.replace('\r\n', '|').lstrip('\ufeff')
    dialect = csv.Sniffer().sniff(text)
    reader = csv.DictReader(StringIO(text), dialect=dialect)
    return(reader)


def check_fields(fields, mandatory=True):
    d = {'rownum': 1}
    for column, field in enumerate(fields, 1):
        if field.endswith(')'):
            f = field.split('(')[0]
        else:
            f = field
        if f not in all_heads and f != '' and not f.startswith('MulMultiMediaRef_tab'):
            d['field'] = field
            logger.error(
                'Invalid column heading: %s', f, extra=d)
        elif f == '':
            d['field'] = 'None'
            logger.error(
                'blank column heading: column {}'.format(column),
                extra=d)
        elif f.startswith('MulMultiMediaRef_tab'):
            ff = f.split('.')[1]
            if ff not in mult_heads:
                d['field'] = f
                logger.error(
                    'Invalid multimedia column heading: %s', f,
                    extra=d)
    if mandatory:
        for field in man_heads:
            if field not in reader.fieldnames:
                d['field'] = field
                logger.error('Missing mandatory column heading', extra=d)
    counts = Counter(reader.fieldnames)
    for field, count in counts.items():
        if count > 1 and field != '':
            d['field'] = field
            logger.error('Duplicate column heading', extra=d)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Check an EMu upload delimited file for possible errors '
        'and data quality issues')
    parser.add_argument(
        'file', metavar='i', type=str, help='delimited upload file')
    parser.add_argument(
        '--holders', type=str,
        help='optional holder upload file')
    parser.add_argument(
        '--mandatory', '-m', action='store_false',
        help="don't check for mandatory headings or values")
    args = parser.parse_args()

    ids = []
    if args.holders is not None:
        print('Parsing ', args.holders)
        h_reader = get_reader(args.holders)
        holders = []
        for rownum, row in enumerate(h_reader, 2):
            h = holder(row, rownum)
            holders.append(h.name)
        for field in h_reader.fieldnames:
            if field not in holder_heads:
                d = {'rownum': 1, 'field': field}
                logger.error(
                    'Invalid column heading: %s', field, extra=d)
        print('\n')
    print('Parsing', args.file)
    reader = get_reader(args.file)
    check_fields(reader.fieldnames, mandatory=args.mandatory)
    for rownum, row in enumerate(reader, 2):
        try:
            r = record(row, rownum, mandatory=args.mandatory)
            if r.ident in ids:
                d = {'rownum': r.rownum, 'field': 'EADUnitID'}
                logger.error(
                    'Duplicate EADUnitID: %s', r.ident, extra=d)
            if args.holders is not None:
                if r.location not in holders:
                    d = {
                        'rownum': r.rownum, 'field':
                        'LocCurrentLocationRef.LocHolderName'}
                    logger.error(
                        'Holder not in holder spreadsheet: %s',
                        r.location, extra=d)
            ids.append(r.ident)
        except Exception:
            pass
