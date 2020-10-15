from GcloudInstanceOld import GcloudInstance
from RedditBot import RedditBot

reddit = RedditBot()
reddit.monitor_posts()

gcloud = GcloudInstance('compute', 'v1', 'restorationbot-credentials.json', 'reddit_objects_bucket')
# gcloud.create_instance('restorationbot', 'us-west1-b', 'k80-redditbot', 'reddit_objects_bucket')
gcloud.get_existing_instance()
gcloud.start_instance()
print('fine')
gcloud.stop_instance()
# gcloud.delete_instance()
