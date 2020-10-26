import praw
import common
import string

from pathlib import Path
from config import FAMILIAR_WORDS  # type: set
from config import BOT_NAME, SUBREDDIT, FILETYPE_SET

DEFAULT_LONGEST_SIDE = 1024


class RedditBot:

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

    def monitor_posts(self) -> None:
        for submission in self.subreddit.hot(limit=3):
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
        for k in upload_links.keys():
            try:
                comment = common.format_comment(self.submissions[k].author.name,
                                                upload_links[k], k)
                self.submissions[k].reply(comment)
            except:
                # TODO can't post exception wait for however long I need to to post again
                continue


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
            img = common.resize_from_memory(common.image_from_url(v.url), DEFAULT_LONGEST_SIDE)
            if img.format is None:
                extension = 'JPG'
            else:
                extension = img.format
            filename = Path(dumpdir, k + '.' + extension)
            img.save(filename)

    def print_titles(self):
        for v in self.submissions.values():
            print(v.title)
