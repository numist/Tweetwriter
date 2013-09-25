#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pushd $DIR > /dev/null

if ! which virtualenv > /dev/null; then
    echo "This script requires virtualenv. Attempting to install..."
    if which pip
        then sudo pip install virtualenv
        else sudo easy_install virtualenv
    fi
fi

echo "Creating/entering virtual environment"

if ! [ -d "env" ]
    then mkdir env
fi

virtualenv env --no-site-packages --unzip-setuptools
source env/bin/activate

if ! which pip > /dev/null; then
    echo "Installing pip into virtual environment..."
    easy_install pip
    source env/bin/activate
fi

echo "Installing requirements..."
pip install -r requirements.txt
echo "Starting tweetwriter..."
python tweetwriter.py
