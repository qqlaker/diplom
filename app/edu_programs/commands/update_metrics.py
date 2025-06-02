from django.core.management.base import BaseCommand
from edu_programs.models import Program


class Command(BaseCommand):
    help = "Обновление всех показателей"

    def handle(self, *args, **options):
        for program in Program.objects.all():
            program.save()
        self.stdout.write(self.style.SUCCESS("Metrics updated"))
