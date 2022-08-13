#!/usr/bin/env python3

import json
import sys
import time
from colorama import Fore, Back, Style
from pynvim import attach


help_message = """\
Usage: """ + sys.argv[0] + """ [-h|--help] | <transitions.tsv> <test_suite.json> [--verbose]

<transitions.tsv>  File containing keys that transition between modes in TSV format
<test_suite.json>  Output file of MTR framework in JSON format
--verbose          If set, all assertions will be printed to standard output
-h, --help         Prints this help message

Precondition: nvim must listen on port 10000 of localhost, i.e. it was started like:
$ nvim -u NONE --listen 127.0.0.1:10000
"""

transitions = {}
test_suite  = {}
input_list  = []


# Check arguments, print usage info if something is missing
def check_args():
    if 1 < len(sys.argv) and sys.argv[1] in ["-h", "--help"]:
        print(help_message)
        exit(0)
    if len(sys.argv) < 3:
        print(help_message)
        exit(1)


# Load transitions info to dictionary: (from, by-keys) -> to
def load_transitions(file_path):
    global transitions
    file = open(file_path, "r")
    lines = file.readlines()
    for line in lines:
        line = line.strip()
        if line == "" or line.startswith("#"):
            continue
        fields = line.split("\t")
        transitions[(fields[0], fields[1])] = fields[2]
    file.close()
    print("Successfully loaded transition list from", file_path)


# Load input sequence from test suite
def load_test_suite(file_path):
    global test_suite
    global input_list
    file = open(file_path, "r")
    json_data = json.load(file)
    test_suite = json_data["test_suite"]
    input_list = test_suite["input_list"]
    test_suite["file"] = file_path
    file.close()
    print("Successfully loaded test suite from", file_path)


def dump_test_suite_info():
    print("\n================== Test suite info ==================")
    print("File:"  , test_suite["file"])
    print("Name:"  , test_suite["name"])
    print("Id:"    , test_suite["id"])
    print("Method:", test_suite["method"])
    print("Input sequence length:", len(input_list))
    print("=====================================================")


# Needed, because "mode()" returns the termcode key representation
def termcode_to_state_name(termcode):
    if termcode == "\x16":
        return "CTRL-V"
    return termcode


def get_mode(nvim):
    mode = termcode_to_state_name(nvim.call("mode", True))
    # We must treat the "search cmdline" as separate mode
    if mode == "c" and nvim.call("getcmdtype") in ["/", "?"]:
        return mode + "s"
    return mode


# Set verbosity
verbose = 3 < len(sys.argv) and sys.argv[3] == "--verbose"

def run_test():
    # Attach to running nvim instance
    nvim = attach("tcp", address="127.0.0.1", port=10000)

    # Run whole test sequence
    print("Running test sequence...")
    total_count = 0
    ok_count    = 0
    nok_count   = 0
    time_begin  = time.time()
    for keys in input_list:
        # Query current mode
        start_mode = get_mode(nvim)

        # Transition by injecting input in form of feeded key sequence
        nvim.feedkeys(nvim.replace_termcodes(keys))

        # Query mode we transitioned to and what's expected
        outcome_mode  = get_mode(nvim)
        expected_mode = transitions[(start_mode, keys)]

        if verbose:
            print("start mode     ", start_mode)
            print("key sequence   ", keys)
            print("outcome mode   ", outcome_mode)
            print("expected mode  ", expected_mode)

        # Check if nvim arrived to the expected mode
        if expected_mode == outcome_mode:
            if verbose:
                print("result:         " + Back.GREEN + Fore.BLACK + "OK" + Style.RESET_ALL)
            ok_count += 1
        else:
            if verbose:
                print("result:         " + Back.RED + Fore.WHITE + "NOT OK!" + Style.RESET_ALL)
            nok_count += 1

        total_count += 1
        if verbose:
            print("-------------------")

    time_end = time.time()

    # Print test summary
    print("\n==================== Test results ===================")
    print("Total assertion count  ", total_count)
    print("Successful assertions  ", ok_count)
    print("Failed assertion       ", nok_count)
    print("Success rate            " + Style.BRIGHT + format(ok_count / total_count * 100, ".2f"), "%" + Style.RESET_ALL)
    print("Execution time         ", format(time_end - time_begin, ".4f"), "s")
    print("=====================================================")


# Main
check_args()
load_transitions(sys.argv[1])
load_test_suite(sys.argv[2])
dump_test_suite_info()
run_test()

