from __future__ import absolute_import

from ocrd import Processor
from ocrd_utils import getLogger, concat_padded, points_from_x0y0x1y1, MIMETYPE_PAGE
from ocrd_models.ocrd_page import TextRegionType, TextLineType, CoordsType, to_xml
from ocrd_modelfactory import page_from_file

from ocrd_kraken.config import OCRD_TOOL

from kraken.pageseg import segment, detect_scripts

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
            pcgts = page_from_file(downloaded_file)
            # TODO binarized variant from get_AlternativeImage()
            image_url = pcgts.get_Page().imageFilename
            log.info("pcgts %s", pcgts)

            im = self.workspace.resolve_image_as_pil(image_url)

            log.info('Segmenting')
            log.info('Params %s', self.parameter)
            res = segment(
                im,
                self.parameter['text_direction'],
                self.parameter['scale'],
                self.parameter['maxcolseps'],
                self.parameter['black_colseps']
            )
            if self.parameter['script_detect']:
                res = detect_scripts(im, res)

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
            self.workspace.add_file(
                self.output_file_grp,
                pageId=input_file.pageId,
                ID=ID,
                mimetype=MIMETYPE_PAGE,
                local_filename="%s/%s.xml" % (self.output_file_grp, ID),
                content=to_xml(pcgts).encode('utf-8'))
