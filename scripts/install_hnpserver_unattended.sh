#!/bin/bash

set -e

scripts_directory="$(dirname $(readlink -f ${BASH_SOURCE}))"
hnp_directory="$(dirname ${scripts_directory})"

if test -f "${hnp_directory}/server/config.py"; then
    "${hnp_directory}/scripts/install_hnpserver.sh"
else
    echo "${hnp_directory}/server/config.py does not exist. Please create the configuration file first using the generateconfig.py script."
    exit 1
fi
