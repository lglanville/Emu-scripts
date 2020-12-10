import argparse
from pathlib import Path
import subprocess
from datetime import timedelta


def conv_to_seconds(tstring):
    if tstring.isdigit():
        return(int(tstring))
    else:
        h, m, s = tstring.split(':')
        t = timedelta(hours=int(h), minutes=int(m), seconds=int(s))
        return t.seconds


def get_segments(redactions):
    redactions.sort()
    segments = []
    start = 0
    for rstart, rend in redactions:
        segment = (start, rstart)
        if segment != (0, 0):
            segments.append(segment)
        start = rend
    segments.append((start, None))
    return segments


def get_filter_args(segments):
    args = ''
    seg_num = 0
    for start, end in segments:
        seg_num += 1
        if end is not None:
            args += f'[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,format=yuv420p[{seg_num}v];'
            args += f'[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[{seg_num}a];'
        else:
            args += f'[0:v]trim=start={start},setpts=PTS-STARTPTS,format=yuv420p[{seg_num}v];'
            args += f'[0:a]atrim=start={start},asetpts=PTS-STARTPTS[{seg_num}a];'
    for x in range(1, seg_num+1):
        args += f'[{x}v][{x}a]'
    args += f'concat=n={seg_num}:v=1:a=1[outv][outa]'
    return args


def redact(file, redactions, input_args=None, output_args=None):
    file = Path(file)
    outfile = Path(file.parent, file.stem + '.REDACTED' + file.suffix)
    if outfile.exists():
        outfile.unlink()
    segments = get_segments(redactions)
    filter_args = get_filter_args(segments)
    args = [
        'ffmpeg', '-i', str(file), '-filter_complex',
        filter_args,
        '-map', '[outv]', '-map', '[outa]', str(outfile)]
    if input_args is not None:
        for arg in input_args:
            i = args.index('-i')
            args.insert(i, arg)
    if output_args is not None:
        for arg in input_args:
            i = args.index(str(outfile))
            args.insert(i, arg)
    sp = subprocess.run(args, stdout=subprocess.PIPE)
    print(sp.args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Simple wrappper script to redact a section from an AV '
        'file using ffmpeg. Requires the ffmpeg executable to be on PATH')
    parser.add_argument('input', metavar='i', help='input av file')
    parser.add_argument(
        '--redactions', '-r', nargs='+',
        help='start and end of redactions (in seconds or HH:MM:SS format)')
    parser.add_argument(
        '--inputargs', '-ia', nargs='+',
        help='additional input parameters for ffmpeg')
    parser.add_argument(
        '--outputargs', '-oa', nargs='+',
        help='additional output parameters for ffmpeg')

    args = parser.parse_args()
    redactions = [[conv_to_seconds(i) for i in r.split('-')] for r in args.redactions]
    redact(args.input, redactions, input_args=args.inputargs, output_args=args.outputargs)
