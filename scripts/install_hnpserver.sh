#!/bin/bash

set -e
set -x
SCRIPTDIR=`dirname "$(readlink -f "$0")"`
hnp_HOME=$SCRIPTDIR/..


if [ -f /etc/debian_version ]; then
    OS=Debian  # XXX or Ubuntu??
    INSTALLER='apt-get'
    REPOPACKAGES='git build-essential python-pip python-dev redis-server libgeoip-dev nginx libsqlite3-dev'
    PYTHON=`which python`
    PIP=`which pip`
    $PIP install virtualenv
    VIRTUALENV=`which virtualenv`

elif [ -f /etc/redhat-release ]; then
    OS=RHEL
    export PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:$PATH
    INSTALLER='yum'
    REPOPACKAGES='epel-release git GeoIP-devel wget redis nginx'

    if  [ ! -f /usr/local/bin/python2.7 ]; then
        $SCRIPTDIR/install_python2.7.sh
    fi

    #use python2.7
    PYTHON=/usr/local/bin/python2.7
    PIP=/usr/local/bin/pip2.7
    $PIP install virtualenv
    VIRTUALENV=/usr/local/bin/virtualenv

    #install supervisor from pip2.7
    $PIP install supervisor

else
    echo -e "ERROR: Unknown OS\nExiting!"
    exit -1
fi

$INSTALLER update
$INSTALLER -y install $REPOPACKAGES


cd $hnp_HOME
hnp_HOME=`pwd`

$VIRTUALENV  -p $PYTHON env
. env/bin/activate

pip install -r server/requirements.txt
if [ -f /etc/redhat-release ]; then
    pip install pysqlite==2.8.1
    service redis start
fi

echo "DONE installing python virtualenv"

mkdir -p /var/log/hnp &> /dev/null
cd $hnp_HOME/server/

echo "==========================================================="
echo "  hnp Configuration"
echo "==========================================================="

python generateconfig.py

echo -e "\nInitializing database, please be patient. This can take several minutes"
python initdatabase.py
cd $hnp_HOME

mkdir -p /opt/www
mkdir -p /etc/nginx

if [ $OS == "Debian" ]; then
    mkdir -p /etc/nginx/sites-available
    mkdir -p /etc/nginx/sites-enabled
    NGINXCONFIG=/etc/nginx/sites-available/default
    touch $NGINXCONFIG
    ln -fs /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
    NGINXUG='www-data:www-data'
    NGINXUSER='www-data'

elif [ $OS == "RHEL" ]; then
    NGINXCONFIG=/etc/nginx/conf.d/default.conf
    NGINXUG='nginx:nginx'
    NGINXUSER='nginx'
fi

cat > $NGINXCONFIG <<EOF
server {
    listen       80;
    server_name  _;
    
    location / { 
        try_files \$uri @hnpserver; 
    }
    
    root /opt/www;

    location @hnpserver {
      include uwsgi_params;
      uwsgi_pass unix:/tmp/uwsgi.sock;
    }

    location  /static {
      alias $hnp_HOME/server/hnp/static;
    }
}
EOF


cat > /etc/supervisor/conf.d/hnp-uwsgi.conf <<EOF 
[program:hnp-uwsgi]
command=$hnp_HOME/env/bin/uwsgi -s /tmp/uwsgi.sock -w hnp:hnp -H $hnp_HOME/env --chmod-socket=666 -b 40960
directory=$hnp_HOME/server
stdout_logfile=/var/log/hnp/hnp-uwsgi.log
stderr_logfile=/var/log/hnp/hnp-uwsgi.err
autostart=true
autorestart=true
startsecs=10
EOF

cat > /etc/supervisor/conf.d/hnp-celery-worker.conf <<EOF 
[program:hnp-celery-worker]
command=$hnp_HOME/env/bin/celery worker -A hnp.tasks --loglevel=INFO
directory=$hnp_HOME/server
stdout_logfile=/var/log/hnp/hnp-celery-worker.log
stderr_logfile=/var/log/hnp/hnp-celery-worker.err
autostart=true
autorestart=true
startsecs=10
user=$NGINXUSER
EOF

touch /var/log/hnp/hnp-celery-worker.log /var/log/hnp/hnp-celery-worker.err
chown $NGINXUG /var/log/hnp/hnp-celery-worker.*

cat > /etc/supervisor/conf.d/hnp-celery-beat.conf <<EOF 
[program:hnp-celery-beat]
command=$hnp_HOME/env/bin/celery beat -A hnp.tasks --loglevel=INFO
directory=$hnp_HOME/server
stdout_logfile=/var/log/hnp/hnp-celery-beat.log
stderr_logfile=/var/log/hnp/hnp-celery-beat.err
autostart=true
autorestart=true
startsecs=10
EOF

hnp_UUID=`python -c 'import uuid;print str(uuid.uuid4())'`
SECRET=`python -c 'import uuid;print str(uuid.uuid4()).replace("-","")'`
/opt/hpfeeds/env/bin/python /opt/hpfeeds/broker/add_user.py "collector" "$SECRET" "" "geoloc.events"

cat > $hnp_HOME/server/collector.json <<EOF
{
  "IDENT": "collector",
  "SECRET": "$SECRET",
  "hnp_UUID": "$hnp_UUID"
}
EOF

cat > /etc/supervisor/conf.d/hnp-collector.conf <<EOF 
[program:hnp-collector]
command=$hnp_HOME/env/bin/python collector_v2.py collector.json
directory=$hnp_HOME/server
stdout_logfile=/var/log/hnp/hnp-collector.log
stderr_logfile=/var/log/hnp/hnp-collector.err
autostart=true
autorestart=true
startsecs=10
EOF

touch $hnp_HOME/server/hnp.log
chown $NGINXUG -R $hnp_HOME/server/*

supervisorctl update
/etc/init.d/nginx restart
