import bagit
import sys
import pyodbc
import os


def removebreaks(field, sep):
    if field is not None:
        return field.replace('\n', sep)


def datasplit(field):
    data = {}
    if field is not None:
        for line in field.splitlines():
            if ':' in line:
                k, v = line.split(':', maxsplit=1)
                if v.strip() != '':
                    data[k.strip()] = v.strip()
    return data


conn = pyodbc.connect('DSN=EMu Catalogue', autocommit=True)
cursor = conn.cursor()
for root, _, files in os.walk(sys.argv[1]):
    if 'bagit.txt' in files:
        b = bagit.Bag(root)
        query = f"""
        select * from ecatalog.csv AS c
        LEFT JOIN EADOrigi.csv AS p ON c.ecatalogue_key = p.ecatalogue_key
        WHERE c.EADUnitID='{b.info.get('identifier')}';
        """
        cursor.execute(query)
        data = cursor.fetchone()
        if data is not None:
            datadict = {
                'title': data.EADUnitTitle,
                'date': data.EADUnitDate,
                'parent identifier': data.parentid,
                'copyright': data.EADUseRestrictions,
                'access': data.EADUseRestrictions,
                'creator': data.NamFullName,
                'description': removebreaks(data.EADScopeAndContent, ' '),
                'carrier': removebreaks(data.EADGenreForm_tab, ' | '),
                'original carrier': removebreaks(data.pgenreform, ' | ')}
            notesdata = datasplit(data.NotNotes)
            datadict = {k: v for k, v in datadict.items() if v is not None}
            datadict.update(notesdata)
            b.info.update(datadict)
            if b.info.get('carrier') is not None:
                b.info.pop('carrier')
            print(b.info)
            b.save()
