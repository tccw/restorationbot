from GcloudInstance import GcloudInstance
from RedditBot import RedditBot
from config import BUCKET, CREDENTIALS

# initialize working objects
reddit = RedditBot()

gcloud = GcloudInstance('compute', 'v1', CREDENTIALS, BUCKET)
gcloud.get_existing_instance()


# find posts and upload their images to the gcloud bucket
reddit.monitor_posts()
reddit.dump_images('tmp_input')
gcloud.upload_dir('tmp_input')

# start up the VM. This will run the startup script, copying and processing all the images
gcloud.start_instance()

# stop the VM to save money and run the shutdown script to copy processed files to the bucket
gcloud.stop_instance()
# download the processed images to the local machine with verification
gcloud.download_from_bucket()

# clean up the tmp_input folder on the bucket and
gcloud.clean_up_bucket()
