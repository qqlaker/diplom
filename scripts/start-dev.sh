#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

create_superuser() {
    echo "Creating superuser..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@test.com', 'admin')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"
}

# Основной скрипт
main() {
    python manage.py migrate
    python manage.py init_db_data
    create_superuser
    python manage.py collectstatic --no-input --clear
    python manage.py runserver 0.0.0.0:8000
}

main
