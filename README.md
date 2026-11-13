Kona Swim Hub is a space for families based in Kona, Hawaii to find and sign up for swim lessons for their kids and for Kona-based instructors to post swim classes.

The problem this app solves: Many local swim instructors have too small of a presence to justify creating
their own website. Because of this, families use word of mouth to find group swim lessons. Swim lessons must be specific to the the learner's age, ability level, schedule, location, etc., so it is common for a lot of back-and-forth to take place between instructors and families just to
get a child enrolled in a swim course. Kona Swim Hub seeks to streamline this process.

App Features Implemented:

- Create an account
- Change account password
- Create, update, and delete a learner
- Create, update, and read a course
- Register for a course
- Each user has an account dashboard that displays their learners and course rosters.
- When a class roster is full, families are able to join a waitlist.
- Instructors can move waitlisted learners onto their course roster when there is space.
- Instructors can send a message to the parents of children on their rosters.
- Families can send a message to their child's swim instructor.

App Features in Development:

- Instructors will be able to unenroll a learner from one of their courses.
- Families will be able to pay for their swim classes through the app.
- Users will be able to filter the available courses by age, location, etc.
- Users will be able to create a profile page for others to view.

## Run with Docker

Copy `.env.docker.example` to `.env.docker` and set a secret key and database URL. Keep `.env.docker` private; it is ignored by Git. For local-only use, SQLite is sufficient. For a Neon test, use its pooled connection URL and do not commit it.

Build and start the app:

```sh
cp .env.docker.example .env.docker
docker compose build
docker compose run --rm web python manage.py migrate
docker compose up
```

Open http://localhost:8000. The `/healthz/` endpoint is available for container health checks. The image collects static files during build and runs Gunicorn as a non-root user. Database migrations are intentionally not run at container startup; apply them as a separate, reviewed operation.

The Compose service targets `linux/amd64` for Lightsail Container Services. The Lightsail deployment needs `SECRET_KEY`, `DATABASE_URL`, the Lightsail hostname in `ALLOWED_HOSTS_EXTRA`, and any production email and Turnstile settings. Put HTTPS origins in `CSRF_TRUSTED_ORIGINS_EXTRA` including the `https://` scheme.

For Lightsail, configure the container health check path as `/healthz/`. After the service is running, create and DNS-validate a Lightsail certificate for `konaswimhub.com` and `www.konaswimhub.com`, attach it to the service, and add domain assignments. Update DNS only after the new service passes testing; record targets are provided by Lightsail and depend on where DNS is hosted.
