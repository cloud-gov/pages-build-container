import logging
import os
import luigi

from colorlog import ColoredFormatter

REPO_BASE_URL = 'github.com'
BUILT_SITE_DIR_NAME = '_site'
CLONE_DIR_NAME = 'clone'


formatter = ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(reset)s %(blue)s[%(name)s]%(reset)s "
    "%(asctime)s %(levelname)-8s %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)
root = logging.getLogger()
root.setLevel(os.environ.get('LOGLEVEL', logging.INFO))
root.addHandler(handler)


class BaseTask(luigi.Task):
    # Required parameters
    repo_name = luigi.Parameter()                       # REPOSITORY
    repo_owner = luigi.Parameter()                      # OWNER
    branch = luigi.Parameter()                          # BRANCH
    work_dir = luigi.Parameter(significant=False)

    # Optional parameters
    base_url = luigi.Parameter(default="''",            # BASE_URL
                               significant=False)
    build_engine = luigi.Parameter(default='copy')
    github_token = luigi.Parameter(default='git',       # GITHUB_TOKEN
                                   significant=False)   # keep out of signature
    template_repo_name = luigi.Parameter(default='')   # SOURCE_REPO
    template_repo_owner = luigi.Parameter(default='')  # SOURCE_OWNER

    @property
    def repo_url(self):
        return (f'https://{self.github_token}@{REPO_BASE_URL}/'
                f'{self.repo_owner}/{self.repo_name}.git')

    @property
    def template_repo_url(self):
        return (f'https://{self.github_token}@{REPO_BASE_URL}/'
                f'{self.template_repo_owner}/{self.template_repo_name}.git')

    @property
    def repo_work_dir(self):
        return os.path.join(self.work_dir, self.repo_owner, self.repo_name)

    @property
    def clone_dir(self):
        return os.path.join(self.repo_work_dir, CLONE_DIR_NAME)

    @property
    def built_site_dir(self):
        return os.path.join(self.repo_work_dir, BUILT_SITE_DIR_NAME)
