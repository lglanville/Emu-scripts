import argparse
import csv


def get_reader(path):
    f = open(path, encoding='utf-8')
    reader = csv.DictReader(f)
    return(reader)


def split_fields(row, fieldname, heads, delimiter=None):
    if row.get(fieldname) is not None:
        subjects = row.pop(fieldname).strip().splitlines()
        if delimiter is not None:
            for sub in subjects:
                new_subs = [s.strip('.') for s in sub.split(delimiter)]
                subjects.remove(sub)
                subjects.extend(new_subs)
        sub_heads = [f'{fieldname}({x})' for x in range(1, len(subjects)+1)]
        for head in sub_heads:
            if head not in heads:
                heads.append(head)
        subjects = dict(zip(sub_heads, subjects))
        row.update(subjects)
    return row, heads


def main(in_csv, out_csv, delimiter=None):
    reader = get_reader(in_csv)
    data = {'headings': reader.fieldnames, 'rows': []}
    fields = [f for f in reader.fieldnames if f.endswith('_tab')]
    for row in reader:
        for field in fields:
            row, heads = split_fields(
                row, field, data['headings'], delimiter=delimiter)
            data['headings'] = heads
        data['rows'].append(row)
    for field in fields:
        if field in data['headings']:
            data['headings'].remove(field)
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, data['headings'])
        writer.writeheader()
        writer.writerows(data['rows'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Split multi-value fields in Emu uplaod sheets')
    parser.add_argument('input', metavar='i', help='csv upload file')
    parser.add_argument('output', metavar='o', help='converted csv file')
    parser.add_argument(
        '--delimiter', '-d',
        help='delimiter for values. Script will always split on new lines,'
        'but if a character is specified here it will '
        'also split on that character')

    args = parser.parse_args()
    main(args.input, args.output, delimiter=args.delimiter)
