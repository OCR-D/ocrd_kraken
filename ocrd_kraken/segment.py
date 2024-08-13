from typing import Optional
from PIL import ImageOps
from os.path import join

from ocrd import Processor
from ocrd_utils import (
    getLogger,
    assert_file_grp_cardinality,
    make_file_id,
    concat_padded,
    polygon_from_x0y0x1y1,
    points_from_polygon,
    polygon_mask,
    coordinates_for_segment,
    coordinates_of_segment,
    MIMETYPE_PAGE
)
import ocrd_models.ocrd_page
from ocrd_models.ocrd_page import (
    OcrdPage,
    PageType,
    BorderType,
    TextRegionType,
    TextLineType,
    CoordsType,
    BaselineType,
    to_xml
)
from ocrd_modelfactory import page_from_file

import shapely.geometry as geom
from shapely.prepared import prep as geom_prep
import torch

from .config import OCRD_TOOL

class KrakenSegment(Processor):

    @property
    def executable(self):
        return 'ocrd-kraken-segment'

    def setup(self):
        """
        Load models
        """
        self.logger = getLogger('processor.KrakenSegment')
        kwargs = {}
        kwargs['text_direction'] = self.parameter['text_direction']
        self.use_legacy = self.parameter['use_legacy']
        if self.use_legacy:
            from kraken.pageseg import segment
            kwargs['scale'] = self.parameter['scale']
            kwargs['maxcolseps'] = self.parameter['maxcolseps']
            kwargs['black_colseps'] = self.parameter['black_colseps']
            self.logger.info("Using legacy segmenter")
        else:
            from kraken.lib.vgsl import TorchVGSLModel
            from kraken.blla import segment
            self.logger.info("Using blla segmenter")
            blla_model_fname = self.resolve_resource(self.parameter['blla_model'])
            kwargs['model'] = TorchVGSLModel.load_model(blla_model_fname)
            device = self.parameter['device']
            if device != 'cpu' and not torch.cuda.is_available():
                device = 'cpu'
            if device == 'cpu':
                self.logger.warning("no CUDA device available. Running without GPU will be slow")
            kwargs['device'] = device
        def segmenter(img, mask=None):
            return segment(img, mask=mask, **kwargs)
        self.segmenter = segmenter

    def process_page_pcgts(self, *input_pcgts : OcrdPage, output_file_id : Optional[str] = None, page_id : Optional[str] = None) -> OcrdPage:
        """Segment into (regions and) lines with Kraken.

        Iterate over the element hierarchy of the PAGE-XML down to the
        ``level-of-operation``, i.e.:

        \b
        - On `page` level and `table` level, detect text regions and lines
          (trying to allocate lines to regions).
        - On `region` level, detect lines only.

        Get the page image from the alternative image or by cropping according to the
        layout annotation. If alternative images are present, prefer binarized form
        (if ``use_legacy``) or use the last available alternative image (otherwise).
        Unless at the top level (i.e. a page without border), calculate a mask image for
        the current segment.

        Next, if ``overwrite_segments``, then delete any existing text regions/lines.
        Otherwise hide the existing segments in the mask image.

        Then compute a segmentation and decode it into new (text regions and) lines, and
        append them to the parent segment.

        Return the resulting hierarchy.
        """

        pcgts = input_pcgts[0]
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

        if self.parameter['level-of-operation'] == 'page':
            self.logger.info('Segmenting page with %s segmenter', 'legacy' if self.use_legacy else 'blla')
            if self.parameter['overwrite_segments']:
                page.TextRegion = []
            elif len(page.TextRegion or []):
                self.logger.warning('Keeping %d text regions on page "%s"', len(page.TextRegion or []), page.id)
            self._process_page(page_image, page_coords, page, zoom)
        elif self.parameter['level-of-operation'] == 'table':
            regions = page.get_AllRegions(classes=['Table'])
            if not regions:
                self.logger.warning('No existing table regions on page "%s"', page_id)
            for region in regions:
                self.logger.info('Segmenting table region "%s" with %s segmenter', region.id, 'legacy' if self.use_legacy else 'blla')
                if self.parameter['overwrite_segments']:
                    region.TextRegion = []
                elif len(region.TextRegion or []):
                    self.logger.warning('Keeping %d text regions in region "%s"', len(region.TextRegion or []), region.id)
                self._process_page(page_image, page_coords, region, zoom)
        else:
            regions = page.get_AllRegions(classes=['Text'])
            if not regions:
                self.logger.warning('No existing text regions on page "%s"', page_id)
            for region in regions:
                self.logger.info('Segmenting text region "%s" with %s segmenter', region.id, 'legacy' if self.use_legacy else 'blla')
                if self.parameter['overwrite_segments']:
                    region.TextLine = []
                elif len(region.TextLine or []):
                    self.logger.warning('Keeping %d lines in region "%s"', len(region.TextLine or []), region.id)
                self._process_region(page_image, page_coords, region, zoom)

        return pcgts

    def _process_page(self, page_image, page_coords, page, zoom=1.0):
        def getmask():
            # use mask if existing regions (any type for page, text cells for table)
            # or segment is lower than page level
            regions = (page.get_TextRegion() +
                       page.get_ImageRegion() +
                       page.get_LineDrawingRegion() +
                       page.get_GraphicRegion() +
                       page.get_ChartRegion() +
                       page.get_MapRegion() +
                       page.get_MathsRegion() +
                       page.get_ChemRegion() +
                       page.get_MusicRegion() +
                       page.get_AdvertRegion() +
                       page.get_NoiseRegion() +
                       page.get_UnknownRegion() +
                       page.get_CustomRegion())
            if isinstance(page, PageType):
                if len(regions) == 0:
                    return None
                if page.Border is None:
                    border = BorderType(CoordsType(points="0,0 0,%d %d,%d %d,0" % (
                        page.get_imageHeight(), page.get_imageWidth(),
                        page.get_imageHeight(), page.get_imageWidth())))
                else:
                    border = page.Border
                poly = coordinates_of_segment(border, page_image, page_coords)
            else:
                # table region
                poly = coordinates_of_segment(page, page_image, page_coords)
            # poly = geom.Polygon(poly).buffer(20/zoom).exterior.coords[:-1]
            mask = ImageOps.invert(polygon_mask(page_image, poly))
            for region in regions:
                self.logger.info("Masking existing region %s", region.id)
                poly = coordinates_of_segment(region, page_image, page_coords)
                # poly = geom.Polygon(poly).buffer(20/zoom).exterior.coords[:-1]
                mask.paste(255, mask=polygon_mask(page_image, poly))
            return mask
        res = self.segmenter(page_image, mask=getmask())
        self.logger.debug("Finished segmentation, serializing")
        if self.use_legacy:
            self.logger.debug(res)
            idx_line = 0
            for idx_line, line in enumerate(res.lines):
                line_poly = polygon_from_x0y0x1y1(line.bbox)
                line_poly = coordinates_for_segment(line_poly, None, page_coords)
                line_points = points_from_polygon(line_poly)
                region_elem = TextRegionType(
                    id=f'region_line_{idx_line + 1}',
                    Coords=CoordsType(points=line_points))
                region_elem.add_TextLine(TextLineType(
                    id=f'region_line_{idx_line + 1}_line',
                    Coords=CoordsType(points=line_points)))
                page.add_TextRegion(region_elem)
            self.logger.debug("Found %d lines on page %s", idx_line + 1, page.id)
        else:
            self.logger.debug(res)
            handled_lines = {}
            regions = [(type_, region)
                       for type_ in res.regions
                       for region in res.regions[type_]]
            idx_region = idx_line = 0
            for idx_region, (type_, region) in enumerate(regions):
                region_poly = coordinates_for_segment(region.boundary, None, page_coords)
                region_poly = make_valid(geom.Polygon(region_poly))
                region_type = self.parameter['blla_classes'][type_]
                region_class = getattr(ocrd_models.ocrd_page, region_type + 'Type')
                region_elem = region_class(
                        id=f'region_{idx_region + 1}',
                        Coords=CoordsType(points=points_from_polygon(region_poly.exterior.coords[:-1])))
                getattr(page, 'add_' + region_type)(region_elem)
                if not region_type == 'TextRegion':
                    continue
                # enlarge to avoid loosing slightly extruding text lines
                region_poly = geom_prep(region_poly.buffer(20/zoom))
                for idx_line, line in enumerate(res.lines):
                    line_poly = coordinates_for_segment(line.boundary, None, page_coords)
                    line_baseline = coordinates_for_segment(line.baseline, None, page_coords)
                    line_id = f'region_{idx_region + 1}_line_{idx_line + 1}'
                    line_type = line.tags.get('type', '')
                    self.logger.info("Line %s is of type %s", line_id, line_type)
                    line_poly = make_valid(geom.Polygon(line_poly))
                    if region_poly.contains(line_poly):
                        if idx_line in handled_lines:
                            self.logger.error("Line %s was already added to region %s" % (idx_line, handled_lines[idx_line]))
                            continue
                        region_elem.add_TextLine(TextLineType(
                            id=line_id,
                            Baseline=BaselineType(points=points_from_polygon(line_baseline)),
                            Coords=CoordsType(points=points_from_polygon(line_poly.exterior.coords[:-1]))))
                        handled_lines[idx_line] = idx_region
            for idx_line, line in enumerate(res.lines):
                if idx_line not in handled_lines:
                    self.logger.error("Line %s could not be assigned a region, creating a dummy region", idx_line)
                    line_poly = coordinates_for_segment(line.boundary, None, page_coords)
                    line_baseline = coordinates_for_segment(line.baseline, None, page_coords)
                    line_id = f'region_line_{idx_line + 1}_line'
                    line_type = line.tags.get('type', '')
                    self.logger.info("Line %s is of type %s", line_id, line_type)
                    line_poly = make_valid(geom.Polygon(line_poly)).exterior.coords[:-1]
                    region_elem = TextRegionType(
                        id='region_line_%s' % (idx_line + 1),
                        Coords=CoordsType(points=points_from_polygon(line_poly)))
                    region_elem.add_TextLine(TextLineType(
                        id=line_id,
                        Baseline=BaselineType(points=points_from_polygon(line_baseline)),
                        Coords=CoordsType(points=points_from_polygon(line_poly))))
                    page.add_TextRegion(region_elem)
            self.logger.debug("Found %d lines and %d regions on page %s", idx_line + 1, idx_region + 1, page.id)

    def _process_region(self, page_image, page_coords, region, zoom=1.0):
        def getmask():
            poly = coordinates_of_segment(region, page_image, page_coords)
            poly = geom.Polygon(poly).buffer(20/zoom).exterior.coords[:-1]
            mask = ImageOps.invert(polygon_mask(page_image, poly))
            for line in region.TextLine:
                self.logger.info("Masking existing line %s", line.id)
                poly = coordinates_of_segment(line, page_image, page_coords)
                # poly = geom.Polygon(poly).buffer(20/zoom).exterior.coords[:-1]
                mask.paste(255, mask=polygon_mask(page_image, poly))
            return mask
        res = self.segmenter(page_image, mask=getmask())
        self.logger.debug("Finished segmentation, serializing")
        idx_line = 0
        if self.use_legacy:
            for idx_line, line in enumerate(res.lines):
                line_poly = polygon_from_x0y0x1y1(line.bbox)
                line_poly = coordinates_for_segment(line_poly, None, page_coords)
                line_points = points_from_polygon(line_poly)
                region.add_TextLine(TextLineType(
                    id=f'{region.id}_line_{idx_line + 1}',
                    Coords=CoordsType(points=line_points)))
        else:
            for idx_line, line in enumerate(res.lines):
                line_poly = coordinates_for_segment(line.boundary, None, page_coords)
                line_baseline = coordinates_for_segment(line.baseline, None, page_coords)
                line_id = f'{region.id}_line_{idx_line + 1}'
                line_type = line.tags.get('type', '')
                self.logger.info("Line %s is of type %s", line_id, line_type)
                line_poly = geom.Polygon(line_poly)
                #line_poly = line_poly.intersection(region_poly)
                line_poly = make_valid(line_poly).exterior.coords[:-1]
                region.add_TextLine(TextLineType(
                    id=line_id,
                    Baseline=BaselineType(points=points_from_polygon(line_baseline)),
                    Coords=CoordsType(points=points_from_polygon(line_poly))))
        self.logger.debug("Found %d lines in region %s", idx_line + 1, region.id)

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
