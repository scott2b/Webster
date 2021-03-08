from enum import Enum
from typing import List, Optional
import asyncio
import json
import os
import typer
from .api import WebsterClient, VERSION


app_id = os.environ['WEBSTER_APP_ID']
app_secret = os.environ['WEBSTER_APP_SECRET']

app = typer.Typer()

_client = None
def client():
    global _client
    if _client is None:
        print('instantiating new client')
        _client = WebsterClient(app_id, app_secret)
    return _client


def complete_content_type(incomplete: str):
    for name in ContentTypes:
        if name.startswith(incomplete):
            yield (name, help_text)


def output(data, *, filename=None, indent=4):
    if filename is None:
        s = json.dumps(data, indent=indent, ensure_ascii=False).encode('utf-8')
        print(s.decode())
    if filename is not None:
        with open(filename, 'w', encoding='utf8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
     

@app.command()
def version():
    """Get the API verson."""
    typer.echo(VERSION)


@app.command()
def openapi():
    """Get the openapi specification."""
    r = client().openapi()
    output(r.json())


@app.command()
def profile():
    r = client().profile()
    output(r.json())


if __name__=='__main__':
    app()
