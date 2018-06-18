from __future__ import absolute_import
import kraken.pageseg as pageseg
from ocrd import Processor, MIMETYPE_PAGE
from ocrd.utils import getLogger, concat_padded, points_from_x0y0x1y1
import ocrd.model.ocrd_page as ocrd_page
from ocrd.model.ocrd_page import TextRegionType, TextLineType, CoordsType, to_xml

from ocrd_kraken.config import OCRD_TOOL

log = getLogger('processor.KrakenSegment')

class KrakenSegment(Processor):

    def __init__(self, *args, **kwargs):
        kwargs['ocrd_tool'] = OCRD_TOOL['tools']['ocrd-kraken-segment']
        super(KrakenSegment, self).__init__(*args, **kwargs)

    def process(self):
        """
        Segment with kraken
        """
        for (n, input_file) in enumerate(self.input_files):
            log.info("INPUT FILE %i / %s", n, input_file)
            downloaded_file = self.workspace.download_file(input_file)
            log.info("downloaded_file %s", downloaded_file)
            pcgts = ocrd_page.from_file(downloaded_file)
            # TODO binarized variant from get_AlternativeImage()
            image_url = pcgts.get_Page().imageFilename
            log.info("pcgts %s", pcgts)

            im = self.workspace.resolve_image_as_pil(image_url)

            log.info('Segmenting')
            log.info('Params %s' % self.parameter)
            res = pageseg.segment(
                im,
                self.parameter['text_direction'],
                self.parameter['scale'],
                self.parameter['maxcolseps'],
                self.parameter['black_colseps']
            )
            if self.parameter['script_detect']:
                res = pageseg.detect_scripts(im, res)

            dummyRegion = TextRegionType()
            pcgts.get_Page().add_TextRegion(dummyRegion)
            #  print(res)
            for lineno, box in enumerate(res['boxes']):
                textline = TextLineType(
                    id=concat_padded("line", lineno),
                    Coords=CoordsType(points=points_from_x0y0x1y1(box))
                )
                dummyRegion.add_TextLine(textline)
            ID = concat_padded(self.output_file_grp, n)
            self.add_output_file(
                ID=ID,
                file_grp=self.output_file_grp,
                basename="%s.xml" % ID,
                mimetype=MIMETYPE_PAGE,
                content=to_xml(pcgts).encode('utf-8')
            )
