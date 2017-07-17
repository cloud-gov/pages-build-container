'''Clone tasks'''

import luigi

from git import Repo

from .common import BaseTask, logging

CLONE_LOGGER = logging.getLogger('clone')


class CloneSiteMain(BaseTask):
    '''
    Meta task for cloning the source repository
    '''
    def output(self):
        return luigi.LocalTarget(self.clone_dir)

    def requires(self):
        if self.template_repo_name and self.template_repo_owner:
            return CloneTemplateRepo(
                repo_name=self.repo_name, repo_owner=self.repo_owner,
                branch=self.branch, github_token=self.github_token,
                work_dir=self.work_dir,
                template_repo_owner=self.template_repo_owner,
                template_repo_name=self.template_repo_name)
        else:
            return CloneRepo(self.repo_name, self.repo_owner, self.branch,
                             self.github_token, self.work_dir)


class CloneRepo(BaseTask):
    '''
    Task to clone the source repository to a local directory
    '''
    def output(self):
        return luigi.LocalTarget(self.clone_dir)

    def run(self):
        CLONE_LOGGER.info(f'Cloning {self.repo_owner}/{self.repo_name}'
                          f' to {self.clone_dir}')
        Repo.clone_from(self.repo_url, self.clone_dir, branch=self.branch)


class CloneTemplateRepo(CloneRepo):
    '''
    Task to clone a template site repository to a local directory
    and push the clone to the new target remote repository
    '''
    # Expects that the destination repo exists
    # (it's created by the Federalist web app)
    template_repo_name = luigi.Parameter()   # SOURCE_REPO
    template_repo_owner = luigi.Parameter()  # SOURCE_OWNER

    # def output(self):
    #   inherited from CloneRepo

    def run(self):
        # First clone the template repo
        CLONE_LOGGER.info(
            f'Cloning template {self.template_repo_owner}/'
            f'{self.template_repo_name}'
            f' to {self.clone_dir}')

        repo = Repo.clone_from(self.template_repo_url,
                               self.clone_dir,
                               branch=self.branch)  # TODO: needed?

        # Then push to the destination repo
        destination = repo.create_remote('destination', self.repo_url)
        CLONE_LOGGER.info(
            f'Pushing site to {self.repo_owner}/{self.repo_name}')
        repo.git.push(destination, self.branch)
