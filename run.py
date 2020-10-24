from GcloudInstance import GcloudInstance
from RedditBot import RedditBot
from Bucket import Bucket
from config import BUCKET, CREDENTIALS
import os
from common import _survey

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS

# initialize working objects
reddit = RedditBot()
bucket = Bucket(BUCKET)
gcloud = GcloudInstance('compute', 'v1')
gcloud.get_existing_instance()


# find posts and upload their images to the gcloud bucket
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

# clean up the raw_images folder on the bucket and
bucket.clean_up_bucket()
