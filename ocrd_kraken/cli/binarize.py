import click

from ocrd.decorators import ocrd_cli_options, ocrd_cli_wrap_processor
from ocrd_kraken.binarize import KrakenBinarize

@click.command()
@ocrd_cli_options
def cli(*args, **kwargs):
    return ocrd_cli_wrap_processor(KrakenBinarize, *args, **kwargs)
