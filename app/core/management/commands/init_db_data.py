# app/core/management/commands/init_db_data.py
from django.core.management.base import BaseCommand
from edu_programs.const import POSSIBLE_DEGREES
from edu_programs.models import EduDegree, Faculty, University


class Command(BaseCommand):
    help = "Initialize database with default data (University, Faculties, EduDegrees)"

    def handle(self, *args, **options):
        self.stdout.write("Starting database initialization...")

        # Создаем университет
        university, created = University.objects.get_or_create(
            name="Воронежский государственный университет",
            defaults={"abbreviation": "ВГУ"},
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created University: {university}"))
        else:
            self.stdout.write(self.style.WARNING(f"University already exists: {university}"))

        # Создаем факультеты
        faculties_data = [
            {"name": "Медико-биологический", "abbreviation": "БиоМедФак"},
            {"name": "Военный учебный центр", "abbreviation": "ВУЦ"},
            {"name": "Географии, геоэкологии и туризма", "abbreviation": "ГГиТ"},
            {"name": "Геологический", "abbreviation": "ГеоФак"},
            {"name": "Журналистики", "abbreviation": "ЖурФак"},
            {"name": "Исторический", "abbreviation": "ИстФак"},
            {"name": "Компьютерных наук", "abbreviation": "ФКН"},
            {"name": "Математический", "abbreviation": "МатФак"},
            {"name": "Международных отношений", "abbreviation": "ФМО"},
            {"name": "Прикладной математики, информатики и механики", "abbreviation": "ПММ"},
            {"name": "Романо-германской филологии", "abbreviation": "РГФ"},
            {"name": "Химический", "abbreviation": "ХимФак"},
            {"name": "Фармацевтический", "abbreviation": "Фармацевт"},
            {"name": "Физический", "abbreviation": "ФизФак"},
            {"name": "Филологический", "abbreviation": "ФилФак"},
            {"name": "Философии и психологии", "abbreviation": "ФиПси"},
            {"name": "Экономический", "abbreviation": "Эконом"},
            {"name": "Юридический", "abbreviation": "ЮрФак"},
        ]

        created_faculties = 0
        for data in faculties_data:
            faculty, created = Faculty.objects.get_or_create(
                university=university,
                name=data["name"],
                defaults={"abbreviation": data["abbreviation"]},
            )
            if created:
                created_faculties += 1
                self.stdout.write(self.style.SUCCESS(f"Created Faculty: {faculty}"))

        self.stdout.write(self.style.SUCCESS(f"Created {created_faculties} faculties"))

        # Создаем степени образования

        created_degrees = 0
        for data in POSSIBLE_DEGREES:
            degree, created = EduDegree.objects.get_or_create(
                name=data["name"],
                defaults={"code": data["code"]},
            )
            if created:
                created_degrees += 1
                self.stdout.write(self.style.SUCCESS(f"Created EduDegree: {degree}"))

        self.stdout.write(self.style.SUCCESS(f"Created {created_degrees} education degrees"))
        self.stdout.write(self.style.SUCCESS("Database initialization completed!"))
