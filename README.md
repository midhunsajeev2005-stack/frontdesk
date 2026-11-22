# Frontdesk

Frontdesk is a Django and PostgreSQL support inbox. Customers submit tickets and reply in the portal. Agents claim tickets, send public replies, write private notes and track working-time deadlines.

[Open the hosted app](https://frontdesk-owvy.onrender.com) · [Completion note](COMPLETION_NOTE.md)

## Run locally

1. Install Python 3.12 or newer and PostgreSQL 17. Clone this repository and open a terminal in the directory containing `manage.py`.
2. In PostgreSQL, connect as an administrator using psql. Create a login and an empty database for this application. The password prompt keeps the password out of the SQL command.

   ```sql
   CREATE ROLE frontdesk_app LOGIN;
   \password frontdesk_app
   CREATE DATABASE frontdesk OWNER frontdesk_app;
   ```

3. Create a virtual environment with `python -m venv .venv`. Activate it with `.venv\Scripts\activate.bat` in Windows Command Prompt or `source .venv/bin/activate` on macOS/Linux. Run `python -m pip install -r requirements.txt`.
4. On Windows, run `Start-Frontdesk.cmd` and enter the database password. On macOS/Linux, run the following in Bash.

   ```bash
   export FRONTDESK_LOCAL=1
   read -rs -p "Database password: " FRONTDESK_DB_PASSWORD
   echo
   export FRONTDESK_DB_PASSWORD
   python manage.py migrate && python manage.py demo && python manage.py runserver
   ```

5. Open http://127.0.0.1:8000. On first setup the demo command prints the passwords for arvo.agent, arvo.second and arvo.customer. Save them privately. Use a separate browser session for the customer. To reset a password, run `python manage.py changepassword arvo.agent` in the same database environment.

The local defaults are database `frontdesk`, user `frontdesk_app`, host `localhost` and port `5432`. Override them with PGDATABASE, PGUSER, PGHOST and PGPORT.

## Hosting

Install requirements and configure the database variables above plus FRONTDESK_DB_PASSWORD. Leave FRONTDESK_LOCAL unset. Set a stable random DJANGO_SECRET_KEY, ALLOWED_HOSTS to the public hostname, and TRUSTED_ORIGINS to the HTTPS origin. Configure database TLS for the provider. Run migrations and initialize demo accounts against the hosted database. Start the service with `gunicorn desk.wsgi:application --bind 0.0.0.0:$PORT`. Schedule `python manage.py close_waiting` every five minutes. Loading the inbox or ticket page also processes inactivity closures. Share the hosted demo credentials privately with reviewers.

## Deadline rules

Working hours are 09:30–18:30 Monday through Friday in Asia/Kolkata. Set HOLIDAYS to comma-separated ISO dates. A half day is 4.5 working hours. Urgent fixes fall due at the end of the current working day, or the next working day for after-hours arrivals. Priority changes restart outstanding targets when the priority changes. Completed first replies retain their deadline. History records the old and new priority, first-reply deadline and resolution deadline. While waiting, stored deadlines exclude the ongoing pause until the clock resumes. Five working days of customer silence close a waiting ticket. Customers can reopen a resolved ticket for seven calendar days, starting a new resolution target.

## Tests

Run `python -m unittest test_calendar` for working-time calculations. Run `python manage.py test desk` with the local environment configured and a PostgreSQL test role allowed to create a disposable test database.

## Health monitoring

After deployment, point an HTTPS uptime monitor at /healthz on the public host and require HTTP 200. The endpoint checks database connectivity and returns 503 on a database connection error. Keep the monitor active for the entire review window.
