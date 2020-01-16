import sys
import csv


def get_reader(path):
    f = open(path, encoding='utf-8')
    reader = csv.DictReader(f)
    return(reader)


def split_fields(row, fieldname, heads):
    if row.get(fieldname) is not None:
        subjects = row.pop(fieldname).strip().splitlines()
        sub_heads = [f'{fieldname}({x})' for x in range(1, len(subjects)+1)]
        for head in sub_heads:
            if head not in heads:
                heads.append(head)
        subjects = dict(zip(sub_heads, subjects))
        row.update(subjects)
    return row, heads


reader = get_reader(sys.argv[1])
data = {'headings': reader.fieldnames, 'rows': []}
fields = [
    'EADSubject_tab', 'EADName_tab', 'EADGeographicName_tab',
    'EADLanguageOfMaterial_tab', 'EADLanguageCodeOfMaterial_tab']
for row in reader:
    for field in fields:
        row, heads = split_fields(row, field, data['headings'])
        data['headings'] = heads
    data['rows'].append(row)
for field in fields:
    if field in data['headings']:
        data['headings'].remove(field)
with open(sys.argv[2], 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, data['headings'])
    writer.writeheader()
    writer.writerows(data['rows'])
