import praw
import common

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

    # def monitor_posts(self) -> None:
    #     for submission in self.subreddit.hot(limit=150):
    #         if self._valid_title_and_image(submission.title, submission.url):
    #             self.submissions[submission.id] = self._create_dict(submission)
    #     self._bot_action_submission(self.submissions)

    def monitor_posts(self) -> None:
        for submission in self.subreddit.hot(limit=150):
            if self._valid_title_and_image(submission.title, submission.url):
                self.submissions[submission.id] = submission
        self._bot_action_submission(self.submissions)

    # @staticmethod
    # def _create_dict(submission: praw.Reddit) -> dict:
    #     return {
    #         'author': submission.author.name,
    #         'title': submission.title,
    #         'created': submission.created,
    #         'subreddit': submission.subreddit.url,
    #         'image_url': submission.url,
    #         'permalink': 'reddit.com' + submission.permalink,
    #     }

    @staticmethod
    def _check_comment_condition(comment: 'praw Comment'):
        comment.reply()
        pass  # stub

    @staticmethod
    def _bot_action_comment(comment: 'praw Comment'):
        pass  # stub

    @staticmethod
    def _bot_action_submission(valid_submissions):
        pass  # stub

    @staticmethod
    def _valid_title_and_image(title: str, url: str):

        if url.split('.')[-1].lower() not in FILETYPE_SET:
            return False

        # TODO: remove parens and other punctuation
        s = set(title.split(' '))  # O(2n)
        if len(s.intersection(FAMILIAR_WORDS)) < 2:  # want at least two of the familial or familiar words together
            return False
        return True
    #
    # def dump_images(self, dumpdir: str):
    #     self._delete_dir_contents(dumpdir)
    #     for k, v in self.to_process_dict.items():
    #         img = common.resize_from_memory(common.image_from_url(v['image_url']), DEFAULT_LONGEST_SIDE)
    #         if img.format is None:
    #             extension = 'JPG'
    #         else:
    #             extension = img.format
    #         filename = Path(dumpdir, k + '.' + extension)
    #         img.save(filename)

    def dump_images(self, dumpdir: str):
        self._delete_dir_contents(dumpdir)
        for k, v in self.submissions.items():
            img = common.resize_from_memory(common.image_from_url(v.url), DEFAULT_LONGEST_SIDE)
            if img.format is None:
                extension = 'JPG'
            else:
                extension = img.format
            filename = Path(dumpdir, k + '.' + extension)
            img.save(filename)

    @staticmethod
    def _delete_dir_contents(rootdir: Path):
        old_paths = [path for path in Path(rootdir).rglob("*") if '.gitignore' not in path.stem]
        for path in old_paths:
            path.unlink()
