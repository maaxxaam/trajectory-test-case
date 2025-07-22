import json
from urllib.request import urlopen
from collections import defaultdict

class Scheduler:
    def __init__(self, url):
        self.url = url
        self.days_by_date = {}
        self.timeslots_by_day = defaultdict(list)
        self._fetch_data()
        self._organize_data()
    
    def _fetch_data(self):
        with urlopen(self.url) as response:
            data = json.loads(response.read().decode())
        self.data = data
    
    def _organize_data(self):
        for day in self.data['days']:
            self.days_by_date[day['date']] = day
        for timeslot in self.data['timeslots']:
            day_id = timeslot['day_id']
            self.timeslots_by_day[day_id].append(timeslot)
    
    @staticmethod
    def time_str_to_minutes(time_str):
        hours, minutes = time_str.split(':')
        return int(hours) * 60 + int(minutes)
    
    @staticmethod
    def minutes_to_time_str(minutes):
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours:02d}:{minutes:02d}"
    
    def get_busy_slots(self, date):
        if date not in self.days_by_date:
            return []
        day = self.days_by_date[date]
        day_id = day['id']
        timeslots = self.timeslots_by_day.get(day_id, [])
        return [(ts['start'], ts['end']) for ts in timeslots]
    
    def get_free_slots(self, date):
        if date not in self.days_by_date:
            return []
        day = self.days_by_date[date]
        day_start_str = day['start']
        day_end_str = day['end']
        day_start_min = self.time_str_to_minutes(day_start_str)
        day_end_min = self.time_str_to_minutes(day_end_str)
        
        busy_slots = self.get_busy_slots(date)
        busy_intervals = []
        for start, end in busy_slots:
            start_min = self.time_str_to_minutes(start)
            end_min = self.time_str_to_minutes(end)
            busy_intervals.append((start_min, end_min))
        
        busy_intervals.sort(key=lambda x: x[0])
        
        free_intervals = []
        current_start = day_start_min
        
        for busy_start, busy_end in busy_intervals:
            if current_start < busy_start:
                free_intervals.append((current_start, busy_start))
            current_start = max(current_start, busy_end)
        
        if current_start < day_end_min:
            free_intervals.append((current_start, day_end_min))
        
        result = []
        for start_min, end_min in free_intervals:
            start_str = self.minutes_to_time_str(start_min)
            end_str = self.minutes_to_time_str(end_min)
            result.append((start_str, end_str))
        
        return result
    
    def is_available(self, date, start_time, end_time):
        if date not in self.days_by_date:
            return False
        
        day = self.days_by_date[date]
        day_start = day['start']
        day_end = day['end']
        
        slot_start_min = self.time_str_to_minutes(start_time)
        slot_end_min = self.time_str_to_minutes(end_time)
        day_start_min = self.time_str_to_minutes(day_start)
        day_end_min = self.time_str_to_minutes(day_end)
        
        if slot_start_min < day_start_min or slot_end_min > day_end_min:
            return False
        
        busy_slots = self.get_busy_slots(date)
        for busy_start_str, busy_end_str in busy_slots:
            busy_start_min = self.time_str_to_minutes(busy_start_str)
            busy_end_min = self.time_str_to_minutes(busy_end_str)
            if slot_start_min < busy_end_min and slot_end_min > busy_start_min:
                return False
        
        return True
    
    def find_slot_for_duration(self, duration_minutes):
        sorted_days = sorted(self.data['days'], key=lambda d: d['date'])
        for day in sorted_days:
            date = day['date']
            free_slots = self.get_free_slots(date)
            for slot_start_str, slot_end_str in free_slots:
                slot_start_min = self.time_str_to_minutes(slot_start_str)
                slot_end_min = self.time_str_to_minutes(slot_end_str)
                slot_duration = slot_end_min - slot_start_min
                if slot_duration >= duration_minutes:
                    booking_end_min = slot_start_min + duration_minutes
                    booking_end_str = self.minutes_to_time_str(booking_end_min)
                    return (date, slot_start_str, booking_end_str)
        return None
