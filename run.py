from GcloudInstance import GcloudInstance
from RedditBot import RedditBot
from Bucket import Bucket
from config import BUCKET, CREDENTIALS, IMGUR_CONFIG
import os
from imgur_python import Imgur

# TODO run scratch healing only if scratch detected within face bounding box

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS

# initialize working objects
imgur_client = Imgur(IMGUR_CONFIG)
reddit = RedditBot(sub='testingground4bots')
bucket = Bucket(BUCKET)
gcloud = GcloudInstance('compute', 'v1')
gcloud.get_existing_instance()



# find posts and upload their images to the gcloud bucket
reddit.monitor_posts()

reddit.dump_images('raw_images')
bucket.upload_dir('raw_images')
reddit.print_titles()
print('waiting...')


# start up the VM. This will run the startup script, copying and processing all the images
#TODO scratch detection and run restoration with scratches
gcloud.start_instance()
print('waiting for status change')
bucket.download_dir('processed_images/')
# stop the VM to save money and run the shutdown script to copy processed files to the bucket
gcloud.stop_instance()
# download the processed images to the local machine with verification
reddit.reply_all_subs(imgur_client)
# clean up the raw_images folder on the bucket and
bucket.clean_up_bucket()
