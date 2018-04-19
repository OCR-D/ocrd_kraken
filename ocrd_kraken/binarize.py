from __future__ import absolute_import
import kraken # pylint: disable=import-error
from ocrd.utils import getLogger
from ocrd import Processor, OcrdPage # pylint: disable=no-name-in-module

log = getLogger('processor.KrakenBinarize')

class KrakenBinarize(Processor):

    def process(self):
        """
        Performs the binarization.
        """
        log.debug('Level of operation: "%s"', self.parameter['level-of-operation'])
        for (n, input_file) in enumerate(self.input_files):
            log.info("XXX INPUT FILE %i / %s", n, input_file)
            self.workspace.download_file(input_file)
            page = OcrdPage.from_file(input_file)
            image_url = page.imageFileName
            log.info("page %s", page)
            for region in page.list_textregions():
                textlines = region.list_textlines()
                log.info("About to binarize %i lines of region '%s'", len(textlines), region.ID)
                for (line_no, line) in enumerate(textlines):
                    log.debug("Binarizing line '%s' in region '%s'", line_no, region.ID)
                    image = self.workspace.resolve_image_as_pil(image_url, line.coords)
                    bin_image = kraken.binarization.nlbin(image)
            '''
            self.add_output_file(
                ID=mets_file_id(self.output_filegrp, n),
                input_file=input_file,
                mimetype=MIMETYPE_PAGE,
                content=page.to_xml()
            )
            '''
