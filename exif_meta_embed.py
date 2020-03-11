import pyodbc
import re
import subprocess
import sys
import os


def id_transform(number):
    r = re.split(r'[,_.-]', number)
    if len(r[1]) < 4:
        pre = 4-len(r[1])
        r[1] = '0'*pre+r[1]
    if len(r[2]) < 5:
        pre = 5-len(r[2])
        r[2] = '0'*pre+r[2]
    return('.'.join(r))


c = pyodbc.connect('DSN=Emu Catalogue', autocommit=True)
cursor = c.cursor()
id = re.compile(r'\d{4}[,_.-]\d{2,4}[,_.-]\d{1,5}')
for root, _, files in os.walk(sys.argv[1]):
    for file in files:
        n = id.findall(file)
        if len(n) == 1:
            unitid = id_transform(n[0])
            q = f"select * from ecatalog.csv as c where c.EADUnitID='{unitid}'"
            cursor.execute(q)
            r = cursor.fetchone()
            subprocess.run([
                "exiftool", f"-Title={r.EADUnitTitle}",
                "-overwrite_original",
                f"-Identifier=UMA:{r.EADUnitID}",
                f"-Description={r.EADScopeAndContent}",
                f"-Coverage={r.EADUnitDate}",
                f"-usageterms={r.EADUseRestrictions}"
                "CollectionName={University of Melbourne Archives,CollectionURI=http://archives.unimelb.edu.au/}",
                os.path.join(root, file)])
