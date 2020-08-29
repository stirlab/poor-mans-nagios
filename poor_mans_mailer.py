import smtplib
from email.mime.text import MIMEText

class PoorMansMailer(object):
    sender = 'admin@example.com'
    receiver = 'info@example.com'

    msg = MIMEText('This is test mail')


  problem-subject: '[PROBLEM] %command failed on %host'
  recovery-subject: '[RECOVERY] %command succeeded on %host'
    msg['Subject'] = 'Test mail'
    msg['From'] = 'admin@example.com'
    msg['To'] = 'info@example.com'

    user = 'username'
    password = 'passoword'

    with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:

        server.login(user, password)
        server.sendmail(sender, receiver, msg.as_string())
        print("mail successfully sent")
