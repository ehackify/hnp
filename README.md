Honey Network Project
====================

HNP is a centralized server for management and data collection of honeypots. HNP
allows you to deploy sensors quickly and to collect data immediately, viewable
from a neat web interface. Honeypot deploy scripts include several common
honeypot technologies, including [Snort](https://snort.org/),
[Cowrie](http://www.micheloosterhof.com/cowrie/),
[Dionaea](https://www.edgis-security.org/single-post/dionaea-malware-honeypot), and
[glastopf](https://github.com/glastopf/), among others.

## Features

HNP is a Flask application that exposes an HTTP API that honeypots can use to:
- Download a deploy script
- Connect and register
- Download snort rules
- Send intrusion detection logs

It also allows system administrators to:
- View a list of new attacks
- Manage snort rules: enable, disable, download


## Installation

- The HNP server is supported on Ubuntu 18.04, Ubuntu 16.04, and Centos 6.9.  
- Other versions of Linux may work but are generally not tested or supported.

Note: if you run into trouble during the install, please checkout the [troubleshooting guide](https://github.com/ehackify/HNP/wiki/HNP-Troubleshooting-Guide) on the wiki.  If you only want to experiment with HNP on some virtual machines, please check out the [Getting up and Running with Vagrant](https://github.com/ehackify/HNP/wiki/Getting-up-and-running-using-Vagrant) guide on the wiki.

Install Git

    # on Debian or Ubuntu
    $ sudo apt install git -y
    
Install HNP
    
    $ cd /opt/
    $ sudo git clone https://github.com/ehackify/hnp.git
    $ cd HNP/

Run the following script to complete the installation.  While this script runs,
you will be prompted for some configuration options.  See below for how this
looks.

    $ sudo ./install.sh


### Configuration
    
    ===========================================================
    HNP Configuration
    ===========================================================
    Do you wish to run in Debug mode?: y/n n
    Superuser email: YOUR_EMAIL@YOURSITE.COM
    Superuser password: 
    Server base url ["http://1.2.3.4"]: 
    Honeymap url ["http://1.2.3.4:3000"]:
    Mail server address ["localhost"]: 
    Mail server port [25]: 
    Use TLS for email?: y/n n
    Use SSL for email?: y/n n
    Mail server username [""]: 
    Mail server password [""]: 
    Mail default sender [""]: 
    Path for log file ["HNP.log"]: 


### Running

If the installation scripts ran successfully, you should have a number of
services running on your HNP server.  See below for checking these.

    user@precise64:/opt/HNP/scripts$ sudo /etc/init.d/nginx status
     * nginx is running
    user@precise64:/opt/HNP/scripts$ sudo /etc/init.d/supervisor status
     is running
    user@precise64:/opt/HNP/scripts$ sudo supervisorctl status
    geoloc                           RUNNING    pid 31443, uptime 0:00:12
    honeymap                         RUNNING    pid 30826, uptime 0:08:54
    hpfeeds-broker                   RUNNING    pid 10089, uptime 0:36:42
    HNP-celery-beat                  RUNNING    pid 29909, uptime 0:18:41
    HNP-celery-worker                RUNNING    pid 29910, uptime 0:18:41
    HNP-collector                    RUNNING    pid 7872,  uptime 0:18:41
    HNP-uwsgi                        RUNNING    pid 29911, uptime 0:18:41
    mnemosyne                        RUNNING    pid 28173, uptime 0:30:08

## Deploying honeypots with HNP

HNP was designed to make scalable deployment of honeypots easier.  Here are the
steps for deploying a honeypot with HNP:

1. Login to your HNP server web app.
2. Click the "Deploy" link in the upper left hand corner.
3. Select a type of honeypot from the drop down menu (e.g. "Ubuntu Dionaea").
4. Copy the deployment command.
5. Login to a honeypot server and run this command as root.

If the deploy script successfully completes you should see the new sensor listed
under your deployed sensor list.

## Integration with Splunk and ArcSight

hpfeeds-logger can be used to integrate HNP with Splunk and ArcSight.

#### Splunk


    cd /opt/HNP/scripts/
    sudo ./install_hpfeeds-logger-splunk.sh

This will log the events as key/value pairs to /var/log/HNP-splunk.log.  This
log should be monitored by the SplunkUniversalForwarder.

#### Arcsight


    cd /opt/HNP/scripts/
    sudo ./install_hpfeeds-logger-arcsight.sh

This will log the events as CEF to /var/log/HNP-arcsight.log


### Credit and Thanks
HNP was created by eHackify Team.

## LICENSE

Honeypot Network Project

MIT License

Copyright (c) 2020 eHackify

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

