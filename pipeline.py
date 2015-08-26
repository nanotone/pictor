import os.path
import subprocess
import sys

orig_path = None
dst_dir = 'tmp'
pictor = ''

exiftool = True
try:
    subprocess.check_call(['exiftool', '-ver'])
except subprocess.CalledProcessError:
    exiftool = False
    print "WARNING: exiftool not found"


def dst_path(root, suffix):
    return '%s/%s-%s' % (dst_dir, root, suffix)

def pictor_path(exe):
    return os.path.join(pictor, exe)

def check_call(*args):
    print
    print '   '.join(args)
    subprocess.check_call(args)


def make_flat(root):
    src = orig_path
    dst = dst_path(root, 'flat.png')
    if not os.path.isfile(dst):
        check_call('go', 'run', pictor_path('flat-init.go'), src, dst)
    return dst

def make_flatnorm(root):
    src = make_flat(root)
    dst = dst_path(root, 'flatnorm.png')
    if not os.path.isfile(dst):
        check_call('python', pictor_path('flat-norm.py'), src, dst)
    return dst

def make_flattened(root):
    src = make_flatnorm(root)
    dst = dst_path(root, 'flattened.png')
    if not os.path.isfile(dst):
        check_call('go', 'run', pictor_path('flat-fix.go'), orig_path, src, dst)
    return dst

def make_linear(root, png=False):
    src = make_flattened(root)
    dst = dst_path(root, 'linear.%s' % ('png' if png else 'jpg'))
    if not os.path.isfile(dst):
        if not exiftool:
            sys.exit("exiftool, which is required for linearize.py, could not be found")
        check_call('python', pictor_path('linearize.py'), src, dst)
    return dst


if __name__ == '__main__':
    import argparse
    pictor = os.path.abspath(os.path.dirname(sys.argv[0]))
    parser = argparse.ArgumentParser(description="Send images through the flattening and undistorting pipeline.")
    parser.add_argument('--dst', default='tmp', help="directory ")
    parser.add_argument('--png', action='store_true', help="output results as PNG for further processing (no EXIF)")
    parser.add_argument('src', nargs='+', help="images to process")
    args = parser.parse_args()

    for path in args.src:
        if not os.path.isfile(path):
            sys.exit("%s is not a file." % path)
    if not os.path.isdir(args.dst):
        sys.exit("%s is not a directory." % args.dst)

    dst_dir = args.dst
    for orig_path in args.src:
        (head, tail) = os.path.split(orig_path)
        (root, ext) = os.path.splitext(tail)
        dst = make_linear(root, png=args.png)
        if exiftool and not args.png:
            check_call('exiftool', '-overwrite_original', '-tagsFromFile', orig_path, dst)
