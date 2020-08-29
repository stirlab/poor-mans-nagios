#!/usr/bin/env python3

import os
import time
import yaml
import logging
import pprint
from poor_mans_mailer import PoorMansMailer

logging.basicConfig(level=logging.INFO)
pp = pprint.PrettyPrinter(indent=4)

DEFAULT_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DEFAULT_CONFIG_FILE = "%s/config.yaml" % DEFAULT_SCRIPT_DIR

class PoorMansNagios(object):

    def __init__(self, config_file=None, args={}):
        self.config = self.parse_config(config_file or DEFAULT_CONFIG_FILE)
        self.config.update(args)
        self.defaults = self.config['defaults']
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

    def execute_check(self):
        data = self.get_cluster_master()
        if data:
            needs_update, hostname, port, slave_hosts = self.master_needs_update(data)
            if needs_update:
                self.logger.info("Master %s:%d exists, needs update, with slaves: %s" % (hostname, port, slave_hosts))
            return needs_update, hostname, port, slave_hosts
        return result

    def next_action(self, result):
        sleep_seconds = self.auto_update_interval_seconds
        if needs_update and self.checks >= self.auto_update_check_threshold:
            self.logger.info("Master needs update and passed check_threshold %d, setting writable" % self.auto_update_check_threshold)
            self.set_instance_writeable(hostname, port)
            sleep_seconds *= self.auto_update_check_threshold
        self.logger.debug("Waiting %d seconds before next check" % sleep_seconds)
        time.sleep(sleep_seconds)

    def monitor(self):
        self.logger.info("Starting poor-mans-nagios with check_interval: %d, retry_interval: %d, failure_threshold: %d" % (self.check_interval, self.retry_interval, self.failure_threshold))
        try:
            while True:
                result = self.execute_check()
                self.next_action(result)
        except KeyboardInterrupt:
            self.logger.warning('Process interrupted')
