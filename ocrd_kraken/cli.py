import click

from ocrd.decorators import ocrd_cli_options, ocrd_cli_wrap_processor
from ocrd_kraken.binarize import KrakenBinarize
from ocrd_kraken.segment import KrakenSegment

@click.command()
@ocrd_cli_options
def ocrd_kraken_binarize(*args, **kwargs):
    return ocrd_cli_wrap_processor(KrakenBinarize, *args, **kwargs)

@click.command()
@ocrd_cli_options
def ocrd_kraken_segment(*args, **kwargs):
    return ocrd_cli_wrap_processor(KrakenSegment, *args, **kwargs)
