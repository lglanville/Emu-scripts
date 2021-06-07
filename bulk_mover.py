from pathlib import Path
import os
import re
import shutil
import subprocess
import argparse

def id_transform(number):
    idents = re.findall(r'(\d{4})[,_.-](\d{2,4})[,_.-](\d{1,5})', number)
    if len(idents) == 1:
        pre = idents[0][0]
        mid = '0' * (4 - len(idents[0][1])) + idents[0][1]
        suf = '0' * (5 - len(idents[0][2])) + idents[0][2]
        identifier = pre + '.' + mid + '.' + suf
        return identifier


def create_jpeg(fpath, outdir):
    fpath = Path(fpath)
    outfile = Path(outdir, fpath.stem+'.jpg')
    if not outfile.exists():
        subprocess.run(
            [
                'magick', 'convert', str(fpath), '-resize', '2048x2048^>',
                '-quality', '65', '-depth', '8', '-unsharp',
                '1.5x1+0.7+0.02', str(outfile)])
    return outfile


def move_image(fpath, base_dir, ident):
    fpath = Path(fpath)
    newpath = Path(base_dir, *ident.split('.'), fpath.suffix.upper().strip('.'))
    if not newpath.exists():
        newpath.mkdir(parents=True)
    page = 1
    new_fname = '-'.join(ident.split('.'))+'-'+'0'*(5-len(str(page)))+str(page)+fpath.suffix
    new_dest = newpath / new_fname
    while new_dest.exists():
        page += 1
        new_fname = '-'.join(ident.split('.'))+'-'+'0'*(5-len(str(page)))+str(page)+fpath.suffix
        new_dest = newpath / new_fname
    shutil.copy2(fpath, new_dest)
    print(fpath.name, '->', new_fname)
    return new_dest


def main(image_dir, dest_dir, exts=['.tif', '.tiff'], jpeg_dir=None):
    for root, _, files in os.walk(image_dir):
        for file in files:
            id = id_transform(file)
            if id is not None:
                fpath = Path(root, file)
                if fpath.suffix.lower() in exts:
                    new_image = move_image(fpath, dest_dir, id)
                    if jpeg_dir is not None:
                        create_jpeg(new_image, jpeg_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Moves an image file into the UMA DAMstore and optionally'
        'creates an access JPEG')
    parser.add_argument('indir', metavar='i', help='base directory for files to be restructured')
    parser.add_argument(
        'outdir', metavar='o', help='base directory for restructured files')
    parser.add_argument(
        '--jpeg', '-j',
        help='optional directory for jpegs')
    parser.add_argument(
        '--extensions', '-e', nargs='+', default=['.tif', '.tiff'],
        help='extensions of files to be restructured')
    args = parser.parse_args()


    main(args.indir, args.outdir, exts=args.extensions, jpeg_dir=args.jpeg)
