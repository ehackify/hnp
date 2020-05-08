from celery import Celery

from hnp import hnp


celery = Celery(include=['hnp.tasks.rules'])
celery.conf.update(hnp.config)
TaskBase = celery.Task
class ContextTask(TaskBase):
    abstract = True
    def __call__(self, *args, **kwargs):
        with hnp.app_context():
            return TaskBase.__call__(self, *args, **kwargs)
celery.Task = ContextTask
