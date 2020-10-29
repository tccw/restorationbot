import time
import pickle
import string
import praw
import common

from pathlib import Path
from googleapiclient import discovery
from google.cloud import storage
from config import ZONE, PROJECT_NAME, VM_NAME, FAMILIAR_WORDS, BOT_NAME, FILETYPE_SET, SUBREDDIT
from CustomExceptions import *

# Constants
LONG_SIDE_NO_SCRATCH = 1024
LONG_SIDE_SCRATCH = 500


class RedditBot:
    """
    A container for a praw Reddit object
    """

    def __init__(self, bot_name=BOT_NAME, sub=SUBREDDIT):
        self.reddit = praw.Reddit(bot_name)
        self.subreddit = self.reddit.subreddit(sub)
        self.submissions = {}

    def monitor_comments(self) -> None:
        for comment in praw.helpers.comment_stream(self.reddit, self.subreddit.display_name):
            if self._check_comment_condition(comment):
                self._bot_action_comment(comment)

    def process_queue_len(self) -> int:
        return len(self.submissions)

    # TODO: mark a post as read/viewed if replied. Then add this as a check to _valid_title_and_image()
    def monitor_posts(self) -> None:
        for submission in self.subreddit.hot(limit=10):
            if self._valid_title_and_image(submission):
                self.submissions[submission.id] = submission

    @staticmethod
    def _check_comment_condition(comment: 'praw Comment'):
        # comment.reply()
        pass  # stub

    @staticmethod
    def _bot_action_comment(comment: 'praw Comment'):
        pass  # stub

    def reply_all_subs(self, imgur_client):
        self._bot_reply_submissions(imgur_client)

    def _bot_reply_submissions(self, client):
        upload_links = common.upload_images_imgur(client, 'processed_images', self.submissions)
        self._bot_reply_submissions_helper(upload_links)

    def _bot_reply_submissions_helper(self, links: {}):
        if len(links) == 0:
            return
        else:
            try:
                k = next(iter(links.keys()))
                comment = common.format_comment(self.submissions[k].author.name, links[k], k)
                time.sleep(2)
                self.submissions[k].reply(comment)
                links.pop(k)
                self._bot_reply_submissions_helper(links)  # call again with 1 elem smaller dict
            except praw.errors.RateLimitExceeded as e:
                print('Sleeping for {} seconds due to over-posting.'.format(e.sleep_time))
                time.sleep(e.sleep_time)
                self._bot_reply_submissions_helper(links)  # call again with the same dict to retry posting
            except praw.errors.Forbidden as e:
                print('{} - possibly banned from {}'.format(e.code, self.subreddit))
                links.pop(next(iter(links.keys())))
                self._bot_reply_submissions_helper(links)  # call again with a 1 elem smaller dict

    @staticmethod
    def _valid_title_and_image(submission):
        title = submission.title
        try:
            url = submission.url if len({submission.url.lower()}.intersection(FILETYPE_SET)) > 0 else \
                submission.media_metadata[list(submission.media_metadata.keys())[0]]['s']['u']
        except AttributeError:
            url = submission.url

        # if (url.split('.')[-1].lower() not in FILETYPE_SET) and \
        #         (('jpg' not in url) and ('png' not in url) and ('jpeg' not in url)):
        #     return False

        if url.split('.')[-1].lower() not in FILETYPE_SET:
            return False

        title = title.translate(str.maketrans('', '', string.punctuation)).lower()  # remove english punctuation
        s = set(title.split(' '))  # O(2n)
        if len(s.intersection(FAMILIAR_WORDS)) < 2:  # want at least two of the familial or familiar words in title
            return False
        return True

    def dump_images(self, dumpdir: str):
        common.delete_dir_contents(dumpdir)
        for k, v in self.submissions.items():
            img = common.resize_from_memory(common.image_from_url(v.url), LONG_SIDE_SCRATCH)
            if img.format is None:
                extension = 'JPG'
            else:
                extension = img.format
            filename = Path(dumpdir, k + '.' + extension)
            img.save(filename)

    def print_titles(self):
        for v in self.submissions.values():
            print(v.title)


# Gcloud Resources

