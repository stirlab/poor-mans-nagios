#!/usr/bin/env python3

import os
import time
import subprocess
import yaml
import logging
import pprint
from poor_mans_mailer import PoorMansMailer

logging.basicConfig(level=logging.INFO)
pp = pprint.PrettyPrinter(indent=4)

DEFAULT_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DEFAULT_CONFIG_FILE = "%s/config.yaml" % DEFAULT_SCRIPT_DIR
DEFAULT_CHECK_INTERVAL = 5
DEFAULT_RETRY_INTERVAL = 1
DEFAULT_FAILURE_THRESHOLD = 5
DEFAULT_NRPE_BINARY = "/usr/lib/nagios/plugins/check_nrpe"

class PoorMansNagios(object):

    def __init__(self, config_file=None, args={}):
        self.config = self.parse_config(config_file or DEFAULT_CONFIG_FILE)
        self.config.update(args)
        self.quiet = 'quiet' in self.config and self.config['quiet']
        self.debug = 'debug' in self.config and self.config['debug']
        self.logger = logging.getLogger(self.__class__.__name__)
        self.log_level = self.logger.level
        if self.quiet:
            self.enable_quiet()
        if self.debug:
            self.enable_debug()
            self.logger.debug('Config:')
            pp.pprint(self.config)
        self.build_configuration()
        self.mailer = PoorMansMailer(self.email_from, self.logger)
        self.reset_on_check_ok()

    def default_loglevel(self):
        self.logger.setLevel(self.log_level)

    def enable_debug(self):
        self.logger.setLevel(logging.DEBUG)

    def enable_quiet(self):
        self.logger.setLevel(logging.ERROR)

    def parse_config(self, config_file):
        with open(config_file, 'r') as stream:
            try:
                config = yaml.safe_load(stream)
            except yaml.YAMLError as err:
                raise RuntimeError("Could not load config file %s: %s" % (config_file, err))
            return config

    def build_configuration(self):
        pmn_config = self.config['poor-mans-nagios']
        nrpe_config = self.config['nrpe']
        try:
            self.nrpe_binary = pmn_config['nrpe-binary']
        except KeyError:
            self.nrpe_binary = DEFAULT_NRPE_BINARY
        try:
            self.check_interval = pmn_config['check-interval']
        except KeyError:
            self.check_interval = DEFAULT_CHECK_INTERVAL
        try:
            self.retry_interval = pmn_config['retry-interval']
        except KeyError:
            self.retry_interval = DEFAULT_RETRY_INTERVAL
        try:
            self.failure_threshold = pmn_config['failure-threshold']
        except KeyError:
            self.failure_threshold = DEFAULT_FAILURE_THRESHOLD
        try:
            self.alert_on_recovery = pmn_config['alert-on-recovery']
        except KeyError:
            self.alert_on_recovery = True
        try:
            self.alert_emails = pmn_config['alert-emails']
        except KeyError:
            self.alert_emails = []
        self.email_from = pmn_config['email-from']
        self.checked_host = nrpe_config['host']
        self.check_command = nrpe_config['command']

    def set_sleep_seconds(self, minutes):
        self.sleep_seconds = minutes * 60

    def reset_on_check_ok(self):
        self.logger.info("Resetting tracking on recovery")
        self.fail_count = 0
        self.alert_sent = False
        self.set_sleep_seconds(self.check_interval)

    def check_failure_threshold(self):
        return self.fail_count >= self.failure_threshold

    def handle_failure(self):
        self.fail_count += 1
        self.logger.debug("Current fail count: %d, failure threshold: %d" % (self.fail_count, self.failure_threshold))
        if self.check_failure_threshold():
            self.logger.warning("Check %s for host %s over failure threshold" % (self.check_command, self.checked_host))
            if self.alert_sent:
                self.logger.debug("Alerts already sent for this failure, skipping")
            else:
                result = self.send_problem_alert()
                if result:
                    self.alert_sent = True

    def handle_recovery(self):
        if self.alert_sent:
            self.logger.info("Service recovered")
            self.reset_on_check_ok()
            self.send_recovery_alert()

    def send_problem_alert(self):
        self.logger.warning("Sending problem alert to: %s" % ", ".join(self.alert_emails))
        return self.mailer.alert_problem(self.alert_emails, self.checked_host, self.check_command)

    def send_recovery_alert(self):
        if self.alert_on_recovery:
            self.logger.info("Sending recovery alert to: %s" % ", ".join(self.alert_emails))
            return self.mailer.alert_recovery(self.alert_emails, self.checked_host, self.check_command)

    def run_shell_command(self, command, capture_output=True):
        kwargs = {}
        if capture_output:
            kwargs.update({
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'universal_newlines': True,
            })
        try:
            proc = subprocess.Popen(command, **kwargs)
            stdout, stderr = proc.communicate()
            returncode = proc.returncode
        except Exception as e:
            stdout = ''
            stderr = e.message if hasattr(e, 'message') else str(e)
            returncode = 1
        return returncode, stdout, stderr

    def build_command_args(self):
        args = [
            self.nrpe_binary,
        ]
        for arg, val in self.config['nrpe'].items():
            args.append("--%s" % arg)
            if val is not True:
                args.append(val)
        return args

    def execute_check(self):
        command = self.build_command_args()
        self.logger.debug("Running check command: %s" % " ".join(command))
        returncode, stdout, stderr = self.run_shell_command(command)
        if returncode == 0:
            self.logger.debug("Check %s on host %s succeeded" % (self.check_command, self.checked_host))
            self.handle_recovery()
            return True
        self.logger.warning("Check %s on host %s failed, stdout: %s, stderr: %s" % (self.check_command, self.checked_host, stdout, stderr))
        self.handle_failure()
        return False

    def configure_next_action(self, success):
        if success:
            self.set_sleep_seconds(self.check_interval)
        else:
            self.set_sleep_seconds(self.retry_interval)
        self.logger.debug("Set interval to %d seconds" % self.sleep_seconds)

    def monitor(self):
        self.logger.info("Starting poor-mans-nagios with check_interval: %d, retry_interval: %d, failure_threshold: %d" % (self.check_interval, self.retry_interval, self.failure_threshold))
        try:
            while True:
                success = self.execute_check()
                self.configure_next_action(success)
                self.logger.debug("Sleeping %d seconds" % self.sleep_seconds)
                time.sleep(self.sleep_seconds)
        except KeyboardInterrupt:
            self.logger.warning('Process interrupted')
