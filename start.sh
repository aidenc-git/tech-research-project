#!/bin/bash

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting gunicorn..."
gunicorn portal.wsgi --bind 0.0.0.0:$PORT
```

**2.3 Save the file**

**Step 3: Update your Procfile**

Replace the content of `Procfile` with just:
```
web: bash start.sh