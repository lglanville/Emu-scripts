import pyodbc
import re
import subprocess
import sys
import os
from concurrent.futures import ThreadPoolExecutor

def id_transform(number):
    r = re.split(r'[,_.-]', number)
    if len(r[1]) < 4:
        pre = 4-len(r[1])
        r[1] = '0'*pre+r[1]
    if len(r[2]) < 5:
        pre = 5-len(r[2])
        r[2] = '0'*pre+r[2]
    return('.'.join(r))


def embed(fpath, record):
    print('Embedding meta in ', fpath)
    subprocess.run([
        "exiftool", f"-Title={record.EADUnitTitle}",
        "-overwrite_original",
        f"-Identifier=UMA:{record.EADUnitID}",
        f"-Description={record.EADScopeAndContent}",
        f"-Coverage={record.EADUnitDate}",
        f"-usageterms={record.EADUseRestrictions}"
        "CollectionName={University of Melbourne Archives,CollectionURI=http://archives.unimelb.edu.au/}",
        fpath])


def main(directory):
    c = pyodbc.connect('DSN=Emu Catalogue', autocommit=True)
    cursor = c.cursor()
    id = re.compile(r'\d{4}[,_.-]\d{2,4}[,_.-]\d{1,5}')
    with ThreadPoolExecutor() as ex:
        for root, _, files in os.walk(sys.argv[1]):
            for file in files:
                ident = id.findall(file)
                if len(ident) == 1:
                    fpath = os.path.join(root, file)
                    unitid = id_transform(ident[0])
                    q = f"select * from ecatalog.csv as c where c.EADUnitID='{unitid}'"
                    cursor.execute(q)
                    record = cursor.fetchone()
                    if record is not None:
                        ex.submit(embed, *(fpath, record))
