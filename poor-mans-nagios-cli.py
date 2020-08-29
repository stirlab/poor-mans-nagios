#!/usr/bin/env python3

import argparse
from poor_mans_nagios import PoorMansNagios, DEFAULT_CONFIG_FILE

def main():
    parser = argparse.ArgumentParser(description="Run poor-mans-nagios from CLI")
    parser.add_argument("--debug", action='store_true', help="Enable debugging")
    parser.add_argument("--quiet", action='store_true', help="Silence output except for errors")
    parser.add_argument("--config-file", type=str, metavar="FILE", default=DEFAULT_CONFIG_FILE, help="Configuration filepath, default: %s" % DEFAULT_CONFIG_FILE)
    args = vars(parser.parse_args())
    config_file = args.pop('config_file')
    pmn = PoorMansNagios(config_file, args)
    pmn.monitor()

if __name__ == "__main__":
    main()
