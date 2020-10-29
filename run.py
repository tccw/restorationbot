import os

from restorationbot import ComputeInstance
from restorationbot import Bucket
from restorationbot import RedditBot
from config import BUCKET, CREDENTIALS, IMGUR_CONFIG
from imgur_python import Imgur

if __name__ == '__main__':

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS

    # initialize working objects
    imgur_client = Imgur(IMGUR_CONFIG)
    reddit = RedditBot(sub='testingground4bots')
    bucket = Bucket(BUCKET)
    gcloud = ComputeInstance('compute', 'v1')
    gcloud.get_existing_instance()

    # clean the bucket in case this didn't get done last time the script ran
    bucket.clean_up_bucket()
    # find posts and upload their images to the gcloud bucket
    print('Searching posts')
    reddit.monitor_posts()
    reddit.dump_images('raw_images')
    bucket.upload_dir('raw_images')
    print('waiting...')

    # start up the VM. This will run the startup script, copying and processing all the images
    gcloud.start_instance()
    print('waiting for status change')
    # stop the VM to save money and run the shutdown script to copy processed files to the bucket
    gcloud.stop_instance()
    # download the processed images to the local machine with verification
    bucket.download_dir('processed_images/')
    # TODO: Could always run with scratch detection and then upscale and sharpen results
    #       also try processing images in segments
    reddit.reply_all_subs(imgur_client=imgur_client)

    # clean up the raw_images folder on the bucket and
    bucket.clean_up_bucket()
