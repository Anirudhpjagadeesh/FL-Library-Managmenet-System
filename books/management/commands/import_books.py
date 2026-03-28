import csv
import os
from django.core.management.base import BaseCommand
from books.models import Book, Author, Category

class Command(BaseCommand):
    help = 'Import books from a CSV file'

    def handle(self, *args, **options):
        csv_file_path = 'books_data.csv'
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'File {csv_file_path} not found'))
            return

        # Create a default category if it doesn't exist
        default_category, _ = Category.objects.get_or_create(name='General')

        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            count = 0
            for row in reader:
                flb_id = row.get('BOOK_ID', '').strip()
                title = row.get('BOOK_NAME', '').strip()
                author_name = row.get('AUTHOR', '').strip() or 'Unknown'
                
                if not title:
                    continue

                # Get or create author
                author, _ = Author.objects.get_or_create(name=author_name)

                # Check if book already exists by title
                book = Book.objects.filter(title__iexact=title).first()
                
                if not book:
                    Book.objects.create(
                        title=title,
                        flb_id=flb_id,
                        author=author,
                        category=default_category,
                        total_copies=1,
                        available_copies=1
                    )
                    count += 1
                    self.stdout.write(self.style.SUCCESS(f'Imported: {title} ({flb_id})'))
                else:
                    # Update flb_id if it's missing
                    if not book.flb_id:
                        book.flb_id = flb_id
                        book.save()
                        self.stdout.write(self.style.SUCCESS(f'Updated FLB_ID for: {title} ({flb_id})'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Skipped (already exists): {title}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} books'))
