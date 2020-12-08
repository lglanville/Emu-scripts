import argparse
import shutil
from pathlib import Path
import subprocess
BASEPATH = r"\\research-cifs.unimelb.edu.au\9730-UniversityArchive-Shared\Digitised_Holdings\Registered"


def jpeg(fpath, outdir):
    fpath = Path(fpath)
    outfile = Path(outdir, fpath.stem+'.jpg')
    if not outfile.exists():
        subprocess.run(
            [
                'magick', 'convert', str(fpath), '-resize', '2048x2048^>',
                '-quality', '65', '-depth', '8', '-unsharp',
                '1.5x1+0.7+0.02', str(outfile)])
    return outfile


def ident_validate(ident):
    try:
        start, mid, end = ident.split('.')
        if [len(p) for p in ident.split('.')] == [4, 4, 5]:
            if all([p.isnumeric() for p in ident.split('.')]):
                return True
            else:
                return False
        else:
            return False
    except ValueError:
        return False


def move_image(fpath, ident, page=1):
    if ident_validate(ident):
        fpath = Path(fpath)
        new_fname = '-'.join(ident.split('.'))+'-'+'0'*(5-len(str(page)))+str(page)+fpath.suffix
        newpath = Path(BASEPATH, *ident.split('.'), fpath.suffix.upper().strip('.'))
        new_dest = newpath / new_fname
        if not newpath.exists():
            newpath.mkdir(parents=True)
            shutil.copy2(fpath, new_dest)
        else:
            print(newpath, 'already exists')
    else:
        print('Invalid identifier:', ident)
    return new_dest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Moves an image file into the UMA DAMstore and optionally'
        'creates an access JPEG')
    parser.add_argument('input', metavar='i', help='csv upload file')
    parser.add_argument('identifier', metavar='o', help='converted csv file')
    parser.add_argument(
        '--jpeg', '-j',
        help='directory for jpegs')
    parser.add_argument(
        '--page', '-p', default=1, type=int,
        help='page number for multipage items')

    args = parser.parse_args()
    newpath = move_image(args.input, args.identifier, page=args.page)
    if args.jpeg is not None:
        jpeg(newpath, args.jpeg)
