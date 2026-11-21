import unittest, os
from unittest.mock import patch
from datetime import datetime,timedelta
from desk.calendar import ZONE, deadlines, worked
class CalendarTest(unittest.TestCase):
    def test_friday(self):
        f=datetime(2026,11,20,18,tzinfo=ZONE)
        self.assertEqual(deadlines(f,"urgent"),(datetime(2026,11,23,11,tzinfo=ZONE),f+timedelta(minutes=30)))
    @patch.dict(os.environ, {"HOLIDAYS":"2026-11-23"})
    def test_holiday(self):
        f=datetime(2026,11,20,18,tzinfo=ZONE)
        due=deadlines(f,"urgent")[0]
        self.assertEqual(due,datetime(2026,11,24,11,tzinfo=ZONE))
        self.assertEqual(worked(f,due),timedelta(hours=2))
