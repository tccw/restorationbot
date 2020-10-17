from GcloudInstance import GcloudInstance
from RedditBot import RedditBot
from config import BUCKET, CREDENTIALS

reddit = RedditBot()
reddit.monitor_posts()

gcloud = GcloudInstance('compute', 'v1', CREDENTIALS, BUCKET)
gcloud.get_existing_instance()
gcloud.start_instance()
gcloud.upload_file(reddit.to_process_dict)
print('fine')
gcloud.stop_instance()

