from os.path import join

from ocrd import Processor
from ocrd_utils import (
    getLogger,
    assert_file_grp_cardinality,
    make_file_id,
    concat_padded,
    points_from_x0y0x1y1,
    points_from_polygon,
    MIMETYPE_PAGE
)
from ocrd_models.ocrd_page import TextRegionType, TextLineType, CoordsType, BaselineType, to_xml
from ocrd_modelfactory import page_from_file

import shapely.geometry as geom
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
        use_legacy = self.parameter['use_legacy']
        if use_legacy:
            kwargs['scale'] = self.parameter['scale']
            kwargs['maxcolseps'] = self.parameter['maxcolseps']
            kwargs['black_colseps'] = self.parameter['black_colseps']
            log.info("Using legacy segmenter")
            segment = legacy_segment
        else:
            log.info("Using blla segmenter")
            blla_model_fname = self.resolve_resource(self.parameter['blla_model'])
            kwargs['model'] = TorchVGSLModel.load_model(blla_model_fname)
            kwargs['device'] = self.parameter['device']
            segment = blla_segment

        for (n, input_file) in enumerate(self.input_files):
            page_id = input_file.pageId or input_file.ID
            log.info("INPUT FILE %i / %s of %s", n, page_id, len(self.input_files))
            pcgts = page_from_file(self.workspace.download_file(input_file))
            self.add_metadata(pcgts)
            page = pcgts.get_Page()
            page_image, _, _ = self.workspace.image_from_page(page, page_id, feature_selector="binarized")
            log.info('Segmenting with %s segmenter' % ('legacy' if use_legacy else 'blla'))
            res = segment(page_image, **kwargs)
            log.info("Finished segmentation, serializing")
            if use_legacy:
                raise NotImplementedError("legacy segmenter NIH")
            else:
                for idx_region, region_polygon_ in enumerate(res['regions']['text']):
                    region_elem = TextRegionType(
                            id=f'region_{idx_region}',
                            Coords=CoordsType(points=points_from_polygon(region_polygon_)))
                    region_polygon = geom.Polygon(region_polygon_)
                    line_idx = 0
                    for line_dict in res['lines']:
                        line_polygon = geom.Polygon(line_dict['boundary'])
                        if region_polygon.contains(line_polygon):
                            region_elem.add_TextLine(TextLineType(
                                id=f'region_{idx_region}_line_{line_idx}',
                                Baseline=BaselineType(points=points_from_polygon(line_dict['baseline'])),
                                Coords=CoordsType(points=points_from_polygon(line_dict['boundary']))))
                        # TODO handle unmatched or twice-matched lines
                        line_idx += 1
                    page.add_TextRegion(region_elem)
            file_id = make_file_id(input_file, self.output_file_grp)
            pcgts.set_pcGtsId(file_id)
            self.workspace.add_file(
                ID=file_id,
                file_grp=self.output_file_grp,
                pageId=input_file.pageId,
                mimetype=MIMETYPE_PAGE,
                local_filename=join(self.output_file_grp, f'{file_id}.xml'),
                content=to_xml(pcgts))
