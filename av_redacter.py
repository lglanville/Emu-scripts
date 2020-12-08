import argparse
from pathlib import Path
import subprocess


def redact_complex(file, beginning, end):
    file = Path(file)
    outfile = Path(file.parent, file.stem + '.REDACTED' + file.suffix)
    if outfile.exists():
        outfile.unlink()
    sp = subprocess.run([
        'ffmpeg', '-i', str(file), '-filter_complex',
        f'[0:v]trim=duration={beginning}[av];[0:a]atrim=duration={beginning}[aa];'
        f'[0:v]trim=start={end},setpts=PTS-STARTPTS[bv];'
        f'[0:a]atrim=start={end},asetpts=PTS-STARTPTS[ba];'
        '[av][bv]concat[outv];[aa][ba]concat=v=0:a=1[outa]',
        '-map', '[outv]', '-map', '[outa]', str(outfile)], stdout=subprocess.PIPE)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Simple wrappper script to redact a section from an AV '
        'file using ffmpeg. Requires the ffmpeg executable to be on PATH')
    parser.add_argument('input', metavar='i', help='input av file')
    parser.add_argument(
        '--start', '-s',
        help='start of redaction (in seconds or HH:MM:SS.xxx format)')
    parser.add_argument(
        '--end', '-e',
        help='end of redaction (in seconds or HH:MM:SS.xxx format)')

    args = parser.parse_args()
    redact_complex(args.input, args.start, args.end)
