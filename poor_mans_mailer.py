import logging
import smtplib
from smtplib import SMTPRecipientsRefused, SMTPHeloError, SMTPSenderRefused, SMTPDataError, SMTPNotSupportedError
from email.mime.text import MIMEText

POOR_MANS_NAGIOS_GIT_URL = "https://github.com/stirlab/poor-mans-nagios"

class PoorMansMailer(object):
    def __init__(self, email_from, logger):
        self.email_from = email_from
        self.logger = logger
        self.debug = self.logger.level == logging.DEBUG

    def alert_problem(self, alert_emails, host, check_command):
        subject = '[PROBLEM] %s failed on %s' % (check_command, host)
        return self.send(subject, alert_emails)

    def alert_recovery(self, alert_emails, host, check_command):
        subject = '[RECOVERY] %s succeeded on %s' % (check_command, host)
        return self.send(subject, alert_emails)

    def send(self, subject, recipients):
        with smtplib.SMTP("localhost") as server:
            if self.debug:
                server.set_debuglevel(1)
            msg = MIMEText("Sent from poor-mans-nagios: %s" % POOR_MANS_NAGIOS_GIT_URL)
            msg['Subject'] = subject
            msg['From'] = self.email_from
            msg['To'] = ", ".join(recipients)
            try:
                server.sendmail(self.email_from, recipients, msg.as_string())
                return True
            except (SMTPRecipientsRefused, SMTPHeloError, SMTPSenderRefused, SMTPDataError, SMTPNotSupportedError) as err:
                message = err.message if hasattr(err, 'message') else str(err)
                self.logger.error("Mailer exception: %s" % err)
                return False
