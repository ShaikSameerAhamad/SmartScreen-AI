import csv
from django.core.management.base import BaseCommand
from core.models import JobRole

class Command(BaseCommand):
    help = 'Loads job roles from a specified CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='The full path to the CSV file to be loaded.')

    def handle(self, *args, **kwargs):
        file_path = kwargs['csv_file_path']
        self.stdout.write(f"Loading job roles from {file_path}...")

        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                loaded_count = 0
                for row in reader:
                    # Using get_or_create to avoid duplicating roles
                    job_role, created = JobRole.objects.get_or_create(
                        name=row['name'],
                        defaults={
                            'category': row['category'],
                            'full_description': row['full_description'],
                            'required_skills': row['required_skills']
                        }
                    )
                    if created:
                        loaded_count += 1
                        self.stdout.write(f"  + Created new role: {job_role.name}")
                
            self.stdout.write(self.style.SUCCESS(f'Successfully loaded {loaded_count} new job roles.'))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Error: The file "{file_path}" was not found.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'An unexpected error occurred: {e}'))
