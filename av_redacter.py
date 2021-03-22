import argparse
from pathlib import Path
import subprocess
from datetime import timedelta

INPUT_SAMMA_ARGS = ['-c:v', 'libopenjpeg']
DEFAULT_VIDEO_ARGS = [
    '-r', '25', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    '-crf', '23', '-movflags', '+faststart', '-c:a', 'aac']
DEFAULT_AUDIO_ARGS = ['-c:a', 'libmp3lame', '-qscale:a', '2']


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


def get_filter_args(segments, video=True):
    'Constructs a string for -filter_complex'
    args = ''
    seg_num = 0
    for start, end in segments:
        seg_num += 1
        if end is not None:
            if video:
                args += f'[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,format=yuv420p[{seg_num}v];'
            args += f'[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[{seg_num}a];'
        else:
            if video:
                args += f'[0:v]trim=start={start},setpts=PTS-STARTPTS,format=yuv420p[{seg_num}v];'
            args += f'[0:a]atrim=start={start},asetpts=PTS-STARTPTS[{seg_num}a];'
    for x in range(1, seg_num+1):
        if video:
            args += f'[{x}v][{x}a]'
        else:
            args += f'[{x}a]'
    if video:
        args += f'concat=n={seg_num}:v=1:a=1[outv][outa]'
    else:
        args += f'concat=n={seg_num}:v=0:a=1[outa]'
    return args


def make_access_file(file, redactions=None, input_args=None, output_args=None, outfile=None, video=True):
    file = Path(file)
    if video:
        ext = '.mp4'
    else:
        ext = '.mp3'
    if outfile is None:
        outfile = Path(file.parent, file.stem + '.access' + ext)
    else:
        outfile = Path(outfile)
    if outfile.exists():
        outfile.unlink()
    args = ['ffmpeg', '-i', str(file), str(outfile)]
    if redactions is not None:
        segments = get_segments(redactions)
        filter = get_filter_args(segments, video=video)
        if video:
            filter_args = [
                '-filter_complex', filter, '-map', '[outv]', '-map', '[outa]']
        else:
            filter_args = [
                '-filter_complex', filter, '-map', '[outa]']
        i = args.index(str(outfile))
        args[i:i] = filter_args
    if input_args is not None:
        i = args.index('-i')
        args[i:i] = input_args
    if output_args is not None:
        i = args.index(str(outfile))
        args[i:i] = output_args
    print(args)
    subprocess.run(args, stdout=subprocess.PIPE)


def main(file, redactions=None, crf=None, output_args=None, outfile=None):
    file = Path(file)
    if file.suffix in ('.mp3', '.wav'):
        video = False
        args = DEFAULT_AUDIO_ARGS
    else:
        video = True
        args = DEFAULT_VIDEO_ARGS
    if redactions is not None:
        redactions = [[conv_to_seconds(i) for i in r.split('-')] for r in redactions]
    if crf is not None:
        i = DEFAULT_VIDEO_ARGS.index('-crf')
        DEFAULT_VIDEO_ARGS[i + 1] = crf
    if file.suffix == '.mxf':
        make_access_file(
            file, redactions=redactions, input_args=INPUT_SAMMA_ARGS,
            output_args=DEFAULT_VIDEO_ARGS, outfile=outfile)
    else:
        make_access_file(
            file, redactions=redactions,
            output_args=args, outfile=outfile, video=video)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Simple wrappper script to create a redacted mpeg4 or mp3'
        ' file using ffmpeg. Requires the ffmpeg executable to be on PATH')
    parser.add_argument('input', metavar='i', help='input av file')
    parser.add_argument(
        '--redactions', '-r', nargs='+',
        help='start and end of any redactions (in seconds or HH:MM:SS format)')
    parser.add_argument(
        '--output', '-o',
        help='output file. If omitted, creates new file in original directory')
    parser.add_argument(
        '--crf',
        help='crf value for ffmpeg. Default is 23, lower is higher quality')

    args = parser.parse_args()
    main(
        args.input, redactions=args.redactions,
        crf=args.crf, outfile=args.output)
