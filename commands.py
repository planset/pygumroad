#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import pygumroad


LIST_FORMAT = "{id:10}{name:20}  {prefix_currency} {price} {suffix_currency}"
DETAIL_FORMAT = "{key:10}: {value}"

class Commander(object):
    client = None
    token = None
    user = None
    password = None
    
    def __init__(self, args):
        self.token = args.token
        self.user = args.user
        self.password = args.password

    def _input_account(self):
        if not self.user:
            print "username(email): ",
            self.user = raw_input()
        if not self.password:
            self.password = getpass.getpass("password: ")

    def with_auth(f):
        def wrap(self, *args, **kwargs):
            if not self.token:
                self._input_account()
            if not self.client:
                self.client = pygumroad.GumroadClient(self.token)
            if not self.client.token:
                self.client.authenticate(self.user, self.password)
            return f(self, *args, **kwargs)
        return wrap
    
    def _print_link(self, link):
        print DETAIL_FORMAT.format(key="ID", value=link.id)
        print DETAIL_FORMAT.format(key="NAME", value=link.name)
        print DETAIL_FORMAT.format(key="URL", value=link.url)
        print DETAIL_FORMAT.format(key="currency", value=link.currency)
        print DETAIL_FORMAT.format(key="price", value=link.price)
        print DETAIL_FORMAT.format(key="description", value=link.description)

    def show_token(self):
        if self.client.token:
            print "token = " + self.client.token
        else:
            print "no login"

    def auth(self):
        self._input_account()
        self.client = pygumroad.GumroadClient()
        self.client.authenticate(self.user, self.password)
        self.show_token()
        
    @with_auth
    def deauthenticate(self):
        self.client.deauthenticate()
        print "logged out"
        
    @with_auth
    def list(self):
        print LIST_FORMAT.format(id="ID", name="NAME", 
            prefix_currency="", price="PRICE", suffix_currency="")
        for link in self.client.get_links():
            print LIST_FORMAT.format(
                    id=link.id,
                    name=link.name,
                    prefix_currency=link.prefix_currency,
                    price=link.price,
                    suffix_currency=link.suffix_currency
                    )

    @with_auth
    def detail(self, id):
        link = self.client.get_link(id)
        self._print_link(link)

    @with_auth
    def edit(self, id, name, url, price, description):
        link = self.client.get_link(id)
        if name:
            link.name = name
        if url:
            link.url = url
        if price:
            link.price = price
        if description:
            link.description = description
        link = self.client.edit_link(link)
        print "edited successfully"
        self._print_link(link)
        
    @with_auth
    def delete(self, id):
        link = self.client.get_link(id)
        self.client.delete_link(link)
        print "deleted successfully"
        self.list()
    
    @with_auth
    def add(self, name, url, price, description):
        link = self.client.add_link(name, url, price, description)
        print "The link has been created successfully."
        self._print_link(link)
        
        
if __name__ == "__main__":
    import sys
    import argparse
    import getpass
    import pygumroad
    
    parser = argparse.ArgumentParser(description="manage gumroad links")
    parser.add_argument("-u", "--user", default=None)
    parser.add_argument("-p", "--password", default=None)
    parser.add_argument("-t", "--token", default=None)
    parser.add_argument("-n", "--nologout", action="store_true")
    
    subparsers = parser.add_subparsers(dest="subparser_name")
    sub_parser = subparsers.add_parser("auth")
    
    sub_parser = subparsers.add_parser("deauth")
    #sub_parser.add_argument("-t", "--token", required=True)
    
    sub_parser = subparsers.add_parser("list")
    
    sub_parser = subparsers.add_parser("detail")
    sub_parser.add_argument("--id", required=True)
    
    sub_parser = subparsers.add_parser("add")
    sub_parser.add_argument("--name", required=True)
    sub_parser.add_argument("--url", required=True)
    sub_parser.add_argument("--price", required=True, type=int)
    sub_parser.add_argument("--description", default=None)
    
    sub_parser = subparsers.add_parser("delete")
    sub_parser.add_argument("--id", required=True)
    
    sub_parser = subparsers.add_parser("edit")
    sub_parser.add_argument("--id", required=True)
    sub_parser.add_argument("--name", default=None)
    sub_parser.add_argument("--url", default=None)
    sub_parser.add_argument("--price", default=None, type=int)
    sub_parser.add_argument("--description", default=None)
    
    args = parser.parse_args()
    
    c = Commander(args)
    if args.subparser_name == "auth":
        c.auth()
    elif args.subparser_name == "list":
        c.list()
    elif args.subparser_name == "detail":
        c.detail(args.id)
    elif args.subparser_name == "add":
        description = args.description or ""
        c.add(args.name.strip(), args.url.strip(), 
              args.price, description.strip()) 
    elif args.subparser_name == "edit":
        c.edit(args.id, args.name, args.url, args.price, args.description)
    elif args.subparser_name == "delete":
        c.delete(args.id)
    else:
        raise Exception(":-o")

    if args.subparser_name != "auth":
        if args.nologout or args.token:
            #c.show_token()
            print "continue logged in"
        else:
            c.deauthenticate()
        
    sys.exit()
    
