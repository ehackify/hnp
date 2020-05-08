import os
from urlparse import urlparse

from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

try:
    import config
except ImportError:
    print 'It seems like this is the first time running the server.'
    print 'First let us generate a proper configuration file.'
    try:
        from generateconfig import generate_config
        generate_config()
        import config
        from hnp import create_clean_db
        print 'Initializing database "{}".'.format(config.SQLALCHEMY_DATABASE_URI)
        create_clean_db()
    except Exception as e:
        print e
        print 'An error ocurred. Please fix the errors and try again.'
        print 'Deleting "config.py" file.'
        try:
            os.remove('config.py')
            os.remove('config.pyc')
        finally:
            raise SystemExit('Exiting now.')

from hnp import hnp, db
from hnp.tasks.rules import fetch_sources


if __name__ == '__main__':
    migrate = Migrate(hnp, db)
    manager = Manager(hnp)
    manager.add_command('db', MigrateCommand)

    @manager.command
    def run():
        # Takes run parameters from configuration.
        serverurl = urlparse(config.SERVER_BASE_URL)
        os.system('celery -A hnp.tasks --config=config beat &')
        os.system('celery -A hnp.tasks --config=config worker &')
        hnp.run(debug=config.DEBUG, host='0.0.0.0',
                port=serverurl.port)

    @manager.command
    def runlocal():
        serverurl = urlparse(config.SERVER_BASE_URL)
        hnp.run(debug=config.DEBUG, host='0.0.0.0',
                port=serverurl.port)

    @manager.command
    def fetch_rules():
        fetch_sources()

    manager.run()
