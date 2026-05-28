from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        User = get_user_model
        if not User.object.filter(username='admin').exists():
            User.object.create_superuser(
                username='admin',
                email='admin@gmail.com',
                password='admiin1234'
            )
            self.stdout.write("Superuser created succesfully")
        else:
            self.stdout.write("Superuser already exists")