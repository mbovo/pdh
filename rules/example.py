#!/usr/bin/env python3
#
# This file is part of the pdh (https://github.com/mbovo/pdh).
# Copyright (c) 2020-2025 Manuel Bovo.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Needed imports
from pdh.rules import rule

# This annotation make the main() method parsing stdin as a json and returning a json to stdout
# Available arguments are
# - alerts: the input data from pdh command line (a list of incidents in json format)
# - pagerduty: an instance of the PagerDuty class, exposes the PagerDuty APIs
# - Filters: useful filter functions
# - Transformations: useful transformation functions
@rule
def main(alerts, pagerduty, Filters, Transformations):

    # From the given input extract only incidents with the word "EC2" in title
    filtered = Filters.apply(
        alerts, filters=[Filters.regexp("service.summary", ".*Graph.*")])

    # # acknowledge all previously filtered incidents
    #pagerduty.incidents.ack(filtered)

    # # resolve all previously filtered incidents
    # pagerduty.incidents.resolve(filtered)

    # # snooze all previously filtered incidents for 1h
    # pagerduty.incidents.snooze(filtered, duration=3600)

    # # Execute an external program and get the output/err/return code
    # p: rules.ShellResponse = rules.exec('kubectl get nodes -o name')
    # if p.rc > 0:
    #     nodes = p.stdout.split("\n")

    return filtered


if __name__ == "__main__":
    main()
