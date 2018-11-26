from __future__ import absolute_import
import io
import kraken.binarization
from ocrd import Processor
from ocrd.utils import getLogger, polygon_from_points, concat_padded
import ocrd.model.ocrd_page as ocrd_page

from ocrd_kraken.config import OCRD_TOOL

log = getLogger('processor.KrakenBinarize')

class KrakenBinarize(Processor):

    def __init__(self, *args, **kwargs):
        kwargs['ocrd_tool'] = OCRD_TOOL['tools']['ocrd-kraken-binarize']
        kwargs['version'] = OCRD_TOOL['version']
        super(KrakenBinarize, self).__init__(*args, **kwargs)

    def process(self):
        """
        Performs the binarization.
        """
        log.debug('Level of operation: "%s"', self.parameter['level-of-operation'])
        log.debug('Input file group %s', self.input_file_grp)
        log.debug('Input files %s', self.input_files)
        for (n, input_file) in enumerate(self.input_files):
            log.info("INPUT FILE %i / %s", n, input_file)
            pcgts = ocrd_page.from_file(self.workspace.download_file(input_file))
            image_url = pcgts.get_Page().imageFilename
            log.info("pcgts %s", pcgts)
            if self.parameter['level-of-operation'] == 'page':
                log.info("About to binarize page '%s'", pcgts.pcGtsId)
                image = self.workspace.resolve_image_as_pil(image_url)
                bin_image = kraken.binarization.nlbin(image)
                bin_image_bytes = io.BytesIO()
                bin_image.save(bin_image_bytes, format='PNG')
                ID = concat_padded(self.output_file_grp, n)
                self.workspace.add_file(
                    self.output_file_grp,
                    ID=ID,
                    basename="%s.bin.png" % ID,
                    mimetype='image/png',
                    content=bin_image_bytes.getvalue())
            else:
                for region in pcgts.get_Page().get_TextRegion():
                    if self.parameter['level-of-operation'] == 'block':
                        log.info("About to binarize region '%s'", region.id)
                        image = self.workspace.resolve_image_as_pil(image_url, polygon_from_points(region.get_Coords().points))
                    else:
                        textlines = region.get_TextLine()
                        log.info("About to binarize %i lines of region '%s'", len(textlines), region.id)
                        for (line_no, line) in enumerate(textlines):
                            log.debug("Binarizing line '%s' in region '%s'", line_no, region.id)
                            image = self.workspace.resolve_image_as_pil(image_url, polygon_from_points(line.get_Coords().points))
                            bin_image = kraken.binarization.nlbin(image)
                            bin_image_bytes = io.BytesIO()
                            bin_image.save(bin_image_bytes, format='PNG')
                            ID = concat_padded(self.output_file_grp, n, region.id, line_no)
                            self.workspace.add_file(
                                self.output_file_grp,
                                ID=ID,
                                basename="%s.bin.png" % ID,
                                mimetype='image/png',
                                content=bin_image_bytes.getvalue())
