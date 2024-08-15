from __future__ import absolute_import
from os.path import join
from typing import Optional

from ocrd.processor.base import OcrdPageResult
from ocrd.processor.ocrd_page_result import OcrdPageResultImage

import kraken.binarization
from ocrd import Processor
from ocrd_utils import assert_file_grp_cardinality, getLogger, make_file_id, MIMETYPE_PAGE
from ocrd_models.ocrd_page import AlternativeImageType, OcrdPage, to_xml
from ocrd_modelfactory import page_from_file

from ocrd_kraken.config import OCRD_TOOL


class KrakenBinarize(Processor):

    @property
    def executable(self):
        return 'ocrd-kraken-binarize'

    def setup(self):
        self.logger = getLogger('processor.KrakenBinarize')

    def process_page_pcgts(self, *input_pcgts: Optional[OcrdPage], page_id: Optional[str] = None) -> OcrdPageResult:
        """Binarize the pages/regions/lines with Kraken.

        Iterate over the input PAGE element hierarchy down to the requested
        ``level-of-operation``.

        Next, for each file, crop each segment image according to the layout
        annotation (via coordinates into the higher-level image, or from the
        alternative image), and determine the threshold for binarization 
        (via Ocropy nlbin). Apply results to the image and export it.

        Add the new image file to the workspace along with the output fileGrp,
        and using a file ID with suffix ``.IMG-BIN`` along with further
        identification of the input element.

        Reference each new image in the AlternativeImage of the element.

        Produce a new output file by serialising the resulting hierarchy.
        """
        assert self.workspace
        assert self.output_file_grp
        self.logger.debug('Level of operation: "%s"', self.parameter['level-of-operation'])

        pcgts = input_pcgts[0]
        assert pcgts
        page = pcgts.get_Page()
        assert page
        page_image, page_xywh, _ = self.workspace.image_from_page(
            page, page_id, feature_filter='binarized')
        result = OcrdPageResult(pcgts)
        if self.parameter['level-of-operation'] == 'page':
            self.logger.info("Binarizing page '%s'", page_id)
            alternative_image = AlternativeImageType(comments=f'{page_xywh["features"]},binarized')
            page.add_AlternativeImage(alternative_image)
            result.images.append(OcrdPageResultImage(kraken.binarization.nlbin(page_image), '.IMG-BIN', alternative_image))
        else:
            for region in page.get_AllRegions(classes=['Text']):
                region_image, region_xywh = self.workspace.image_from_segment(
                    region, page_image, page_xywh, feature_filter='binarized')
                if self.parameter['level-of-operation'] == 'region':
                    self.logger.info("Binarizing region '%s'", region.id)
                    alternative_image = AlternativeImageType(comments=f'{region_xywh["features"]},binarized')
                    region.add_AlternativeImage(alternative_image)
                    result.images.append(OcrdPageResultImage(kraken.binarization.nlbin(region_image), f'{region.id}.IMG-BIN', alternative_image))
                else:
                    for line in region.get_TextLine():
                        line_image, line_xywh = self.workspace.image_from_segment(
                            line, region_image, region_xywh, feature_filter='binarized')
                        self.logger.info("Binarizing line '%s'", line.id)
                        alternative_image = AlternativeImageType(comments=f'{line_xywh["features"]},binarized')
                        line.add_AlternativeImage(alternative_image)
                        result.images.append(OcrdPageResultImage(kraken.binarization.nlbin(line_image), f'{region.id}_{line.id}.IMG-BIN', alternative_image))
        return result
