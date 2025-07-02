import csv
from django.core.management.base import BaseCommand
from core.models import LearningResource

class Command(BaseCommand):
    help = 'Loads learning resources from a specified CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='The full path to the CSV file to be loaded.')

    def handle(self, *args, **kwargs):
        file_path = kwargs['csv_file_path']
        self.stdout.write(f"Loading learning resources from {file_path}...")

        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                created_count = 0
                updated_count = 0

                for row in reader:
                    skill_name = row['skill_name'].lower().strip() # Ensure skill name is clean and lowercase
                    
                    # Use update_or_create to either add new resources or update existing ones
                    obj, created = LearningResource.objects.update_or_create(
                        skill_name=skill_name,
                        defaults={
                            'definition': row.get('definition', ''),
                            'youtube_link': row.get('youtube_link', ''),
                            'course_link': row.get('course_link', ''), # Assumes you might add this column later
                            'resume_bullet_template': row.get('resume_bullet_template', '')
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                
            self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} and updated {updated_count} learning resources.'))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Error: The file "{file_path}" was not found.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'An unexpected error occurred: {e}'))

