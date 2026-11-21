import secrets
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from desk.store import rows,create
class Command(BaseCommand):
    @transaction.atomic
    def handle(self,*args,**options):
        for name, staff in (("arvo.agent",True),("arvo.second",True),("arvo.customer",False)):
            user, new = get_user_model().objects.get_or_create(username=name,defaults={"is_staff":staff})
            if new:
                password = secrets.token_urlsafe(12)
                user.set_password(password)
                user.save()
                self.stdout.write(f"{name}   {password}")
        if not rows("SELECT id FROM fd_ticket WHERE customer=%s LIMIT 1",(user.pk,)):
            create(user.pk,"Unable to open the billing dashboard","urgent",user.pk)
