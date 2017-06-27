import os
import tempfile
import logging
import luigi

from git import Repo

logging.basicConfig(
    level=logging.INFO,
    format='[%(name)s] %(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

clone_logger = logging.getLogger('clone')


class CloneRepo(luigi.Task):
    repo_name = luigi.Parameter()                    # REPOSITORY
    repo_owner = luigi.Parameter()                   # OWNER
    branch = luigi.Parameter()                       # BRANCH
    github_token = luigi.Parameter(default='git',    # GITHUB_TOKEN
                                   significant=False)  # keep out of signature
    repo_base_url = luigi.Parameter(default='github.com')
    clone_dir = luigi.Parameter(default='')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.clone_dir:
            self.clone_dir = tempfile.mkdtemp()

        self.output_path = os.path.join(self.clone_dir, 'site_repo')

    def output(self):
        return luigi.LocalTarget(self.output_path)

    @property
    def repo_url(self):
        return (f'https://{self.github_token}@{self.repo_base_url}'
                f'/{self.repo_owner}/{self.repo_name}.git')

    def run(self):
        clone_logger.info(f'Cloning {self.repo_owner}/{self.repo_name}'
                          f' to {self.output_path}')
        Repo.clone_from(self.repo_url, self.output_path, branch=self.branch)


class CloneTemplateRepo(CloneRepo):
    # Expects that the destination repo exists
    # (it's created by federalist web)

    template_repo_name = luigi.Parameter()   # SOURCE_REPO
    template_repo_owner = luigi.Parameter()  # SOURCE_OWNER

    @property
    def template_repo_url(self):
        return (f'https://{self.github_token}@{self.repo_base_url}'
                f'/{self.template_repo_owner}'
                f'/{self.template_repo_name}.git')

    def run(self):
        # First clone the template repo
        clone_logger.info(
            f'Cloning template {self.template_repo_owner}/'
            f'{self.template_repo_name}'
            f' to {self.output_path}')

        repo = Repo.clone_from(self.template_repo_url,
                               self.output_path,
                               branch=self.branch)  # TODO: needed?

        # Then push to the destination repo
        destination = repo.create_remote('destination', self.repo_url)
        clone_logger.info(
            f'Pushing site to {self.repo_owner}/{self.repo_name}')
        repo.git.push(destination, self.branch)
