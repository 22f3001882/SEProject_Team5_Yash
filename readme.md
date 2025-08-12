reqs:
    venv:
     python3 -m venv .venv_qm
     source ./.venv_qm/bin/activate
    Redis:
     sudo apt update && sudo apt install redis
    MailHog: 
     sudo apt-get -y install golang-go
     go install github.com/mailhog/MailHog@latest
    requirements.txt

commands to run
    Mailhog: ~/go/bin/MailHog (now.day == 1(change to today)), prev_month = 3 (change to current month)
    flask app: python3 app.py
    celery worker: celery -A app:celery_app worker -l INFO
    celery beat: celery -A app:celery_app beat -l INFO