import sys

from PIL import Image
from PIL import ImageFilter

src_path, dst_path = sys.argv[1:]

im = Image.open(src_path)
size = (5472, 3648)
if im.size != size:
    im = im.resize(size, resample=Image.BILINEAR)

im.filter(ImageFilter.GaussianBlur(radius=200)).save(dst_path)
