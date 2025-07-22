import unittest
import json
from unittest.mock import patch, MagicMock
from scheduler import Scheduler

class TestScheduler(unittest.TestCase):
    def setUp(self):
        # Sample JSON data to be returned by mocked urlopen
        self.sample_data = {
            "days": [
                {"id": 1, "date": "2024-10-10", "start": "09:00", "end": "18:00"},
                {"id": 2, "date": "2024-10-11", "start": "08:00", "end": "17:00"},
                {"id": 3, "date": "2024-10-12", "start": "10:00", "end": "15:00"}
            ],
            "timeslots": [
                {"id": 1, "day_id": 1, "start": "11:00", "end": "12:00"},
                {"id": 3, "day_id": 2, "start": "09:30", "end": "16:00"},
                {"id": 4, "day_id": 1, "start": "14:00", "end": "15:00"}
            ]
        }
        
        # Create a mock response object
        self.mock_response = MagicMock()
        self.mock_response.read.return_value = json.dumps(self.sample_data).encode('utf-8')
        self.mock_response.__enter__.return_value = self.mock_response

    @patch('scheduler.urlopen')
    def test_get_busy_slots(self, mock_urlopen):
        mock_urlopen.return_value = self.mock_response
        scheduler = Scheduler(url="http://test.url")
        
        # Test existing date with busy slots
        self.assertEqual(
            scheduler.get_busy_slots("2024-10-10"),
            [("11:00", "12:00"), ("14:00", "15:00")]
        )
        
        # Test existing date with no busy slots
        self.assertEqual(
            scheduler.get_busy_slots("2024-10-12"),
            []
        )
        
        # Test non-existent date
        self.assertEqual(
            scheduler.get_busy_slots("2024-10-13"),
            []
        )

    @patch('scheduler.urlopen')
    def test_get_free_slots(self, mock_urlopen):
        mock_urlopen.return_value = self.mock_response
        scheduler = Scheduler(url="http://test.url")
        
        # Test free slots with gaps
        self.assertEqual(
            scheduler.get_free_slots("2024-10-10"),
            [("09:00", "11:00"), ("12:00", "14:00"), ("15:00", "18:00")]
        )
        
        # Test fully booked day
        self.assertEqual(
            scheduler.get_free_slots("2024-10-11"),
            [("08:00", "09:30"), ('16:00', '17:00')]
        )
        
        # Test empty day
        self.assertEqual(
            scheduler.get_free_slots("2024-10-12"),
            [("10:00", "15:00")]
        )

    @patch('scheduler.urlopen')
    def test_is_available(self, mock_urlopen):
        mock_urlopen.return_value = self.mock_response
        scheduler = Scheduler(url="http://test.url")
        
        # Valid slot before busy period
        self.assertTrue(scheduler.is_available("2024-10-10", "10:00", "10:30"))
        
        # Slot overlapping busy period
        self.assertFalse(scheduler.is_available("2024-10-10", "11:30", "12:30"))
        
        # Slot exactly in free period
        self.assertTrue(scheduler.is_available("2024-10-10", "12:30", "13:30"))
        
        # Slot outside working hours
        self.assertFalse(scheduler.is_available("2024-10-10", "08:00", "09:00"))
        
        # Slot spanning multiple busy periods
        self.assertFalse(scheduler.is_available("2024-10-10", "10:30", "14:30"))

    @patch('scheduler.urlopen')
    def test_find_slot_for_duration(self, mock_urlopen):
        mock_urlopen.return_value = self.mock_response
        scheduler = Scheduler(url="http://test.url")
        
        # Find 60-minute slot (earliest available)
        self.assertEqual(
            scheduler.find_slot_for_duration(60),
            ("2024-10-10", "09:00", "10:00")
        )
        
        # Find 90-minute slot (needs to go to next day)
        self.assertEqual(
            scheduler.find_slot_for_duration(90),
            ("2024-10-10", "09:00", "10:30")
        )
        
        # Find 300-minute slot (only fits in third day)
        self.assertEqual(
            scheduler.find_slot_for_duration(300),
            ("2024-10-12", "10:00", "15:00")
        )
        
        # Slot too long for any day
        self.assertIsNone(scheduler.find_slot_for_duration(1000))

if __name__ == '__main__':
    unittest.main()
