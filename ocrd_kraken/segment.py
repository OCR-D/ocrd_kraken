from os.path import join

from ocrd import Processor
from ocrd_utils import (
    getLogger,
    assert_file_grp_cardinality,
    make_file_id,
    concat_padded,
    polygon_from_x0y0x1y1,
    points_from_polygon,
    coordinates_for_segment,
    MIMETYPE_PAGE
)
import ocrd_models.ocrd_page
from ocrd_models.ocrd_page import TextRegionType, TextLineType, CoordsType, BaselineType, to_xml
from ocrd_modelfactory import page_from_file

import shapely.geometry as geom
from shapely.prepared import prep as geom_prep

from .config import OCRD_TOOL

class KrakenSegment(Processor):

    def __init__(self, *args, **kwargs):
        kwargs['ocrd_tool'] = OCRD_TOOL['tools']['ocrd-kraken-segment']
        kwargs['version'] = OCRD_TOOL['version']
        super().__init__(*args, **kwargs)
        if hasattr(self, 'output_file_grp'):
            # processing context
            self.setup()

    def setup(self):
        """
        Load models
        """
        log = getLogger('processor.KrakenSegment')
        kwargs = {}
        kwargs['text_direction'] = self.parameter['text_direction']
        self.use_legacy = self.parameter['use_legacy']
        if self.use_legacy:
            from kraken.pageseg import segment
            kwargs['scale'] = self.parameter['scale']
            kwargs['maxcolseps'] = self.parameter['maxcolseps']
            kwargs['black_colseps'] = self.parameter['black_colseps']
            log.info("Using legacy segmenter")
        else:
            from kraken.lib.vgsl import TorchVGSLModel
            from kraken.blla import segment
            log.info("Using blla segmenter")
            blla_model_fname = self.resolve_resource(self.parameter['blla_model'])
            kwargs['model'] = TorchVGSLModel.load_model(blla_model_fname)
            kwargs['device'] = self.parameter['device']
        def segmenter(img):
            return segment(img, **kwargs)
        self.segmenter = segmenter

    def process(self):
        """
        Segment with kraken
        """
        log = getLogger('processor.KrakenSegment')
        assert_file_grp_cardinality(self.input_file_grp, 1)
        assert_file_grp_cardinality(self.output_file_grp, 1)

        for n, input_file in enumerate(self.input_files):
            page_id = input_file.pageId or input_file.ID
            log.info("INPUT FILE %i / %s of %s", n, page_id, len(self.input_files))
            pcgts = page_from_file(self.workspace.download_file(input_file))
            self.add_metadata(pcgts)
            page = pcgts.get_Page()
            page_image, page_coords, page_info = self.workspace.image_from_page(
                page, page_id,
                feature_selector="binarized" if self.use_legacy else "")
            if page_info.resolution != 1:
                dpi = page_info.resolution
                if page_info.resolutionUnit == 'cm':
                    dpi = round(dpi * 2.54)
                zoom = 300.0 / dpi
            else:
                zoom = 1.0
            # TODO: be DPI-relative
            log.info('Segmenting with %s segmenter' % ('legacy' if self.use_legacy else 'blla'))
            # TODO: be incremental by aggregating existing regions and passing `mask`
            res = self.segmenter(page_image)
            log.info("Finished segmentation, serializing")
            if self.use_legacy:
                log.debug(res)
                for idx_line, line_x0y0x1y1 in enumerate(res['boxes']):
                    line_poly = polygon_from_x0y0x1y1(line_x0y0x1y1)
                    line_poly = coordinates_for_segment(line_poly, None, page_coords)
                    line_points = points_from_polygon(line_poly)
                    region_elem = TextRegionType(
                        id='region_line_%s' % (idx_line + 1),
                        Coords=CoordsType(points=line_points))
                    region_elem.add_TextLine(TextLineType(
                        id='region_line_%s_line' % (idx_line + 1),
                        Coords=CoordsType(points=line_points)))
                    page.add_TextRegion(region_elem)
            else:
                handled_lines = {}
                regions = [(type_, poly)
                           for type_, polys in res['regions'].items()
                           for poly in polys]
                for idx_region, (region_type, region_poly) in enumerate(regions):
                    region_poly = coordinates_for_segment(region_poly, None, page_coords)
                    region_type = self.parameter['blla_classes'][region_type]
                    region_class = getattr(ocrd_models.ocrd_page, region_type + 'Type')
                    region_elem = region_class(
                            id='region_%s' % (idx_region + 1),
                            Coords=CoordsType(points=points_from_polygon(region_poly)))
                    getattr(page, 'add_' + region_type)(region_elem)
                    if not region_type == 'TextRegion':
                        continue
                    region_polygon = make_valid(geom.Polygon(region_poly))
                    # enlarge to avoid loosing slightly extruding text lines
                    region_polygon = geom_prep(region_polygon.buffer(20/zoom))
                    for idx_line, line_dict in enumerate(res['lines']):
                        line_poly = coordinates_for_segment(line_dict['boundary'], None, page_coords)
                        line_baseline = coordinates_for_segment(line_dict['baseline'], None, page_coords)
                        line_polygon = make_valid(geom.Polygon(line_poly))
                        if region_polygon.contains(line_polygon):
                            if idx_line in handled_lines:
                                log.error("Line %s was already added to region %s" % (idx_line, handled_lines[idx_line]))
                                continue
                            region_elem.add_TextLine(TextLineType(
                                id='region_%s_line_%s' % (idx_region + 1, idx_line + 1),
                                Baseline=BaselineType(points=points_from_polygon(line_baseline)),
                                Coords=CoordsType(points=points_from_polygon(line_poly))))
                            handled_lines[idx_line] = idx_region
                for idx_line, line_dict in enumerate(res['lines']):
                    if idx_line not in handled_lines:
                        log.error("Line %s could not be assigned a region, creating a dummy region", idx_line)
                        line_poly = coordinates_for_segment(line_dict['boundary'], None, page_coords)
                        line_baseline = coordinates_for_segment(line_dict['baseline'], None, page_coords)
                        region_elem = TextRegionType(
                            id='region_line_%s' % (idx_line + 1),
                            Coords=CoordsType(points=points_from_polygon(line_poly)))
                        region_elem.add_TextLine(TextLineType(
                            id='region_line_%s_line' % (idx_line + 1),
                            Baseline=BaselineType(points=points_from_polygon(line_baseline)),
                            Coords=CoordsType(points=points_from_polygon(line_poly))))
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

def make_valid(polygon):
    for split in range(1, len(polygon.exterior.coords)-1):
        if polygon.is_valid or polygon.simplify(polygon.area).is_valid:
            break
        # simplification may not be possible (at all) due to ordering
        # in that case, try another starting point
        polygon = geom.Polygon(polygon.exterior.coords[-split:]+polygon.exterior.coords[:-split])
    for tolerance in range(1, int(polygon.area)):
        if polygon.is_valid:
            break
        # simplification may require a larger tolerance
        polygon = polygon.simplify(tolerance)
    return polygon
