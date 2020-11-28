#!/usr/bin/env python3

import argparse
import random
import requests
import string
import sys

TRAKT_DOMAIN = "https://api.trakt.tv"
TRAKT_AUTHORIZE_ENDPOINT = "/oauth/authorize"
TRAKT_TOKEN_ENDPOINT = "/oauth/token"

def _csrf_token():
    return "".join(random.SystemRandom().choice(
        string.ascii_uppercase + string.digits) for _ in range(6)
    )

def _check_response(response, message):
    if not response.ok:
        print("""
{message}

  url: {url}

  status_code: {status_code}

  headers: {headers}

  content: {content}
""".format(
            message=message,
            url=response.url,
            status_code=response.status_code,
            headers=response.headers,
            content=response.text), file=sys.stderr)
        sys.exit(1)
    return response

def _trakt_uri(endpoint):
    return "{domain}{endpoint}".format(domain=TRAKT_DOMAIN, endpoint=endpoint)

def _authorize(client_id, redirect_uri, state):
    return requests.Request(
        "GET",
        _trakt_uri(TRAKT_AUTHORIZE_ENDPOINT),
        params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
        },
    )

def _token(code, client_id, client_secret, redirect_uri):
    return requests.post(
        _trakt_uri(TRAKT_TOKEN_ENDPOINT),
        headers={
            "Content-Type": "application/json",
        },
        params={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        },
    )

def _prompt_for_code(client_id, redirect_uri):
    csrf_token = _csrf_token()

    authorize = _authorize(client_id, redirect_uri, csrf_token)
    print("""
Navigate to the following url and allow access:")

  {url}

Note the code and state parameters in the redirect url.

If state does not match the following, this authorization is not trustworthy:

  {state}
""".format(url=authorize.prepare().url, state=csrf_token))

    code = input("Copy/paste the code from the redirect url: ").strip()
    while not code:
        print("Invalid code.")
        code = input("Copy/paste the code from the redirect url: ").strip()
    return code

def _parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--client_id")
    parser.add_argument("--client_secret")
    parser.add_argument("--redirect_uri")
    parser.add_argument("--code", required=False)
    return parser.parse_args(argv)

def main(argv=None):
    args = _parse_args(argv=argv)

    if not args.code:
        args.code = _prompt_for_code(args.client_id, args.redirect_uri)

    token = _check_response(
        _token(
            args.code,
            args.client_id,
            args.client_secret,
            args.redirect_uri,
        ),
        "Failed to trade code for token.",
    )

    print("""
Success!

Copy the tokens from the response into your application:

{response}
""".format(response=token.json()))

if __name__ == "__main__":
    main(sys.argv[1:])
