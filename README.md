# Mini Project 6 - Django Study Planner

INF601 - Advanced Programming in Python  

Nicholas Pollard

## What this project does

Study Planner is a Django web application that helps students organize their courses and assignments. A user can create an account, sign in, add courses, record assignments and due dates, and mark work complete as it is finished. The dashboard shows what is coming up, what is overdue, and how much work has been completed.

Each user has a separate set of courses and assignments. The application uses Django's built-in authentication, forms, ORM, and admin interface, along with Bootstrap for its layout and styling.

## Main features
- **Registration and login:** Create an account, sign in, and log out using Django's authentication system.
- **Personal dashboard:** View total, completed, pending, and overdue assignment counts, upcoming work, and a course summary.
- **Course management:** Create, view, edit, and delete courses with a course code, name, and optional description.
- **Assignment management:** Add assignments to courses, provide descriptions and due dates, edit or delete them, and mark them complete or incomplete.
- **Assignment filters:** Switch between All, Pending, Completed, and Overdue assignments.
- **Assignment search:** Search assignment titles, descriptions, course names, and course codes without worrying about capitalization. Search works together with the status filters and only looks through the signed-in user's assignments.
- **Bootstrap interface:** Shared navigation, responsive layouts, form styling, status badges, and a working deletion-confirmation modal.
- **Django admin:** Manage courses and assignments with searchable lists, filters, organized entry fields, and read-only timestamps.
- **Automated tests:** Test models, forms and views, authentication, admin permissions, configuration, and security-related behavior.

## Pages and how to use the application

The public pages are **Home**, **About**, **Features**, **Help**, **Register**, and **Login**. They share a common Bootstrap layout through `templates/base.html`.

After registering or logging in, a user can:
1. Open **My Courses** and add a course. Each course has a name and code; its description is optional. Course codes are saved in uppercase, and the same user cannot create two courses with the same code.
2. Open a course to see its assignments or select **My Assignments** to view assignments across all courses.
3. Add an assignment, select one of their own courses, and enter a title and due date. The description and completed status are optional.
4. Mark assignments complete or incomplete, edit their details, or filter the assignment list by status. Use the search bar on **My Assignments** to find work by title, description, course name, or course code. A search can be combined with a status filter; use **Clear** to remove the search without changing that filter.
5. Use the **Dashboard** to review completed, pending, overdue, and upcoming work.
6. Use the **Delete** button and Bootstrap confirmation modal when removing a course or assignment. Deleting a course also deletes its associated assignments.

Users can only view and manage records associated with their own accounts. The administrative interface is separate from the normal student pages and requires the appropriate Django staff permissions.

## Project structure

```text
miniproject6NicholasPollard/
    config/
        __init__.py
        settings.py
        urls.py
        asgi.py
        wsgi.py
    planner/
        migrations/
            __init__.py
            0001_initial.py
        tests/
            __init__.py
            helpers.py
            test_admin.py
            test_assignment_views.py
            test_assignment_search.py
            test_auth.py
            test_course_views.py
            test_models.py
            test_security.py
            test_settings.py
            test_views.py
        __init__.py
        admin.py
        apps.py
        forms.py
        models.py
        urls.py
        views.py
    templates/
        base.html
        registration/
            login.html
            register.html
        planner/
            home.html
            about.html
            features.html
            help.html
            dashboard.html
            course_list.html
            course_detail.html
            course_form.html
            assignment_list.html
            assignment_form.html
            includes/
                assignment_table.html
                delete_modal.html
                form_fields.html
    static/
        css/
            style.css
        js/
            delete-modal.js
    .env.example
    .gitignore
    manage.py
    requirements.txt
    README.md
```

The main project files are:
- `config/settings.py` — Django settings for the database, templates, authentication redirects, static files, and environment-based security configuration.
- `config/urls.py` — Top-level URL routing for the planner application and Django admin.
- `planner/models.py` — The `Course` and `Assignment` database models and relationship validation.
- `planner/forms.py` — Registration, login, course, and assignment forms with Bootstrap styling and user-specific choices.
- `planner/views.py` and `planner/urls.py` — Public and private pages, dashboard calculations, assignment filtering and searching, and create/edit/delete actions.
- `planner/admin.py` — Customized Django admin displays and entry forms.
- `planner/migrations/0001_initial.py` — The initial database schema for the planner models.
- `templates/` — Shared page layout, authentication screens, individual pages, and reusable template sections.
- `static/` — Custom CSS and JavaScript for the deletion modal.
- `planner/tests/` — Automated Django test cases, including `test_assignment_search.py` for search behavior and account isolation.
- `requirements.txt` — Python dependencies used by the application.
- `.env.example` — Example configuration values without actual credentials or secret keys.

