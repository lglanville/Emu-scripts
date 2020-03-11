import pyodbc
import sys
import os
import csv


def find_item(file, cursor):
    stem = os.path.splitext(file)[0].replace("'", "")
    altstem = stem.replace("-", "_")
    q = f"""
    SELECT c.EADUnitID, c.EADUnitTitle, EADUnitDate, c.EADUseRestrictions,
    m.MulIdentifier FROM ecatalog.csv AS c
    LEFT JOIN MulMulti.csv AS m on c.ecatalogue_key=m.ecatalogue_key
    WHERE m.MulIdentifier LIKE '%{stem}%'
    OR c.EADScopeAndContent LIKE '%{altstem}%'
    """
    cursor.execute(q)
    row = cursor.fetchone()
    if row is not None:
        return {
            'EADUnitID': row.EADUnitID, 'EADUnitTitle': row.EADUnitTitle,
            'EADUnitDate': row.EADUnitDate,
            'EADUseRestrictions': row.EADUseRestrictions}
    else:
        return {}


c = pyodbc.connect('DSN=Emu Catalogue', autocommit=True)
cursor = c.cursor()

rows = []
for root, _, files in os.walk(sys.argv[1]):
    for file in files:
        if file.endswith('.tif'):
            row = find_item(file, cursor)
            row['filepath'] = os.path.join(root, file)
            rows.append(row)

with open(sys.argv[2], 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
