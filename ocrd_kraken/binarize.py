from __future__ import absolute_import
import io
import kraken.binarization
from ocrd import Processor, MIMETYPE_PAGE # pylint: disable=no-name-in-module
from ocrd.utils import getLogger, polygon_from_points, mets_file_id
import ocrd.model.ocrd_page as ocrd_page

log = getLogger('processor.KrakenBinarize')

class KrakenBinarize(Processor):

    def process(self):
        """
        Performs the binarization.
        """
        log.debug('Level of operation: "%s"', self.parameter['level-of-operation'])
        for (n, input_file) in enumerate(self.input_files):
            log.info("INPUT FILE %i / %s", n, input_file)
            pcgts = ocrd_page.from_file(self.workspace.download_file(input_file))
            image_url = pcgts.get_Page().imageFilename
            log.info("pcgts %s", pcgts)
            for region in pcgts.get_Page().get_TextRegion():
                textlines = region.get_TextLine()
                log.info("About to binarize %i lines of region '%s'", len(textlines), region.id)
                for (line_no, line) in enumerate(textlines):
                    log.debug("Binarizing line '%s' in region '%s'", line_no, region.id)
                    image = self.workspace.resolve_image_as_pil(image_url, polygon_from_points(line.get_Coords().points))
                    print(dir(kraken.binarization))
                    bin_image = kraken.binarization.nlbin(image)
                    bin_image_bytes = io.BytesIO()
                    bin_image.save(bin_image_bytes, format='PNG')
                    ID = mets_file_id(self.output_file_grp, n)
                    self.add_output_file(
                        ID=ID,
                        file_grp=self.output_file_grp,
                        basename="%s.bin.png" % ID,
                        mimetype='image/png',
                        content=bin_image_bytes.getvalue()
                    )
