'''Entry point for running build pipeline'''

import os
import shutil
import luigi

import tasks
from tasks.common import logging

# TODO:
#  Maybe just have three main tasks: Publish, Build, Clone
#  and each of those will have an output target:
#   - Clone: local repo directory
#   - Build: _site directory
#   - Publish: files in S3

# Then, do all the internal logic as plain ole functions called from run()
# methods to simplify all these dang tasks

# Eg: CloneTask's run(self):
#     if template_repo and template_name:
#       cloneRepo(template_owner, template_name,...)
#       pushToRemote(repo_owner, repo_name, ...)
#     else:
#       cloneRepo(repo_owner, repo_name, ...)
#

# TODO: change to whatever the final task in the chain is
MAIN_TASK = tasks.BuildSiteMain
# MAIN_TASK = tasks.CloneSiteMain
# MAIN_TASK = tasks.CloneRepo


MAIN_LOGGER = logging.getLogger('main')

class RunAll(tasks.BaseTask):
    '''
    Dummy task that triggers execution of a other tasks

    PYTHONPATH='.' luigi --module main RunAll --repo-owner jseppi \
        --repo-name test-federalist-site --branch master --local-scheduler
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if os.path.exists(self.work_dir):
            MAIN_LOGGER.info(f'Removing {self.clone_dir} and {self.built_site_dir} before starting pipeline')
            shutil.rmtree(self.clone_dir, ignore_errors=True)
            shutil.rmtree(self.built_site_dir, ignore_errors=True)

    def requires(self):
        return MAIN_TASK(
            repo_name=self.repo_name, repo_owner=self.repo_owner, branch=self.branch,
            work_dir=self.work_dir, github_token=self.github_token,
            build_engine=self.build_engine,
            template_repo_name=self.template_repo_name,
            template_repo_owner=self.template_repo_owner,
            base_url=self.base_url)
