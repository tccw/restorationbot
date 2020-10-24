from PIL import Image, ImageStat
from pathlib import Path
import itertools
import subprocess
from urllib.request import urlopen
import numpy as np
import requests


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


def image_from_url(url: str) -> Image:
    response = urlopen(url)
    return Image.open(response)


def delete_dir_contents(rootdir: Path):
    old_paths = [path for path in Path(rootdir).rglob("*") if '.gitignore' not in path.stem]
    for path in old_paths:
        path.unlink()


def format_comment(user: str, imgur_link: str, post_id: str):
    main_message = """
    Hey, /u/{}! I think that this might be a photo of one of your family members!
    
    I've done my best to restore your photo here: {}
    
    """
    survey = _survey(post_id)
    footer = "<font size = 2>(git)[https://github.com/tccw/restorationbot] |" + \
             "[how](https://github.com/microsoft/Bringing-Old-Photos-Back-to-Life)</font>"
    return main_message + survey + footer


def _survey(post_id: str) -> str:
    user = 'restoration-bot'
    return """
    Let me know how I did! \n
    [Great!]({}) | [Not so great...]({}) | [So bad you hurt my feelings!]({})
    """.format(_dm_builder(user, 'Great!', post_id),
               _dm_builder(user, 'Not so great...', post_id),
               _dm_builder(user, 'So bad you hurt my feelings!', post_id))


def _dm_builder(to_user: str, message: str, post_id: str) -> str:
    formatted_message: str = ''.join(s + '%20' for s in message.split(' '))
    base_url = 'https://np.reddit.com/message/compose/?to={}-bot&subject=ID%20{}&message='.format(to_user, post_id)
    return base_url + formatted_message
