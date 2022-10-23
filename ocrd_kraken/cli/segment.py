import click
from ocrd.decorators import ocrd_cli_options, ocrd_cli_wrap_processor
from ocrd_kraken.segment import KrakenSegment

@click.command()
@ocrd_cli_options
def cli(*args, **kwargs):
    return ocrd_cli_wrap_processor(KrakenSegment, *args, **kwargs)
