# Poor Man's Nagios

Extremely simple NRPE-based server monitor -- ideal for monitoring your monitor
server in a small setup.

## Overview

After having set up a small server farm monitored using [Icinga2](https://icinga.com/),
I found myself in need of a simple way to monitor the monitoring server itself.

Not wanting to install and configure an entire second Icinga2 instance just to perform
one simple monitoring action, I wrote this instead.

It implements a simple checking algorithm with a failure threshold, and sends
alert emails via the local SMTP server.

Works for me.

This humble library provides the following:

 * A base ```PoorMansNagios``` class, which handles the monitoring checks and alerting
 * ```PoorMansMailer``` class, which handles sending alert emails
 * ```poor-mans-nagios-cli.py```: Wraps the base class for calling from CLI
 * ```poor-mans-nagios.service```: Example systemd service file.

### Setup

Written in pure Python, 3.x required, no external dependencies.

The library does its work by leveraging the [Nagios NRPE](https://github.com/NagiosEnterprises/nrpe)
framework, so that will need to be properly installed/configured. This library needs access to the
```check_nrpe``` binary, and the monitored server needs a running NRPE daemon with a check configured.

You'll also need a running SMTP server, such as [Postfix](http://www.postfix.org/),
capable of sending emails it receives locally.

### Configuration

 * Copy ```config.sample.yaml``` to ```config.yaml```
 * Edit to taste

### Usage

Execute ```poor-mans-nagios-cli.py --help``` for help.
