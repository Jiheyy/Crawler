#!/bin/sh

DAEMON1="kin_crawler.py"

MESSAGE="_was dead, so I restarted it now"


CheckDaemon()
{
    COUNT=$(ps aux | grep -v grep | grep -c $DAEMON1)
    if [ "$COUNT" -gt "0" ]; then
        echo "Agent is working"
    else
        nohup python3 $DAEMON1 &

        echo "Agent is not working."
        echo "$DAEMON1$MESSAGE"

    fi
}

while true; do
    CheckDaemon
    sleep 60
done
