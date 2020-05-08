#!/bin/bash

sudo sed -i'' 's/autostart=false/autostart=true/g'     /etc/supervisor/conf.d/hnp-collector.conf
sudo sed -i'' 's/autorestart=false/autorestart=true/g' /etc/supervisor/conf.d/hnp-collector.conf
sudo supervisorctl update

