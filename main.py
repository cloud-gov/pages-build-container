import luigi

import tasks


class RunAll(luigi.Task):
    '''
    Dummy task that triggers execution of a other tasks

    PYTHONPATH='.' luigi --module main RunAll --repo-owner jseppi \
        --repo-name test-federalist-site --branch master --local-scheduler
    '''
    def requires(self):
        # TODO: call the final task in the chain
        return tasks.CloneRepo()
