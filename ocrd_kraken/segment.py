from __future__ import absolute_import

from ocrd import Processor
from ocrd_utils import (
    getLogger,
    assert_file_grp_cardinality,
    concat_padded,
    points_from_x0y0x1y1,
    MIMETYPE_PAGE
)
from ocrd_models.ocrd_page import TextRegionType, TextLineType, CoordsType, to_xml
from ocrd_modelfactory import page_from_file

from kraken.lib.vgsl import TorchVGSLModel
from kraken.pageseg import segment as legacy_segment
from kraken.blla import segment as blla_segment

from .config import OCRD_TOOL

class KrakenSegment(Processor):

    def __init__(self, *args, **kwargs):
        kwargs['ocrd_tool'] = OCRD_TOOL['tools']['ocrd-kraken-segment']
        kwargs['version'] = OCRD_TOOL['version']
        super(KrakenSegment, self).__init__(*args, **kwargs)

    def process(self):
        """
        Segment with kraken
        """
        log = getLogger('processor.KrakenSegment')
        assert_file_grp_cardinality(self.input_file_grp, 1)
        assert_file_grp_cardinality(self.output_file_grp, 1)
        kwargs = {}
        kwargs['text_direction'] = self.parameter['text_direction']
        use_legacy = self.parameter['use_legacy']:
        if use_legacy:
            kwargs['scale'] = self.parameter['scale']
            kwargs['maxcolseps'] = self.parameter['maxcolseps']
            kwargs['black_colseps'] = self.parameter['black_colseps']
            log.info("Using legacy segmenter")
            segment = legacy_segment
        else:
            log.info("Using blla segmenter")
            blla_model_fname = self.resolve_resource(parameter['blla_model'])
            kwargs['model'] = TorchVGSLModel(blla_model_fname)
            kwargs['device'] = self.parameter['device']
            segment = blla_segment

        for (n, input_file) in enumerate(self.input_files):
            page_id = input_file.pageId or input_file.ID
            self.logger.info("INPUT FILE %i / %s", n, page_id)
            pcgts = page_from_file(self.workspace.download_file(input_file))
            self.add_metadata(pcgts)
            page = pcgts.get_Page()
            page_image, page_coords, page_image_info = self.workspace.image_from_page(page, page_id, feature_selector="binarized")
            log.info('Segmenting')
            log.info('Params %s', self.parameter)
            res = segment(
                page_image,
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
