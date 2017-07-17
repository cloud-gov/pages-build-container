'''Build tasks'''

import os
import shutil
import subprocess

import luigi

from .common import BaseTask, logging
from .clone import CloneSiteMain

AVAILABLE_BUILD_ENGINES = ['hugo', 'jekyll', 'copy']

RVM_PATH = '/usr/local/rvm/scripts/rvm'
RUBY_VERSION_FILE = '.ruby-version'  # TODO: the path is in the clone dir
NVM_PATH = '$NVM_DIR/nvm.sh'  # TODO: will subprocess.call expand the env var?
NVMRC_FILE = '.nvmrc'  # TODO: the path is in the clone dir

BUILD_LOGGER = logging.getLogger('build')


class BuildSiteMain(BaseTask):
    '''
    Meta task to build the source repository site.
    '''
    # "Parent" task
    # - Delete _site if it exists in cloned repo (do in sub-tasks)
    # - Init RVM
    # - Install ruby version if .ruby-version is present
    # - Initialize NVM
    # - Install node version from .nvmrc if it is present
    # - If package.json, install deps and `run npm run federalist`
    # - Run build-engine-specific task
    build_engine = luigi.Parameter(default='copy')

    def output(self):
        return luigi.LocalTarget(self.built_site_dir)

    def requires(self):
        # if self.build_engine not in AVAILABLE_BUILD_ENGINES:
        #    raise ValueError(f'Unsupported build engine: {self.build_engine}')
        return CloneSiteMain(
            repo_name=self.repo_name, repo_owner=self.repo_owner,
            branch=self.branch, github_token=self.github_token,
            work_dir=self.work_dir,
            template_repo_owner=self.template_repo_owner,
            template_repo_name=self.template_repo_name)

    def run(self):
        BUILD_LOGGER.info('Initializing RVM')
        subprocess.call('source /usr/local/rvm/scripts/rvm', shell=True)

        BUILD_LOGGER.info(f'$PATH: {os.getenv("PATH", "")}')

        BUILD_LOGGER.info(f'Build engine is: {self.build_engine}')
        if self.build_engine is 'copy':
            yield BuildCopySite(self.repo_name, self.repo_owner, self.branch,
                                self.github_token, self.work_dir)
        elif self.build_engine is 'jekyll':
            yield BuildJekyllSite()
        elif self.build_engine is 'hugo':
            yield BuildHugoSite()


class BuildJekyllSite(BaseTask):
    '''
    Task to built the source repository using jekyll
    '''
    # Expects jekyll to be in PATH

    # TODO:
    #  - delete _site if it exists in the repo? Not sure if necessary any more
    #  - invoke jekyll:
    #   if [[ -f Gemfile ]]; then
    #         echo "[build.sh] Setting up bundler"
    #         gem install bundler
    #         echo "[build.sh] Installing dependencies in Gemfile"
    #         bundle install
    #         echo "[build.sh] Building using Jekyll version: $(bundle exec jekyll -v)"
    #         bundle exec jekyll build --destination ./_site
    #     else
    #         echo "[build.sh] Installing Jekyll"
    #         gem install jekyll
    #         echo "[build.sh] Building using Jekyll version: $(jekyll -v)"
    #         jekyll build --destination ./_site
    #     fi
    pass


class BuildHugoSite(BaseTask):
    '''
    Task to built the source repository using hugo
    '''
    # Expects hugo to be in PATH

    # TODO:
    #   - invoke hugo:
    #  echo "[build.sh] Using hugo version: $(hugo version)"
    #   hugo --baseURL ${BASEURL-"''"} --source . --destination ./_site

    def run(self):
        # if not os.path.exists(self.built_site_dir):
        #     os.makedirs(self.built_site_dir)
        pass


class BuildCopySite(BaseTask):
    '''
    Task to copy all files (except .git/) from the source repository
    into the target built site directory
    '''
    def output(self):
        return luigi.LocalTarget(self.built_site_dir)

    def run(self):
        BUILD_LOGGER.info(f'Copying all repository files to {self.built_site_dir}')

        # ignore the .git directory in the source repository
        ignore = shutil.ignore_patterns('.git')

        # recursively copy all files to the built site directory
        shutil.copytree(self.clone_dir, self.built_site_dir, ignore=ignore)

