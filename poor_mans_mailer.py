import logging
import smtplib
from email.mime.text import MIMEText

POOR_MANS_NAGIOS_GIT_URL = "https://github.com/stirlab/poor-mans-nagios"

class PoorMansMailer(object):
    def __init__(self, email_from, logger):
        self.email_from = email_from
        self.logger = logger
        self.debug = self.logger.level == logging.DEBUG

    def send_problem_alert(self, alert_emails, host, check_command):
        subject = '[PROBLEM] %s failed on %s' % (check_command, host)
        self.send(subject, alert_emails)

    def send_recovery_alert(self, alert_emails, host, check_command):
        subject = '[RECOVERY] %s succeeded on %s' % (check_command, host)
        self.send(subject, alert_emails)

    def send(self, subject, recipients):
        with smtplib.SMTP("localhost") as server:
            if self.debug:
                server.set_debuglevel(1)
            msg = MIMEText("Sent from poor-mans-nagios: %s" % POOR_MANS_NAGIOS_GIT_URL)
            msg['Subject'] = subject
            msg['From'] = email_from
            msg['To'] = ", ".join(recipients)
            server.sendmail(self.email_from, recipients, msg.as_string())
