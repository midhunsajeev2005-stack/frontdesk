# Frontdesk
A Django/PostgreSQL ticket inbox for Arvo Systems.

## Start on Midhun’s Windows laptop
1. Extract this ZIP into a new folder. Open the extracted Frontdesk folder.
2. Double-click Start-Frontdesk.cmd and enter your frontdesk_app database password. The launcher uses the Python environment in Documents/frontdesk/.venv and PostgreSQL 17. If prompted for Python, enter the full path to that environment’s Scripts/python.exe.
3. The first run prints randomly generated passwords for arvo.agent, arvo.second, and arvo.customer. Save these privately. Open http://127.0.0.1:8000 and sign in as arvo.agent. Leave the terminal open while using the app.
4. Open the sample ticket, take it, send a public reply and add a team note. Open a private browser window and sign in as arvo.customer to see the public reply. Use Wait for customer and then reply from the customer window to restart the timer.

The launcher adds the application's tables to the configured database. Existing Django auth tables are reused. The demo command preserves existing accounts on subsequent runs. To reset a forgotten demo password, use manage.py changepassword with the account name and the same database environment settings.

## Other installations and deployment
Use a supported Python installation and PostgreSQL. Install requirements with python -m pip install -r requirements.txt. Set FRONTDESK_DB_PASSWORD, PGDATABASE, PGUSER, PGHOST, and PGPORT. For local testing set FRONTDESK_LOCAL=1. For production set a stable random DJANGO_SECRET_KEY, ALLOWED_HOSTS (comma-separated domains), and TRUSTED_ORIGINS (comma-separated https origins). Use HTTPS. Configure database TLS as required by your provider, e.g. PGSSLMODE=verify-full with its trusted CA.

Run python manage.py migrate, then python manage.py demo once and save the new credentials. For a local server run python manage.py runserver. For a Linux web host use gunicorn desk.wsgi:application --bind 0.0.0.0:$PORT. Schedule python manage.py close_waiting every five minutes. Opening a ticket or the inbox also processes inactivity closures. Provide reviewer credentials privately. Keep the hosting and database active for at least a week after submission.

## Business decisions
Working time uses Asia/Kolkata, weekdays 09:30–18:30. Set HOLIDAYS to comma-separated ISO dates for the support team's festival calendar. Half a day is 4.5 working hours, a week is 45. An after-hours urgent ticket must be fixed by the end of the next working day. Priority changes restart outstanding targets at the new priority and preserve a recorded first reply. Waiting pauses the service clocks and five working days of customer silence closes the ticket. Customer reopening is available for seven calendar days after resolution. Reopening starts a fresh fix target. After inactivity closure a customer can create a new ticket. Replies are delivered in the authenticated customer portal.

Agent actions lock the ticket row, validate ownership and append a timestamped event in the same transaction. The customer history query selects an explicit allowlist of public event kinds. A PostgreSQL trigger rejects updates, deletes and truncation of the event log. Database administrators control the schema.

## Verification and completion note
Run python -m unittest test_calendar for the calendar tests. Run python manage.py test desk using a PostgreSQL test account authorized to create a disposable test database. The Django tests cover concurrent claims, customer isolation, note privacy and immutable reply history.

Calendar tests passed and all Python source compiled in the build environment. Django/PostgreSQL integration and the Windows launcher still need runtime verification because those dependencies were unavailable there. No email gateway, export or external API is included. The public URL, hosted database, scheduled job and repository must be set up by the submitter with their hosting accounts. Submit the verified live URL, repository, README and a completion note updated with your actual test and deployment results.
