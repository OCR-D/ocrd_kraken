import click

from ocrd.decorators import ocrd_cli_options, ocrd_cli_wrap_processor # pylint: disable=no-name-in-module,import-error
from ocrd_kraken.binarize import KrakenBinarize

@click.command()
@ocrd_cli_options
def ocrd_kraken_binarize(*args, **kwargs):
    return ocrd_cli_wrap_processor(KrakenBinarize, *args, **kwargs)
