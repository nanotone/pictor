import subprocess
import sys

import cv2
import lensfunpy


def get_exif(path, key, numeric=False):
    """Use exiftool to retrieve EXIF values from an image."""
    args = ['exiftool', '-' + key, path]
    if numeric:
        args.insert(1, '-n')
    output = subprocess.check_output(args).strip()
    if ':' not in output:
        raise KeyError("%s has no EXIF data for %s" % (path, key))
    return output.split(':')[1].strip()


def get_cam_lens(path, lfdb):
    """Get camera and lens models from EXIF and look them up in the Lensfun DB."""
    cam_maker = get_exif(path, 'Make')
    cam_model = get_exif(path, 'Model')
    lens_maker = get_exif(path, 'LensID').split()[0]
    lens_model = '%s %s' % (lens_maker, get_exif(path, 'LensModel'))
    if lens_maker == 'Canon' and 'EF' in lens_model and 'EF ' not in lens_model:
        lens_model = lens_model.replace('EF', 'EF ')

    cam = lfdb.find_cameras(cam_maker, cam_model)[0]
    lens = lfdb.find_lenses(cam, lens_maker, lens_model)[0]
    return (cam, lens)


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
    src_path, dst_path = sys.argv[1:]
    undist_coords = get_map_coords(src_path, distance=10)

    im = cv2.imread(src_path)
    im_undistorted = cv2.remap(im, undist_coords, None, cv2.INTER_LANCZOS4)
    cv2.imwrite(dst_path, im_undistorted)