The `.venv/` virtual environment, `.env` secrets file, local `db.sqlite3` database, and generated `staticfiles/` folder are excluded from Git.

## Requirements
- Python 3.12 or 3.13
- Django 5.2.18
- python-dotenv 1.2.4
- WhiteNoise 6.12.0
- SQLite (included with Python)
- Internet access for the Bootstrap 5 CDN assets used in the templates

The complete dependency list, including Django's support packages, is in `requirements.txt`.

## Local setup on Windows

The following commands use **PowerShell** and assume you are working from the project folder.

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Configure the environment

Copy the example configuration:

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder `DJANGO_SECRET_KEY` value with a unique random Django secret key. You can generate one using the following command; keep the result private:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Use these local development settings in `.env` (in addition to the generated secret key):

```dotenv
DJANGO_SECRET_KEY=your-unique-generated-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=
DJANGO_SECURE_COOKIES=False
```

The secret key shown above is only a placeholder. Do not use it as an actual key, and do not commit `.env` to GitHub.

### 4. Initialize the database

```powershell
python manage.py makemigrations
python manage.py migrate
```

The initial planner migration is already included in the repository. `makemigrations` checks for model changes and creates new migration files if the schema is changed later; `migrate` applies migrations to the local database.

### 5. Create an administrator account (optional)

```powershell
python manage.py createsuperuser
```

Use a strong password. The Django admin is available at `/admin/` after the server starts.

### 6. Start the development server

```powershell
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in a browser. Register a normal account, add a course, and then add assignments. Press `Ctrl+C` in the terminal to stop the local server.

## Deployment on the INF601 Linux dev box

The course provides a Linux dev box and a separate HTTPS site address. The code is developed locally, pushed to GitHub, and then installed and run on the assigned Linux box. The instructor's instructions require Django to listen on all interfaces on port **8000** and remain running inside **tmux**.

### 1. Clone the repository and install dependencies

After signing into the assigned dev box and opening its terminal:

```bash
cd ~
git clone https://github.com/nicholaslpollard/miniproject6NicholasPollard.git
cd miniproject6NicholasPollard
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

For later updates, use `git pull --ff-only origin main` from the project folder rather than cloning again.

### 2. Create a private server configuration

Copy `.env.example` to `.env`, generate a **new** random server secret key, and update the settings. The following example shows the required public configuration values, not a real secret:

```dotenv
DJANGO_SECRET_KEY=your-separate-unique-server-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=dev-student17.fhsucyber.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://dev-student17.fhsucyber.com
DJANGO_SECURE_COOKIES=True
```

Do not reuse or publish the private development key. Keep `.env` out of Git and restrict its file permissions on Linux, for example with `chmod 600 .env`. The hostname in these settings is the assigned course site, not the address of the terminal login page.

### 3. Apply migrations and collect static files

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check
```

WhiteNoise serves the collected CSS, JavaScript, and Django admin static files even with `DEBUG=False`. Bootstrap's CSS and JavaScript are loaded separately from a CDN.

### 4. Create a Django administrator account

```bash
python manage.py createsuperuser
```

The Django administrator login is separate from the course dev-box and site-front-door credentials. Never put either password in the source files or README.

### 5. Run the server inside tmux

```bash
tmux new -A -s work
cd ~/miniproject6NicholasPollard
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

Open `https://dev-student17.fhsucyber.com` and pass the instructor's site password prompt to view the application. The Django admin is under `/admin/` on that site.

To leave the server running after closing the browser terminal, detach from tmux with **Ctrl+B**, then **D**. Reconnect later with `tmux attach -t work`.

The server's HTTPS connection is handled by the course reverse proxy. The application intentionally does not enable Django's own forced HTTPS redirects or HSTS until the proxy configuration is verified. Django's `runserver` is used here because the instructor specifically requires it; it is not an appropriate production server for an internet-facing commercial application.

## Database models

### Course

Each `Course` has an owner, name, code, optional description, and creation/update timestamps. Course codes are normalized to uppercase. A database constraint prevents duplicate codes **within one user's account** while allowing different users to have the same code.

### Assignment

Each `Assignment` has an owner, a related course, title, optional description, required due date, completion status, and creation/update timestamps. Assignments are ordered by due date and can be marked complete or incomplete. An assignment's owner must match the owner of its course.

