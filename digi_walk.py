import os
import csv
import argparse
import re

parser = argparse.ArgumentParser(
    description='Generate or update EMu upload csv for digital surrogates')
parser.add_argument(
    'directory', metavar='i', type=str, nargs='+',
    help='the base directory for the surrogates')
parser.add_argument(
    '--csv', dest='csvfile', required=True,
    help='output csv file or an existing EMu csv upload file without'
    'multimedia columns')
parser.add_argument(
    '--ext', dest='extension', required=True, nargs='+',
    help='file extension with dot of the surrogates for upload')
parser.add_argument(
    '--pub', dest='publish', default='no', choices=['yes', 'no'],
    help='whether the surrogates should be published to the web'
    '(default is no)')
parser.add_argument(
    '--unmatched', dest='unmatched', default=False,
    action='store_true',
    help='add additional matched items to the spreadsheet')

fields = [
    'ObjectType', 'EADLevelAttribute', 'EADUnitID',
    'AssParentObjectRef.EADUnitID',	'LocCurrentLocationRef.LocHolderName',
    'EADUnitTitle', 'EADUnitDate', 'EADUnitDateEarliest',
    'EADUnitDateLatest', 'EADScopeAndContent', 'AssRelatedPartiesRef_tab.irn',
    'EADUseRestrictions']


class item():
    def __init__(self, number):
        p = re.findall(r'\d{4}[,_.-]\d{2,4}[,_.-]\d{1,5}', number)
        if p == []:
            return(None)
        else:
            self.item_number = self.id_transform(p[0])
            n = [str(int(i)) for i in self.item_number.split('.')]
            self.pattern = re.compile(r"[,_.-]0*".join(n)+r'\D+')
            if os.path.exists(number):
                self.surrogates = [os.path.abspath(number)]
            else:
                self.surrogates = []

    def __repr__(self):
        if hasattr(self, 'item_number'):
            return("<item {}>".format(self.item_number))
        else:
            return("<empty item>")

    def id_transform(self, number):
        r = re.split(r'[,_.-]', number)
        if len(r[1]) < 4:
            pre = 4-len(r[1])
            r[1] = '0'*pre+r[1]
        if len(r[2]) < 5:
            pre = 5-len(r[2])
            r[2] = '0'*pre+r[2]
        return('.'.join(r))

    def match(self, filepath):
        s = self.pattern.findall(filepath)
        if len(s) > 0 and os.path.abspath(filepath) not in self.surrogates:
            self.surrogates.append(os.path.abspath(filepath))
            return(1)
        else:
            return(0)


def add_fields(i, row):
    for x, v in enumerate(i.surrogates, start=1):
        newfields = {
            'MulMultiMediaRef_tab({}).Multimedia'.format(x): v,
            'MulMultiMediaRef_tab({}).DetResourceType'.format(x): '',
            'MulMultiMediaRef_tab({}).DetSource'.format(x): i.item_number,
            'MulMultiMediaRef_tab({}).AdmPublishWebNoPassword'.format(x):
            args.publish}
        for field in newfields.keys():
            if field not in fields:
                fields.append(field)
        row.update(newfields)


def list_items(directory, ext):
    item_list = {}
    file_list = []
    for root, dirs, files in os.walk(directory):
        file_list.extend([
            os.path.join(root, file) for file in files
            if os.path.splitext(file)[1] in ext])
    for file in file_list:
        i = item(file)
        if i.item_number not in item_list.keys():
            item_list.update({i.item_number: i})
        else:
            item_list[i.item_number].match(file)
    return(item_list)


def write_csv(rows, fields):
    with open(args.csvfile, 'w', newline='') as e:
        writer = csv.DictWriter(e, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


if __name__ == '__main__':
    args = parser.parse_args()
    items = {}
    for dir in args.directory:
        items.update(list_items(dir, args.extension))
    if os.path.exists(args.csvfile):
        with open(args.csvfile, newline='') as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames
            rows = []
            for row in reader:
                if row['EADUnitID'] in items.keys():
                    add_fields(items.pop(row['EADUnitID']), row)
                    rows.append(row)
        if items != {}:
            print('Unmatched files:')
            for k, v in items.items():
                print(k)
                print(", ".join(v.surrogates))
        write_csv(rows)
    else:
        rows = []
        for k, v in items.items():
            row = {'EADUnitID': k}
            add_fields(v, row)
            rows.append(row)
        write_csv(rows, fields)
