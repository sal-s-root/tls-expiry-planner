#!/usr/bin/env python3
"""Calculate a certificate renewal deadline relative to an explicit evaluation time."""
import argparse
import collections
import configparser
import datetime
import fnmatch
import hashlib
import ipaddress
import itertools
import json
import math
import re
import statistics
import sys
import urllib.parse


def evaluate(data):
    """Evaluate supplied infrastructure metadata without changing remote systems."""
    if not isinstance(data, dict):
        raise ValueError("input must be a JSON object")
    now = datetime.datetime.fromisoformat(data['as_of'].replace('Z','+00:00'))
    expiry = datetime.datetime.fromisoformat(data['expires_at'].replace('Z','+00:00'))
    if now.tzinfo is None or expiry.tzinfo is None:
        raise ValueError('timestamps require a timezone')
    days = math.floor((expiry-now).total_seconds()/86400)
    lead = int(data.get('renew_before_days', 30))
    if lead < 0:
        raise ValueError('renewal lead must be nonnegative')
    return {'days_remaining':days,'renew_now':days <= lead,'expired':expiry <= now}


def _check_finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("numeric input must be finite")
    if isinstance(value, dict):
        for child in value.values():
            _check_finite(child)
    elif isinstance(value, list):
        for child in value:
            _check_finite(child)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", default="-", help="JSON input file, or - for stdin")
    args = parser.parse_args(argv)
    try:
        if args.input == "-":
            data = json.load(sys.stdin)
        else:
            with open(args.input, encoding="utf-8") as source:
                data = json.load(source)
        _check_finite(data)
        result = evaluate(data)
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError, OverflowError, configparser.Error) as error:
        print("Input error: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
