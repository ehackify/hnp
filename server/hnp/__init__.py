from urlparse import urljoin

from flask import Flask, request, jsonify, abort, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.utils import encrypt_password as encrypt
from flask_mail import Mail
from werkzeug.contrib.atom import AtomFeed
import xmltodict
import uuid
import random
import string
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

db = SQLAlchemy()
# After defining `db`, import auth models due to
# circular dependency.
from hnp.auth.models import User, Role, ApiKey
user_datastore = SQLAlchemyUserDatastore(db, User, Role)


hnp = Flask(__name__)
hnp.config.from_object('config')
csrf.init_app(hnp)

# Email app setup.
mail = Mail()
mail.init_app(hnp)

# Registering app on db instance.
db.init_app(hnp)

# Setup flask-security for auth.
Security(hnp, user_datastore)

# Registering blueprints.
from hnp.api.views import api
hnp.register_blueprint(api)

from hnp.ui.views import ui
hnp.register_blueprint(ui)

from hnp.auth.views import auth
hnp.register_blueprint(auth)

# Trigger templatetag register.
from hnp.common.templatetags import format_date
hnp.jinja_env.filters['fdate'] = format_date

from hnp.auth.contextprocessors import user_ctx
hnp.context_processor(user_ctx)

from hnp.common.contextprocessors import config_ctx
hnp.context_processor(config_ctx)

import logging
from logging.handlers import RotatingFileHandler

hnp.logger.setLevel(logging.INFO)
formatter = logging.Formatter(
      '%(asctime)s -  %(pathname)s - %(message)s')
handler = RotatingFileHandler(
        hnp.config['LOG_FILE_PATH'], maxBytes=10240, backupCount=5)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
hnp.logger.addHandler(handler)
if hnp.config['DEBUG']:
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    hnp.logger.addHandler(console)


@hnp.route('/feed.json')
def json_feed():
    feed_content = get_feed().to_string()
    return jsonify(xmltodict.parse(feed_content))


@hnp.route('/feed.xml')
def xml_feed():
    return get_feed().get_response()


def makeurl(uri):
    baseurl = hnp.config['SERVER_BASE_URL']
    return urljoin(baseurl, uri)


def get_feed():
    from hnp.common.clio import Clio
    from hnp.auth import current_user
    authfeed = hnp.config['FEED_AUTH_REQUIRED']
    if authfeed and not current_user.is_authenticated:
        abort(404)
    feed = AtomFeed('hnp HpFeeds Report', feed_url=request.url,
                    url=request.url_root)
    sessions = Clio().session.get(options={'limit': 1000})
    for s in sessions:
        feedtext = u'Sensor "{identifier}" '
        feedtext += '{source_ip}:{source_port} on sensorip:{destination_port}.'
        feedtext = feedtext.format(**s.to_dict())
        feed.add('Feed', feedtext, content_type='text',
                 published=s.timestamp, updated=s.timestamp,
                 url=makeurl(url_for('api.get_session', session_id=str(s._id))))
    return feed


def create_clean_db():
    """
    Use from a python shell to create a fresh database.
    """
    with hnp.test_request_context():
        db.create_all()
        # Creating superuser entry.
        superuser = user_datastore.create_user(
                email=hnp.config.get('SUPERUSER_EMAIL'),
                password=encrypt(hnp.config.get('SUPERUSER_PASSWORD')))
        adminrole = user_datastore.create_role(name='admin', description='')
        user_datastore.add_role_to_user(superuser, adminrole)
        user_datastore.create_role(name='user', description='')
        db.session.flush()

        apikey = ApiKey(user_id=superuser.id, api_key=str(uuid.uuid4()).replace("-", ""))
        db.session.add(apikey)
        db.session.flush()

        from os import path

        from hnp.api.models import DeployScript, RuleSource
        from hnp.tasks.rules import fetch_sources
        # Creating a initial deploy scripts.
        # Reading initial deploy script should be: ../../scripts/
        #|-- deploy_conpot.sh
        #|-- deploy_dionaea.sh
        #|-- deploy_snort.sh
        #|-- deploy_kippo.sh
        deployscripts = [
            ['Ubuntu - Conpot', '../scripts/deploy_conpot.sh'],
            ['Ubuntu/Raspberry Pi - Drupot', '../scripts/deploy_drupot.sh'],
            ['Ubuntu/Raspberry Pi - Magenpot', '../scripts/deploy_magenpot.sh'],
            ['Ubuntu - Wordpot', '../scripts/deploy_wordpot.sh'],
            ['Ubuntu - Shockpot', '../scripts/deploy_shockpot.sh'],
            ['Ubuntu - p0f', '../scripts/deploy_p0f.sh'],
            ['Ubuntu - Suricata', '../scripts/deploy_suricata.sh'],
            ['Ubuntu - Glastopf', '../scripts/deploy_glastopf.sh'],
            ['Ubuntu - ElasticHoney', '../scripts/deploy_elastichoney.sh'],
            ['Ubuntu - Amun', '../scripts/deploy_amun.sh'],
            ['Ubuntu - Snort', '../scripts/deploy_snort.sh'],
            ['Ubuntu - Cowrie', '../scripts/deploy_cowrie.sh'],
            ['Ubuntu/Raspberry Pi - Dionaea', '../scripts/deploy_dionaea.sh'],
            ['Ubuntu - Shockpot Sinkhole', '../scripts/deploy_shockpot_sinkhole.sh'],
        ]
        for honeypot, deploypath in reversed(deployscripts):

            with open(path.abspath(deploypath), 'r') as deployfile:
                initdeploy = DeployScript()
                initdeploy.script = deployfile.read()
                initdeploy.notes = 'Initial deploy script for {}'.format(honeypot)
                initdeploy.user = superuser
                initdeploy.name = honeypot
                db.session.add(initdeploy)

        # Creating an initial rule source.
        rules_source = hnp.config.get('SNORT_RULES_SOURCE')
        if not hnp.config.get('TESTING'):
            rulesrc = RuleSource()
            rulesrc.name = rules_source['name']
            rulesrc.uri = rules_source['uri']
            rulesrc.name = 'Default rules source'
            db.session.add(rulesrc)
            db.session.commit()
            fetch_sources()
