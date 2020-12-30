from __future__ import absolute_import
import io
import kraken.binarization
from ocrd import Processor
from ocrd_utils import getLogger, polygon_from_points, concat_padded
from ocrd_modelfactory import page_from_file

from ocrd_kraken.config import OCRD_TOOL

class KrakenRecognize(Processor):

    def __init__(self, *args, **kwargs):
        kwargs['ocrd_tool'] = OCRD_TOOL['tools']['ocrd-kraken-recognize']
        kwargs['version'] = OCRD_TOOL['version']
        super(KrakenRecognize, self).__init__(*args, **kwargs)

    def process(self):
        """
        Recognize with kraken
        """
        log = getLogger('processor.KrakenRecognize')
        for (n, input_file) in enumerate(self.input_files):
            page_id = input_file.pageId or input_file.ID
            log.info("INPUT FILE %i / %s of %s", n, page_id, len(self.input_files))
            pcgts = page_from_file(self.workspace.download_file(input_file))
            self.add_metadata(pcgts)
            page = pcgts.get_Page()
            page_image, _, _ = self.workspace.image_from_page(page, page_id, feature_selector="binarized")
            log.info("Converting PAGE to kraken 'bounds' format")
            bounds = {'boxes': []}
            for line in page.get_AllTextLine():
                bounds['boxes'].append(bbox_from_points(line.get_Coords().get('points')))
            print(bounds)
            log.info('Segmenting with %s segmenter' % ('legacy' if use_legacy else 'blla'))
            res = segment(page_image, **kwargs)
            log.info("Finished segmentation, serializing")
