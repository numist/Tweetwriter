Tweetwriter
===========

The most instructive part of this project is the tweetwriter.py script, which can be used as a basic demonstration of how to create a tweet wall style project of your own. The rest of the code consists of an init script, bootstrap script, and glue code for getting the tweet data out to a [hacked typewriter](http://numist.net/post/2010/project-typewriter.html).

Configuration
-------------

Copy config.example.json to config.json and populate it with your Twitter developer key and token information. You may have to [generate a new access token](https://dev.twitter.com/docs/auth/tokens-devtwittercom) for your application. You'll probably also want to edit `tweetwriter.py` to reflect your intended search terms and output to a device other than a teletype.

Running
-------

Just execute `run.sh` and it will run the Tweetwriter script until you kill it. If you want to install this to run at boot (on any sane Linux environment), copy `tweetwriter` to `/etc/init.d` and run `update-rc.d tweetwriter defaults`.
