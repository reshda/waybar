#!/usr/bin/env python3

from os import getenv, environ
from os.path import expanduser, exists, isfile
import json
import requests
from dataclasses import dataclass
from datetime import datetime
from tabulate import tabulate
from colorama import Fore, init
from argparse import ArgumentParser

EWW_CALENDAR = """
(box :orientation 'v'
    (box :orientation 'v' :halign 'start' :class 'calendar-events'
        %s
    )
)
"""
EWW_EVENT = """
(box :orientation 'v' :halign 'start' :class 'calendar-event' :space-evenly 'false'
    (label :class 'calendar-event-date' :halign 'start' :text "%s")
    (box :orientation 'h' :class 'calendar-event'
      (label :class 'calendar-event-time' :halign 'start' :text "%s - %s")
    )
    (label :class 'calendar-event-summary' :halign 'start' :text "%s")
)
"""

EWW_ALL_DAY_EVENT = """
(box :orientation 'v' :halign 'start' :class 'calendar-event'
    (label :class 'calendar-event-date' :halign 'start' :text "%s")
    (box :orientation 'h' :class 'calendar-event'
      (label :class 'calendar-event-time' :halign 'start' :text "%s")
    )
    (label :class 'calendar-event-summary' :halign 'start' :text "%s")
)
"""

@dataclass
class Event:
    start_date: str
    start_date_time: str
    end_date: str
    end_date_time: str
    summary: str
    description: str
    call: str
    organizer: str

def parse_args():
    """ Parse command line arguments """
    parser = ArgumentParser(description="Fetch and display calendar events.")
    parser.add_argument("-e", "--eww", help="Output in eww format", action="store_true", required=False)
    return parser.parse_args()

def convert_date(date_str):
    """ Convert date string to string in YYYY-MM-DD format """
    try:
        return datetime.strptime(date_str, "%a %b %d %Y")
    except ValueError:
        print(f"Invalid date format: {date_str}")
        exit(1)

def format_time(time_str):
    """ Convert time string to string in HH:MM format """
    try:
        return datetime.fromisoformat(time_str).strftime("%H:%M")
    except ValueError:
        print(f"Invalid time format: {time_str}")
        return time_str

def format_date(date_str):
    """ Convert date string to string in YYYY-MM-DD format """
    try:
        return convert_date(date_str).strftime("%m/%d")
    except ValueError:
        print(f"Invalid date format: {date_str}")
        return date_str
    

def load_configuration():
    """ Load the file located in ~/.config/gcalendar/config.json """
    config_path = expanduser("~/.config/gcalendar/config.json")
    if not exists(config_path) or not isfile(config_path):
        print(f"Configuration file not found at {config_path}.")
        exit(1)
    
    with open(config_path, "r") as file:
        config = json.load(file)
        if "endpoint" not in config:
            print("No endpoint found in configuration file.")
            exit(1)
        environ["endpoint"] = config.get("endpoint", None) 
    return config

def remove_previous_events(events):
    """ Remove events that are in the past """
    today = datetime.now()
    # remove one day
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    events = [event for event in events if convert_date(event.start_date) >= today]
    # get only the next 5 events
    return events[:4]

def group_events(events):
    """ Group events by date """
    grouped_events = {}
    for event in events:
        if event.start_date_time and event.end_date_time:
            event.start_date_time = format_time(event.start_date_time)
            event.end_date_time = format_time(event.end_date_time)
        date = event.start_date
        if date not in grouped_events:
            grouped_events[date] = []
        grouped_events[date].append(event)
    return grouped_events

def load_data():
    """ load data from the endpoint """
    endpoint = getenv("endpoint", None)
    if endpoint is None:
        print("No endpoint found in environment variables.")
        exit(1) 
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        data = response.json()
        if not data:
            print("No data found in response.")
            exit(1)
        events = [Event(**event) for event in data]
        events = remove_previous_events(events)
        # sort them by date
        events.sort(key=lambda x: convert_date(x.start_date))
        return group_events(events)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from endpoint: {e}")
        exit(1)

def header(text):
    return color(text, Fore.MAGENTA)

def color(text, color):
    return color + text + Fore.RESET

def std_output(events):
    headers = [header("Date"), header("Start Time"), header("End Time"), header("Event")]
    content = []
    for _, events_list in events.items():
        for event in events_list:
            start_time = event.start_date_time if event.start_date_time else "ALL DAY"
            end_time = event.end_date_time if event.end_date_time else "ALL DAY"
            start_time = color(start_time, Fore.YELLOW)
            end_time = color(end_time, Fore.YELLOW)
            event.summary = color(event.summary, Fore.BLUE)
            content.append([color(format_date(event.start_date), Fore.CYAN), start_time, end_time, event.summary])
    print()
    print(tabulate(content, headers=headers, tablefmt="pipe", stralign="center"))

def eww_output(events):
    output = ""

    for date, events_list in events.items():
        for event in events_list:
            start_time = event.start_date_time if event.start_date_time else "ALL DAY"
            end_time = event.end_date_time if event.end_date_time else "ALL DAY"
            # if summary is empty or None, set it to "No summary"
            # if summary is longer than 30 characters, truncate it to 30 characters
            event.summary = event.summary if event.summary else "No summary"
            formatted_date = format_date(event.start_date)
            if len(event.summary) > 30:
                event.summary = event.summary[:30] + "..."
            if event.start_date_time and event.end_date_time:
                output += EWW_EVENT % (formatted_date, start_time, end_time, event.summary)
            else:
                if event.start_date != event.end_date:
                    formatted_date = "%s - %s" % (format_date(event.start_date), format_date(event.end_date))
                output += EWW_ALL_DAY_EVENT % (formatted_date, start_time, event.summary)
    print(EWW_CALENDAR % output)


def main():
    init(autoreset=True)
    load_configuration()
    args = parse_args()
    events = load_data()
    if not events:
        print("No events found.")
        exit(1)
    if args.eww:
        eww_output(events)
    else:
        std_output(events)

if __name__ == "__main__":
    main()
