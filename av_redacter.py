import argparse
from pathlib import Path
import subprocess
from datetime import timedelta

INPUT_SAMMA_ARGS = ['-c:v', 'libopenjpeg']
DEFAULT_OUTPUT_ARGS = [
    '-r', '25', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    '-crf', '23', '-movflags', '+faststart', '-c:a', 'aac']


def conv_to_seconds(tstring):
    'Converts a string of either a digit or a timecode into seconds.'
    'Note ffmpeg supports timecodes, but have found it kind of buggy.'
    if tstring.isdigit():
        return(int(tstring))
    else:
        h, m, s = tstring.split(':')
        t = timedelta(hours=int(h), minutes=int(m), seconds=int(s))
        return t.seconds


def get_segments(redactions):
    'Given a sequence of redactions, returns a list of tuples of timecodes of '
    'unredacted segments.'
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
    'Constructs a string for -filter_complex'
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


def redact(file, redactions, input_args=None, output_args=None, outfile=None):
    file = Path(file)
    if outfile is None:
        outfile = Path(file.parent, file.stem + '.REDACTED' + '.mp4')
    else:
        outfile = Path(outfile)
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
    print(args)
    subprocess.run(args, stdout=subprocess.PIPE)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Simple wrappper script to create a redacted mpeg4 file'
        'using ffmpeg. Requires the ffmpeg executable to be on PATH')
    parser.add_argument('input', metavar='i', help='input av file')
    parser.add_argument(
        '--redactions', '-r', nargs='+',
        help='start and end of redactions (in seconds or HH:MM:SS format)')
    parser.add_argument(
        '--output', '-o',
        help='output file. If omitted, creates new file in original directory')
    parser.add_argument(
        '--SAMMA', '-s', action='store_true',
        help='Designates that the source is a SAMMA JPEG2000/MXF file')
    parser.add_argument(
        '--crf',
        help='crf value for ffmpeg. Default is 23, lower is higher quality')

    args = parser.parse_args()
    redactions = [[conv_to_seconds(i) for i in r.split('-')] for r in args.redactions]
    if args.crf is not None:
        i = DEFAULT_OUTPUT_ARGS.index('-crf')
        DEFAULT_OUTPUT_ARGS.pop(i + 1)
        DEFAULT_OUTPUT_ARGS.insert(i + 1, args.crf)
    if args.SAMMA:
        redact(
            args.input, redactions, input_args=INPUT_SAMMA_ARGS,
            output_args=DEFAULT_OUTPUT_ARGS, outfile=args.output)
    else:
        redact(
            args.input, redactions,
            output_args=DEFAULT_OUTPUT_ARGS, outfile=args.output)
