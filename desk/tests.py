from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import datetime, timedelta
from unittest.mock import patch
from .calendar import ZONE, DAY, add_work, deadlines
from django.contrib.auth import get_user_model
from django.db import DatabaseError, connections, transaction
from django.test import TestCase, TransactionTestCase
from .store import create, change, rows, close_waiting

class TicketTests(TestCase):
    def setUp(self):
        users = get_user_model().objects
        self.customer = users.create_user("customer")
        self.agent = users.create_user("agent",is_staff=True)
        self.pk = create(self.customer.pk,"Invoice","medium",self.customer.pk)
        change(self.pk,self.agent,"claim")

    def test_health_endpoint(self):
        self.assertEqual(self.client.get("/healthz").content, b"ok")
        with patch("desk.views.rows", side_effect=DatabaseError):
            self.assertEqual(self.client.get("/healthz").status_code, 503)

    def test_customer_visibility(self):
        change(self.pk,self.agent,"note","internal only 843")
        change(self.pk,self.agent,"reply","public reply 920")
        self.client.force_login(self.customer)
        page = self.client.get(f"/ticket/{self.pk}/")
        self.assertContains(page,"public reply 920")
        self.assertNotContains(page,"internal only 843")
        self.assertNotContains(self.client.get("/"),"internal only 843")
        self.client.force_login(get_user_model().objects.create_user("other"))
        self.assertEqual(self.client.get(f"/ticket/{self.pk}/").status_code,404)

    def test_first_reply_and_history(self):
        change(self.pk,self.agent,"reply","First")
        change(self.pk,self.agent,"reply","Second")
        first = rows("SELECT happened FROM fd_event WHERE ticket=%s AND kind='Agent reply' ORDER BY id",(self.pk,))[0]
        self.assertEqual(rows("SELECT first_reply FROM fd_ticket WHERE id=%s",(self.pk,))[0]["first_reply"],first["happened"])
        with self.assertRaises(DatabaseError), transaction.atomic():
            rows("UPDATE fd_event SET body='changed' WHERE ticket=%s",(self.pk,))

    def ticket(self):
        return rows("SELECT * FROM fd_ticket WHERE id=%s", (self.pk,))[0]

    def test_pause_and_customer_reply(self):
        before = self.ticket()
        start = datetime(2027, 1, 4, 10, tzinfo=ZONE)
        with patch("desk.store.database_now", return_value=start):
            change(self.pk, self.agent, "wait")
        with patch("desk.store.database_now", return_value=start + timedelta(hours=2)):
            change(self.pk, self.customer, "reply", "More details")
        after = self.ticket()
        self.assertEqual(after["state"], "open")
        for key in ("reply_due", "fix_due"):
            self.assertEqual(after[key], add_work(before[key], timedelta(hours=2)))

    def test_priority_change_preserves_first_reply_and_audits_targets(self):
        change(self.pk, self.agent, "reply", "Checking")
        before = self.ticket()
        when = before["first_reply"] + timedelta(hours=1)
        with patch("desk.store.database_now", return_value=when):
            change(self.pk, self.agent, "priority", "urgent")
        after = self.ticket()
        self.assertEqual(after["reply_due"], before["reply_due"])
        self.assertEqual(after["fix_due"], deadlines(when, "urgent")[1])
        audit = rows("SELECT body FROM fd_event WHERE ticket=%s AND kind='Priority changed'", (self.pk,))[0]["body"]
        for record in (before, after):
            self.assertIn(record["priority"], audit)
            for field in ("reply_due", "fix_due"):
                self.assertIn(record[field].astimezone(ZONE).isoformat(), audit)

    def test_auto_close_at_five_working_days(self):
        start = datetime(2027, 1, 4, 10, tzinfo=ZONE)
        with patch("desk.store.database_now", return_value=start):
            change(self.pk, self.agent, "wait")
        due = add_work(start, 5 * DAY)
        with patch("desk.store.database_now", return_value=due - timedelta(seconds=1)):
            close_waiting()
        self.assertEqual(self.ticket()["state"], "waiting")
        with patch("desk.store.database_now", return_value=due):
            close_waiting()
        self.assertEqual(self.ticket()["state"], "closed")

    def test_reopen_window_and_resolution_target(self):
        change(self.pk, self.agent, "resolve")
        boundary = self.ticket()["finished"] + timedelta(days=7)
        with patch("desk.store.database_now", return_value=boundary + timedelta(seconds=1)):
            with self.assertRaises(ValueError):
                change(self.pk, self.customer, "reopen")
        with patch("desk.store.database_now", return_value=boundary):
            change(self.pk, self.customer, "reopen")
        self.assertEqual(self.ticket()["fix_due"], deadlines(boundary, "medium")[1])

    def test_missed_deadlines_after_resolution(self):
        when = self.ticket()["fix_due"] + timedelta(hours=1)
        with patch("desk.store.database_now", return_value=when):
            change(self.pk, self.agent, "reply", "Checking")
            change(self.pk, self.agent, "resolve")
        self.client.force_login(self.agent)
        page = self.client.get("/?show=late")
        self.assertContains(page, "First reply sent after its deadline")
        self.assertContains(page, "Resolved after its deadline")

class ClaimRace(TransactionTestCase):
    available_apps = ["django.contrib.auth","django.contrib.contenttypes","django.contrib.sessions","desk"]
    def test_two_agents(self):
        users = get_user_model().objects
        customer = users.create_user("customer")
        agents = [users.create_user(name,is_staff=True) for name in ("first","second")]
        pk = create(customer.pk,"Simultaneous claim","urgent",customer.pk)
        gate = Barrier(2)
        def claim(agent):
            try:
                gate.wait(timeout=10)
                change(pk,agent,"claim")
                return True
            except ValueError:
                return False
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(claim,agents)),[False,True])
        winners = rows("SELECT actor FROM fd_event WHERE ticket=%s AND kind='Claimed'",(pk,))
        self.assertEqual(winners,[{"actor":rows("SELECT owner FROM fd_ticket WHERE id=%s",(pk,))[0]["owner"]}])

    def _fixture_teardown(self):
        # Django flushes registered models only. Clear dependent unmanaged tables in the isolated test database.
        with transaction.atomic():
            rows("ALTER TABLE fd_event DISABLE TRIGGER fd_event_guard")
            rows("TRUNCATE fd_event,fd_ticket")
            # auth_user has unmanaged FK dependents. Include them in Django's flush via CASCADE.
            super()._fixture_teardown()
            rows("ALTER TABLE fd_event ENABLE TRIGGER fd_event_guard")
