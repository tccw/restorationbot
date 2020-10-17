from PIL import Image, ImageStat
from pathlib import Path
import itertools
import subprocess
from urllib.request import urlopen
import numpy as np
import io


def bash_command(command_list: [str]) -> None:
    subprocess.run(command_list)


# Thoughts
# https://stackoverflow.com/questions/20068945/detect-if-image-is-color-grayscale-or-black-and-white-with-python-pil
def is_monochrome(img: Image):
    if img.mode == 'RGB':
        rgb_pxl_medians = ImageStat.Stat(img).median
        img_arr = np.array(img)
        median_diffs = [np.sum(img_arr[i] - rgb_pxl_medians[i]) / (img.width * img.height) for i in range(3)]
        # not a strong enough discriminator


def resize_from_memory(img: Image, longest_side: int):
    if max(img.size) < longest_side:
        return img
    h, w = _new_dims(img, longest_side)
    return img.resize((h, w))


def resize_from_filepath(rootdir: str, longest_side: int):
    paths = _get_image_paths(rootdir)
    for path in paths:
        img = Image.open(path)
        if max(img.size) > longest_side:
            h, w = _new_dims(img, longest_side)
            img.resize((h, w))
            img.save(path)  # overwrite the original image


def _new_dims(img: Image, longest_side: int) -> (int, int):
    curr_h, curr_w = img.size
    resize_ratio = longest_side / max(curr_h, curr_w)
    return int(curr_h * resize_ratio), int(curr_w * resize_ratio)


def _get_image_paths(rdir: str) -> [str]:
    extensions = {'*.png', '*.jpg'}
    paths = []
    for ext in extensions:
        paths.append([str(p) for p in Path(rdir).rglob(ext)])
    return _flatten_list(paths)


def _flatten_list(ls: [[str]]) -> [str]:
    return list(itertools.chain.from_iterable(ls))


def image_from_url(url: str):
    response = urlopen(url)
    return Image.open(response)


