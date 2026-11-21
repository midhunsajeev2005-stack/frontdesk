from django.core.management.base import BaseCommand
from desk.store import close_waiting
class Command(BaseCommand):
    def handle(self,*args,**options):
        close_waiting()
