
import pandas as pd
import base64
import re
import io

def parse_rafts_file(rafts_file):
    rafts_data = {}
    event_times = {}

    for line in rafts_file:
        line_data = line.split()
        if re.match(r'\s{1,4}\w', line):
            event = int(line_data[0])
            routing_increments = int(line_data[2])
            length_of_increment = int(float(line_data[3]))
            times = pd.timedelta_range(start=0, periods=routing_increments, 
                freq='{0}T'.format(length_of_increment))
            times = list(times.astype(str))
            event_times[event] = times
            rafts_data[event] = {}
            pass
        elif re.match(r'\w', line):
            node = line.split(' ', 1)[1].strip()
            rafts_data[event][node] = []
            pass
        else:
            # try:
            rafts_data[event][node].extend([float(f) for f in line_data])
            # except KeyError:
            #     rafts_data[event][node] = \
            #         [float(f) for f in line_data]

    return rafts_data, event_times

def parse_events_file(events_file):
    events = {}

    for i, line in enumerate(events_file):
        events[i+1] = line.strip() # events start from 1 in RAFTS file

    return events
