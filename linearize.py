import subprocess

import cv2
import lensfunpy


class EXIFError(Exception): pass

def get_exif(path, key, numeric=False):
    """Use exiftool to retrieve EXIF values from an image."""
    args = ['exiftool', '-' + key, path]
    if numeric:
        args.insert(1, '-n')
    output = subprocess.check_output(args).strip()
    if ':' not in output:
        raise EXIFError("%s has no EXIF data for %s" % (path, key))
    return output.split(':')[1].strip()


def get_cam_lens(path, lfdb):
    """Get camera and lens models from EXIF and look them up in the Lensfun DB."""
    cam_maker = get_exif(path, 'Make')
    cam_model = get_exif(path, 'Model')
    lens_maker = get_exif(path, 'LensID').split()[0]
    lens_model = '%s %s' % (lens_maker, get_exif(path, 'LensModel'))
    if lens_maker == 'Canon' and 'EF' in lens_model and 'EF ' not in lens_model:
        lens_model = lens_model.replace('EF', 'EF ')

    cams = lfdb.find_cameras(cam_maker, cam_model)
    if not cams:
        raise EXIFError("Camera %r made by %r not found in lensfun" % (cam_model, cam_maker))
    cam = cams[0]
    lenses = lfdb.find_lenses(cam, lens_maker, lens_model)
    if not lenses:
        raise EXIFError("Lens %r made by %r not found in lensfun" % (lens_model, lens_maker))
    return (cam, lenses[0])


def get_modifier(path, lfdb):
    """Construct a modifier from a Lensfun DB, based on EXIF data."""
    (cam, lens) = get_cam_lens(path, lfdb)
    (width, height) = map(int, get_exif(path, 'ImageSize').split('x'))
    return lensfunpy.Modifier(lens, cam.crop_factor, width, height)


def get_map_coords(path, distance=10):
    """Initialize a Lensfun modifier with a subject distance (in meters)
    and return its geometry map for undoing distortion."""
    db = lensfunpy.Database()
    mod = get_modifier(path, db)

    focal_length = float(get_exif('FocalLength', path, numeric=True))
    aperture = float(get_exif('Aperture', path, numeric=True))

    mod.initialize(focal_length, aperture, distance)
    return mod.apply_geometry_distortion()


if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Use lensfun to fix lens distortion.")
    parser.add_argument('src')
    parser.add_argument('dst')
    parser.add_argument('--exif-src', help="path to file with original EXIF data")
    args = parser.parse_args()

    try:
        undist_coords = get_map_coords(args.exif_src or args.src, distance=10)
    except EXIFError as e:
        sys.exit(e.message)

    im = cv2.imread(args.src)
    im_undistorted = cv2.remap(im, undist_coords, None, cv2.INTER_LANCZOS4)
    cv2.imwrite(args.dst, im_undistorted)