class Bucket:
    """
    A container for a gcloud.storage bucket with support for upload/download/removal of files
    """

    def __init__(self, bucket_name: str):
        self._storage_client = storage.Client()
        self.bucket = self._storage_client.bucket(bucket_name)
        self.bucket_name = bucket_name

    def upload_dir(self, rootdir: str):
        paths = [str(path) for path in Path(rootdir).rglob('*') if '.gitignore' not in path.stem]
        for path in paths:
            try:
                self.upload_to_bucket(source_filename=path.split('/')[-1])
            except FailedToUploadException:
                print("ERR: Failed to upload file {}".format(path))
                continue

    def download_dir(self, remote_dir: str):
        Path(remote_dir).mkdir(parents=True, exist_ok=True)
        common.delete_dir_contents(remote_dir)
        bucket_files = self.list_bucket_objects()
        for file in bucket_files:
            if file.name.startswith(remote_dir) and file.name.lower().endswith(tuple(FILETYPE_SET)):
                try:
                    self.download_from_bucket(file.name, file.name)
                except FailedToDownloadException:
                    print('ERR: Failed to download {}'.format(file))
                    continue

    def upload_to_bucket(self, data=None, to_pickle=False, source_filename=None):
        """
        Uploads a picklable file to the gcloud bucket attached to this object
        :param source_filename: name of the file to be uploaded
        :param to_pickle: boolean indicator, default is False
        :param data: Any data to be uploaded
        :return: int code 1 for success, -1 for failure
        """

        try:
            if source_filename is None:
                source_filename = 'raw_images/input_data.pkl'
            if to_pickle and data is not None:
                with open(source_filename, 'wb') as f:
                    pickle.dump(data, f)

            dest_and_src_path = str(Path('raw_images', source_filename))

            blob = self.bucket.blob(dest_and_src_path)

            blob.upload_from_filename(dest_and_src_path)
        except Exception:
            raise FailedToUploadException

    def download_from_bucket(self, dest_file_name: str, source_blob_name: str):
        try:
            blob = self.bucket.blob(source_blob_name)
            blob.download_to_filename(dest_file_name)
        except Exception:
            raise FailedToDownloadException

    # TODO should eventually clean up the processed_images directory too
    def clean_up_bucket(self) -> None:
        bucket_files = self.list_bucket_objects()
        for file in bucket_files:
            if file.name.startswith(('raw_images/', 'processed_images/')) \
                    and file.name.lower().endswith(tuple(FILETYPE_SET)):
                blob = self.bucket.blob(file.name)
                blob.delete()

    def list_bucket_objects(self) -> [str]:
        return list(self._storage_client.list_blobs(self.bucket_name))


class ComputeInstance:
    """
    A container for a gcloud compute instance with basic functionality for finding, starting, stopping,
     and deleting the instance. Does not currently support instance creation.
    """

    def __init__(self, service_name: str, version: str):
        self.compute = discovery.build(service_name, version)  # Google API resource object
        self.operation = None
        self.project = None
        self.zone = None
        self.name = None

    def get_existing_instance(self, project=PROJECT_NAME, zone=ZONE, name=VM_NAME):
        self.project = project
        self.zone = zone
        self.name = name
        self.operation = self.compute.instances().get(
            project=self.project,
            zone=self.zone,
            instance=self.name).execute()

    def status(self):
        if self.operation is None:
            return "Object has no current operation/instance."
        return self.operation['status']

    def _wait_for_operation(self) -> object:

        while self.operation is not None:
            result = self.compute.zoneOperations().get(
                project=self.project,
                zone=self.zone,
                operation=self.operation).execute()

            if result['status'] == 'DONE':
                if 'error' in result:
                    raise Exception(result['error'])
                return result

            time.sleep(1)

    def delete_instance(self) -> None:
        return self.compute.instances().delete(
            project=self.project,
            zone=self.zone,
            instance=self.name).execute()

    def stop_instance(self):
        return self.compute.instances().stop(
            project=self.project,
            zone=self.zone,
            instance=self.name).execute()

    def start_instance(self):
        if self.operation is not None and self.status() != 'RUNNING':
            self.compute.instances().start(
                project=self.project,
                zone=self.zone,
                instance=self.name).execute()
