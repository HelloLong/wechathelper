#!/bin/sh

set -e

# Change the next 3 lines to suit where you install your script and what you want to call it
DIR=/your/path
DAEMON=$DIR/wechat.py
DAEMON_NAME=wechat

# Add any command line options for your daemon here
DAEMON_OPTS=""

# This next line determines what user the script runs as.
# Root generally not recommended but necessary if you are using the Raspberry Pi GPIO from Python.
DAEMON_USER=user

# The process ID of the script when it runs is stored here:
PIDFILE=/var/run/$DAEMON_NAME.pid

export PATH="${PATH:+$PATH:}/usr/sbin:/sbin"

. /lib/lsb/init-functions

do_start () {
    log_daemon_msg "Starting $DAEMON_NAME daemon"
    start-stop-daemon --no-close --start --background --pidfile $PIDFILE --make-pidfile --user $DAEMON_USER --chuid $DAEMON_USER --startas $DAEMON -- $DAEMON_OPTS >> "$DIR/output.log" 2>&1
    log_end_msg $?
}
do_stop () {
    log_daemon_msg "Stopping $DAEMON_NAME daemon"
    start-stop-daemon --stop --pidfile $PIDFILE --retry 10
    log_end_msg $?
}

case "$1" in

    start|stop)
        do_${1}
        ;;

    restart|reload|force-reload)
        do_stop
        do_start
        ;;

    status)
        status_of_proc "$DAEMON_NAME" "$DAEMON" && exit 0 || exit $?
        ;;

    *)
        echo "Usage: ./service.sh {start|stop|restart|status}"
        exit 1
        ;;

esac
exit 0