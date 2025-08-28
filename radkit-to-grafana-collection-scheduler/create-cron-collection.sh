#!/bin/bash

# Usage:
# ./cron_job_manager.sh add|remove schedule.yaml
#
# Parameters:
#   add     - Add or update the cron job with the schedule specified in the YAML file
#   remove  - Remove the existing cron job created by this script
#   schedule.yaml - YAML file containing the cron schedule (required only for 'add' option)

CRON_COMMENT="#moneybyte_cron_job"
CMD="/usr/local/bin/docker run --rm --network moneybyte_moneybyte-app-network --name moneybyte-collector moneybyte-collector"

function add_cron_job() {
    local schedule_file=$1
    if [[ ! -f "$schedule_file" ]]; then
        echo "Schedule file '$schedule_file' not found."
        exit 1
    fi

    # Extract schedule fields from YAML file
    minute=$(grep '^minute:' "$schedule_file" | awk '{print $2}')
    hour=$(grep '^hour:' "$schedule_file" | awk '{print $2}')
    day_of_month=$(grep '^day_of_month:' "$schedule_file" | awk '{print $2}')
    month=$(grep '^month:' "$schedule_file" | awk '{print $2}')
    day_of_week=$(grep '^day_of_week:' "$schedule_file" | awk '{print $2}')

    # Validate that all fields are present
    if [[ -z "$minute" || -z "$hour" || -z "$day_of_month" || -z "$month" || -z "$day_of_week" ]]; then
        echo "One or more schedule fields are missing in $schedule_file."
        exit 1
    fi

    # Building of the image
    docker build -t moneybyte-collector .

    # Remove any existing cron job with the comment
    crontab -l | grep -v "$CRON_COMMENT" | crontab -

    # Add new cron job
    echo "$minute $hour $day_of_month $month $day_of_week $CMD $CRON_COMMENT >> /tmp/moneybyte_cronjob.log 2>&1"
    (crontab -l 2>/dev/null; echo "$minute $hour $day_of_month $month $day_of_week $CMD $CRON_COMMENT >> /tmp/moneybyte_cronjob.log 2>&1") | crontab -

    echo "=============MoneyByte Cron job added/updated successfully.============="
}

function remove_cron_job() {
    # Remove cron job with the specific comment
    crontab -l | grep -v "$CRON_COMMENT" | crontab -
    echo "=============Cron job removed successfully.============="
}

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 add|remove [schedule.yaml]"
    exit 1
fi

ACTION=$1

case $ACTION in
    add)
        if [[ $# -ne 2 ]]; then
            echo "Usage: $0 add schedule.yaml"
            exit 1
        fi
        add_cron_job "$2"
        ;;
    remove)
        remove_cron_job
        ;;
    *)
        echo "Invalid action. Use 'add' or 'remove'."
        exit 1
        ;;
esac