The model and form validation checks help prevent mismatched ownership. Deleting a user removes their associated courses and assignments, while deleting a course removes its assignments through Django's cascade relationship.

## Security and user privacy

The application uses the following protections:
- Django's built-in password hashing, password validation, session handling, login, and logout views.
- `@login_required` on private pages, with individual course and assignment lookups filtered by `owner=request.user`. The assignment search further filters this user-specific queryset rather than searching across other accounts.
- Course and assignment forms that do not accept an owner field from the browser. The forms assign ownership from the authenticated user and restrict course choices to the user's own courses.
- CSRF protection on submitted forms; deletion, completion toggles, and logout require POST requests.
- Django's ORM and standard template autoescaping instead of manually constructed SQL or unescaped user content.
- Validation for duplicate course codes and for assignment/course ownership relationships.
- Safe handling of user-supplied redirect destinations.
- An environment-based Django secret key, a restricted `ALLOWED_HOSTS` setting, and secure session/CSRF cookies for HTTPS deployment.
- Django admin access controls and model entry validation.

The automated tests include cross-account access attempts, forged form data, rejected CSRF requests, and protections against modifying records using GET requests. No application can be guaranteed vulnerability-free. This course project does not include application-level login rate limiting or a password-reset flow, and the course deployment uses Django's development server behind the provided proxy.

## Testing

Django's built-in test runner is used. From the project root with the environment configured and virtual environment activated, run:

```bash
python manage.py check
python manage.py makemigrations --check
python manage.py test
```

The test suite covers:
- Course and assignment models, required fields, relationships, and owner consistency.
- Customized Django admin pages, searching, filtering, and permissions.
- Registration, login, logout, and account-permission checks.
- Course and assignment creation, editing, deletion, completion toggling, and filtering.
- Assignment searching by title, description, course name, and course code; case-insensitive matching; combining search with status filters; no-results messages; and account isolation.
- Access restrictions between separate user accounts and forged ownership submissions.
- CSRF handling, safe redirects, template escaping, and state-changing HTTP methods.
- Deployment settings, WhiteNoise configuration, and secure-cookie behavior.

**Last verified result:** 168 tests passed locally on Windows using Python 3.12.5 and Django 5.2.18, with no Django system-check issues and no new migrations required. This includes 12 new assignment-search tests. Before the search addition, 156 tests also passed on the Linux dev box using Python 3.13.14. The 168-test version has not yet been reported as verified on Linux. Automated tests do not guarantee that every possible security issue has been found.

The Home and About pages were also opened in the course site's browser interface to confirm that the live site loaded and Bootstrap styling appeared correctly.

## AI Usage

### What I used AI for

I used **Claude Code** in Visual Studio Code to help develop the Django application in stages. It assisted with the project structure, models, forms, views, authentication, templates, Bootstrap styling, Django admin, automated tests, and deployment configuration. Claude Code also ran checks, helped identify and correct problems found during development, and reported test results after each stage. AI assistance was also used to help draft and organize the project documentation.

### What I did myself

I created the local project folder and GitHub repository, set up the Python virtual environment, installed dependencies, reviewed the development results, made and pushed the project commits, and set up the application on the assigned Linux dev box. I configured the server environment, ran database migrations and tests, started the Django server in tmux, and checked the live Home and About pages in the browser. I also manually incorporated the assignment-search changes, added the new test file, and ran the expanded test suite.

### What I changed

My main functional change was adding an **Assignment Search** feature to the My Assignments page. I updated `planner/views.py` to read a search term and use Django ORM `Q` expressions to match assignment titles, descriptions, course names, and course codes. I modified `templates/planner/assignment_list.html` to add the Bootstrap search form, a Clear button, and a useful message when there are no matches. I kept the existing All, Pending, Completed, and Overdue filters working with the search and preserved the existing `owner=request.user` restriction.

I also added `planner/tests/test_assignment_search.py` covering search matches, filtering, case-insensitive searches, safe handling of search text, and isolation between user accounts. I ran the full local suite and confirmed that all 168 tests passed.

Separately, after reviewing the site's appearance, I removed the course-project footer from the shared `base.html` template so course information would not be repeated at the bottom of every page. 

## Repository and submission

The source code is maintained on the `main` branch:

https://github.com/nicholaslpollard/miniproject6NicholasPollard

The assignment submission is the GitHub repository URL rather than a file upload. The repository contains the application source, migration, templates, tests, `requirements.txt`, and `README.md`. Private `.env` files and local databases are not committed.
