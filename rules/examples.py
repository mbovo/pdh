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
from pdh import rules, Filters


# This annotation make the main() method parse stdin as json into the parameter called input
# All returned values are converted to json and printed to stdout
@rules.rule
def main(input):

    # Initialize PagerDuty's APIs
    api = rules.api()

    # From the given input extract only incidents with the word cassandra in title
    incs = Filters.apply(input, filters=[Filters.regexp("title", ".*EC2.*")])

    # ackwnoledge all previously filtered incidents
    api.ack(incs)

    # # resolve all previously filtered incidents
    # api.resolve(incs)

    # # snooze all previously filtered incidents for 1h
    # api.snooze(incs, duration=3600)

    # # Chain a given rule, i.e call that rule with the output of this one
    # # chain-loading supports only a single binary, not directories
    # c = rules.chain(incs, "rules/test_chaining.sh")

    # # Execute an external program and get the output/err/return code
    # p: rules.ShellResponse = rules.exec('kubectl get nodes -o name')
    # if p.rc > 0:
    #     nodes = p.stdout.split("\n")

    # if you return a list of dicts, it will be rendered with each item as a row in a table
    # Othrwise will be converted as string
    return incs


if __name__ == "__main__":
    main()
