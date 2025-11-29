import os
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMultiAlternatives, get_connection
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Sends a mass email to all registered users.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--subject',
            type=str,
            required=True,
            help='Subject of the email',
        )
        parser.add_argument(
            '--html-file',
            type=str,
            required=True,
            help='Path to the HTML file to use as the email body',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate sending without actual delivery',
        )

    def handle(self, *args, **options):
        subject = options['subject']
        html_file_path = options['html_file']
        dry_run = options['dry_run']

        if not os.path.exists(html_file_path):
            raise CommandError(f'HTML file not found: {html_file_path}')

        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            raise CommandError(f'Error reading HTML file: {e}')

        # Strip HTML tags for the text version (basic fallback)
        # For a better text version, one might use a library like html2text, 
        # but for now we'll just use a simple message or the raw HTML if acceptable,
        # or just a placeholder. Let's use a placeholder or simple strip.
        text_content = "This email contains HTML content. Please enable HTML to view it."

        users = User.objects.filter(is_active=True).exclude(email='')
        total_users = users.count()

        self.stdout.write(f'Found {total_users} active users with email addresses.')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN: No emails will be sent.'))
            self.stdout.write(f'Subject: {subject}')
            self.stdout.write(f'Body (first 100 chars): {html_content[:100]}...')
            return

        # Use a single connection for efficiency
        connection = get_connection()
        connection.open()

        messages = []
        for user in users:
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                connection=connection,
            )
            msg.attach_alternative(html_content, "text/html")
            messages.append(msg)

        # Send messages in chunks to avoid memory issues if there are many users
        # But send_mass_mail or connection.send_messages handles lists.
        # For very large lists, batching is better.
        
        batch_size = 100
        sent_count = 0
        
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            try:
                count = connection.send_messages(batch)
                sent_count += count
                self.stdout.write(f'Sent batch {i // batch_size + 1}: {count} emails')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error sending batch {i // batch_size + 1}: {e}'))

        connection.close()

        self.stdout.write(self.style.SUCCESS(f'Successfully sent {sent_count} emails.'))
