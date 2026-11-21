from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.contrib.auth import get_user_model
from django.db import DatabaseError, connections, transaction
from django.test import TestCase, TransactionTestCase
from .store import create, change, rows

class TicketTests(TestCase):
    def setUp(self):
        users = get_user_model().objects
        self.customer = users.create_user("customer")
        self.agent = users.create_user("agent",is_staff=True)
        self.pk = create(self.customer.pk,"Invoice","medium",self.customer.pk)
        change(self.pk,self.agent,"claim")

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
