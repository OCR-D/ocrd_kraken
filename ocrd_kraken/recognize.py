from typing import Optional, Union
from ocrd.processor.base import OcrdPageResult
import regex
import itertools
import numpy as np
from scipy.sparse.csgraph import minimum_spanning_tree
from shapely.geometry import Polygon, LineString, box as Rectangle
from shapely.ops import unary_union, nearest_points

from ocrd import Processor
from ocrd_utils import (
    getLogger,
    coordinates_of_segment,
    coordinates_for_segment,
    bbox_from_polygon,
    points_from_polygon,
    points_from_bbox,
    polygon_from_points,
    xywh_from_points,
    transform_coordinates,
)
from ocrd_models.ocrd_page import (
    OcrdPage,
    RegionRefType,
    RegionRefIndexedType,
    OrderedGroupType,
    OrderedGroupIndexedType,
    UnorderedGroupType,
    UnorderedGroupIndexedType,
    BaselineType,
    TextEquivType,
    WordType,
    GlyphType,
    CoordsType,
    to_xml
)
from ocrd_models.ocrd_page_generateds import (
    ReadingDirectionSimpleType,
    TextLineOrderSimpleType
)

class KrakenRecognize(Processor):

    @property
    def executable(self):
        return 'ocrd-kraken-recognize'

    def setup(self):
        """
        Load model, set predict function
        """

        self.logger = getLogger('processor.KrakenRecognize')
        import torch
        from kraken.rpred import rpred
        from kraken.lib.models import load_any
        model_fname = self.resolve_resource(self.parameter['model'])
        self.logger.info("loading model '%s'", model_fname)
        device = self.parameter['device']
        if device != 'cpu' and not torch.cuda.is_available():
            device = 'cpu'
        if device == 'cpu':
            self.logger.warning("no CUDA device available. Running without GPU will be slow")
        self.model = load_any(model_fname, device=device)
        def predict(page_image, segmentation):
            return rpred(self.model, page_image, segmentation,
                         self.parameter['pad'],
                         self.parameter['bidi_reordering'])
        self.predict = predict

    def process_page_pcgts(self, *input_pcgts: Optional[OcrdPage], page_id: Optional[str] = None) -> OcrdPageResult:
        """Recognize text on lines with Kraken.

        Open the parsed PAGE-XML file, then iterate over the element hierarchy
        down to the line level.

        Set up Kraken to recognise each text line (via coordinates into
        the higher-level image, or from the alternative image. If the model
        has single-channel input with `one_channel_mode=1`, then the image
        must have been binarised. Rescale and pad the image, then pass it
        to the recogniser (along with the boundary polygon).

        Create new Word and Glyph elements below the line level.
        If any text annotation already exists, then remove it - unless
        `overwrite_text=false`. Then put text results and confidence values
        into additional TextEquiv at each level, and make the higher levels
        consistent with that (by concatenation joined by whitespace).

        Return the resulting hierarchy.
        """
        assert self.workspace
        from kraken.containers import Segmentation, BaselineLine, BBoxLine

        pcgts = input_pcgts[0]
        assert pcgts
        page = pcgts.get_Page()
        assert page
        page_image, page_coords, _ = self.workspace.image_from_page(
            page, page_id,
            feature_selector="binarized"
            if self.model.nn.input[1] == 1 and self.model.one_channel_mode == '1'
            else '')
        page_rect = Rectangle(0, 0, page_image.width - 1, page_image.height - 1)
        # TODO: find out whether kraken.lib.xml.XMLPage(...).to_container() is adequate

        all_lines = page.get_AllTextLines()
        # assumes that missing baselines are rare, if any
        if any(line.Baseline for line in all_lines):
            self.logger.info("Converting PAGE to Kraken Segmentation (baselines)")
            segtype = 'baselines'
        else:
            self.logger.info("Converting PAGE to Kraken Segmentation (boxes only)")
            segtype = 'bbox'
        scale = 0.5 * np.median([xywh_from_points(line.Coords.points)['h'] for line in all_lines])
        self.logger.info("Estimated scale: %.1f", scale)
        seglines = []
        for line in all_lines:
            # FIXME: see whether model prefers baselines or bbox crops (seg_type)
            # FIXME: even if we do not have baselines, emulating baseline+boundary might be useful to prevent automatic center normalization
            poly = coordinates_of_segment(line, None, page_coords)
            poly = make_valid(Polygon(poly))
            poly = poly.intersection(page_rect)
            if segtype == 'baselines':
                if line.Baseline is None:
                    base = dummy_baseline_of_segment(line, page_coords)
                else:
                    base = baseline_of_segment(line, page_coords)
                    if len(base) < 2 or np.abs(np.mean(base[0] - base[-1])) <= 1:
                        base = dummy_baseline_of_segment(line, page_coords)
                    elif not LineString(base).intersects(poly):
                        base = dummy_baseline_of_segment(line, page_coords)
                # kraken expects baseline to be fully contained in boundary
                base = LineString(base)
                if poly.is_empty:
                    poly = polygon_from_baseline(base, scale=scale)
                elif not base.within(poly):
                    poly = join_polygons([poly, polygon_from_baseline(base, scale=scale)],
                                         loc=line.id, scale=scale)
                seglines.append(BaselineLine(baseline=list(map(tuple, base.coords)),
                                             boundary=list(map(tuple, poly.exterior.coords)),
                                             id=line.id,
                                             tags={'type': 'default'}))
                # write back
                base = coordinates_for_segment(base.coords, None, page_coords)
                line.set_Baseline(BaselineType(points=points_from_polygon(base)))
                poly = coordinates_for_segment(poly.exterior.coords[:-1], None, page_coords)
                line.set_Coords(CoordsType(points=points_from_polygon(poly)))
            else:
                seglines.append(BBoxLine(bbox=poly.envelope.bounds,
                                         id=line.id))

        segmentation = Segmentation(lines=seglines,
                                    script_detection=False,
                                    text_direction='horizontal-lr',
                                    type=segtype,
                                    imagename=page_id)
        for idx_line, ocr_record in enumerate(self.predict(page_image, segmentation)):
            line = all_lines[idx_line]
            id_line = line.id
            if not ocr_record.prediction and not ocr_record.cuts:
                self.logger.warning('No results for line "%s"', line.id)
                continue
            text_line = ocr_record.prediction
            if len(ocr_record.confidences) > 0:
                conf_line = sum(ocr_record.confidences) / len(ocr_record.confidences)
            else:
                conf_line = None
            if self.parameter['overwrite_text']:
                line.TextEquiv = []
            line.add_TextEquiv(TextEquivType(Unicode=text_line, conf=conf_line))
            idx_word = 0
            line_offset = 0
            for text_word in regex.splititer(r'(\s+)', text_line):
                next_offset = line_offset + len(text_word)
                cuts_word = list(map(list, ocr_record.cuts[line_offset:next_offset]))
                # fixme: kraken#98 says the Pytorch CTC output is too impoverished to yield good glyph stops
                # as a workaround, here we just steal from the next glyph start, respectively:
                if len(ocr_record.cuts) > next_offset + 1:
                    cuts_word.extend(list(map(list, ocr_record.cuts[next_offset:next_offset+1])))
                else:
                    cuts_word.append(list(ocr_record.cuts[-1]))
                confidences_word = ocr_record.confidences[line_offset:next_offset]
                line_offset = next_offset
                if len(text_word.strip()) == 0:
                    continue
                id_word = '%s_word_%s' % (id_line, idx_word + 1)
                idx_word += 1
                poly_word = [point for cut in cuts_word for point in cut]
                bbox_word = bbox_from_polygon(coordinates_for_segment(poly_word, None, page_coords))
                # avoid zero-size coords on ties
                bbox_word = np.array(bbox_word, dtype=int)
                if np.prod(bbox_word[2:4] - bbox_word[0:2]) == 0:
                    bbox_word[2:4] += 1
                if len(confidences_word) > 0:
                    conf_word = sum(confidences_word) / len(confidences_word)
                else:
                    conf_word = None
                word = WordType(id=id_word,
                                Coords=CoordsType(points=points_from_bbox(*bbox_word)))
                word.add_TextEquiv(TextEquivType(Unicode=text_word, conf=conf_word))
                for idx_glyph, text_glyph in enumerate(text_word):
                    id_glyph = '%s_glyph_%s' % (id_word, idx_glyph + 1)
                    poly_glyph = cuts_word[idx_glyph] + cuts_word[idx_glyph + 1]
                    bbox_glyph = bbox_from_polygon(coordinates_for_segment(poly_glyph, None, page_coords))
                    # avoid zero-size coords on ties
                    bbox_glyph = np.array(bbox_glyph, dtype=int)
                    if np.prod(bbox_glyph[2:4] - bbox_glyph[0:2]) == 0:
                        bbox_glyph[2:4] += 1
                    conf_glyph = confidences_word[idx_glyph]
                    glyph = GlyphType(id=id_glyph,
                                      Coords=CoordsType(points=points_from_bbox(*bbox_glyph)))
                    glyph.add_TextEquiv(TextEquivType(Unicode=text_glyph, conf=conf_glyph))
                    word.add_Glyph(glyph)
                line.add_Word(word)
            self.logger.info('Recognized line "%s"', line.id)
            page_update_higher_textequiv_levels('line', pcgts)

        self.logger.info("Finished recognition, serializing")
        return OcrdPageResult(pcgts)

# zzz should go into core ocrd_utils
def baseline_of_segment(segment, coords):
    line = np.array(polygon_from_points(segment.Baseline.points))
    line = transform_coordinates(line, coords['transform'])
    return np.round(line).astype(np.int32)

def dummy_baseline_of_segment(segment, coords, yrel=0.2):
    poly = coordinates_of_segment(segment, None, coords)
    xmin, ymin, xmax, ymax = bbox_from_polygon(poly)
    ymid = ymin + yrel * (ymax - ymin)
    return [[xmin, ymid], [xmax, ymid]]

# zzz should go into core ocrd_utils
def polygon_from_baseline(baseline, scale : Union[float, np.floating] = 20):
    if not isinstance(baseline, LineString):
        baseline = LineString(baseline)
    ltr = baseline.coords[0][0] < baseline.coords[-1][0]
    # left-hand side if left-to-right, and vice versa
    polygon = make_valid(join_polygons([baseline.buffer(scale * (-1) ** ltr,
                                                        single_sided=True)],
                                       scale=scale))
    return polygon

def join_polygons(polygons, loc='', scale : Union[float, np.floating] = 20):
    """construct concave hull (alpha shape) from input polygons"""
    # compoundp = unary_union(polygons)
    # jointp = compoundp.convex_hull
    polygons = list(itertools.chain.from_iterable([
        poly.geoms if poly.geom_type in ['MultiPolygon', 'GeometryCollection']
        else [poly]
        for poly in polygons]))
    npoly = len(polygons)
    if npoly == 1:
        return polygons[0]
    # find min-dist path through all polygons (travelling salesman)
    pairs = itertools.combinations(range(npoly), 2)
    dists = np.eye(npoly, dtype=float)
    for i, j in pairs:
        dist = polygons[i].distance(polygons[j])
        if dist < 1e-5:
            dist = 1e-5 # if pair merely touches, we still need to get an edge
        dists[i, j] = dist
        dists[j, i] = dist
    dists = minimum_spanning_tree(dists, overwrite=True)
    # add bridge polygons (where necessary)
    for prevp, nextp in zip(*dists.nonzero()):
        prevp = polygons[prevp]
        nextp = polygons[nextp]
        nearest = nearest_points(prevp, nextp)
        bridgep = LineString(nearest).buffer(max(1, scale/5), resolution=1)
        polygons.append(bridgep)
    jointp = unary_union(polygons)
    assert jointp.geom_type == 'Polygon', jointp.wkt
    if jointp.minimum_clearance < 1.0:
        # follow-up calculations will necessarily be integer;
        # so anticipate rounding here and then ensure validity
        jointp = Polygon(np.round(jointp.exterior.coords))
        jointp = make_valid(jointp)
    return jointp

def make_valid(polygon):
    points = list(polygon.exterior.coords)
    for split in range(1, len(points)):
        if polygon.is_valid or polygon.simplify(polygon.area).is_valid:
            break
        # simplification may not be possible (at all) due to ordering
        # in that case, try another starting point
        polygon = Polygon(points[-split:]+points[:-split])
    for tolerance in range(int(polygon.area)):
        if polygon.is_valid:
            break
        # simplification may require a larger tolerance
        polygon = polygon.simplify(tolerance + 1)
    return polygon

# from ocrd_tesserocr...

def page_element_unicode0(element):
    """Get Unicode string of the first text result."""
    if element.get_TextEquiv():
        return element.get_TextEquiv()[0].Unicode or ''
    else:
        return ''

def page_element_conf0(element):
    """Get confidence (as float value) of the first text result."""
    if element.get_TextEquiv():
        # generateDS does not convert simpleType for attributes (yet?)
        return float(element.get_TextEquiv()[0].conf or "1.0")
    return 1.0

def page_update_higher_textequiv_levels(level, pcgts, overwrite=True):
    """Update the TextEquivs of all PAGE-XML hierarchy levels above ``level`` for consistency.

    Starting with the lowest hierarchy level chosen for processing,
    join all first TextEquiv.Unicode (by the rules governing the respective level)
    into TextEquiv.Unicode of the next higher level, replacing them.
    If ``overwrite`` is false and the higher level already has text, keep it.

    When two successive elements appear in a ``Relation`` of type ``join``,
    then join them directly (without their respective white space).

    Likewise, average all first TextEquiv.conf into TextEquiv.conf of the next higher level.

    In the process, traverse the words and lines in their respective ``readingDirection``,
    the (text) regions which contain lines in their respective ``textLineOrder``, and
    the (text) regions which contain text regions in their ``ReadingOrder``
    (if they appear there as an ``OrderedGroup``).
    Where no direction/order can be found, use XML ordering.

    Follow regions recursively, but make sure to traverse them in a depth-first strategy.
    """
    page = pcgts.get_Page()
    relations = page.get_Relations() # get RelationsType
    if relations:
        relations = relations.get_Relation() # get list of RelationType
    else:
        relations = []
    joins = list()
    for relation in relations:
        if relation.get_type() == 'join': # ignore 'link' type here
            joins.append((relation.get_SourceRegionRef().get_regionRef(),
                          relation.get_TargetRegionRef().get_regionRef()))
    reading_order = dict()
    ro = page.get_ReadingOrder()
    if ro:
        page_get_reading_order(reading_order, ro.get_OrderedGroup() or ro.get_UnorderedGroup())
    if level != 'region':
        for region in page.get_AllRegions(classes=['Text']):
            # order is important here, because regions can be recursive,
            # and we want to concatenate by depth first;
            # typical recursion structures would be:
            #  - TextRegion/@type=paragraph inside TextRegion
            #  - TextRegion/@type=drop-capital followed by TextRegion/@type=paragraph inside TextRegion
            #  - any region (including TableRegion or TextRegion) inside a TextRegion/@type=footnote
            #  - TextRegion inside TableRegion
            subregions = region.get_TextRegion()
            if subregions: # already visited in earlier iterations
                # do we have a reading order for these?
                # TODO: what if at least some of the subregions are in reading_order?
                if (all(subregion.id in reading_order for subregion in subregions) and
                    isinstance(reading_order[subregions[0].id], # all have .index?
                               (OrderedGroupType, OrderedGroupIndexedType))):
                    subregions = sorted(subregions, key=lambda subregion:
                                        reading_order[subregion.id].index)
                region_unicode = page_element_unicode0(subregions[0])
                for subregion, next_subregion in zip(subregions, subregions[1:]):
                    if (subregion.id, next_subregion.id) not in joins:
                        region_unicode += '\n' # or '\f'?
                    region_unicode += page_element_unicode0(next_subregion)
                region_conf = sum(page_element_conf0(subregion) for subregion in subregions)
                region_conf /= len(subregions)
            else: # TODO: what if a TextRegion has both TextLine and TextRegion children?
                lines = region.get_TextLine()
                if ((region.get_textLineOrder() or
                     page.get_textLineOrder()) ==
                    TextLineOrderSimpleType.BOTTOMTOTOP):
                    lines = list(reversed(lines))
                if level != 'line':
                    for line in lines:
                        words = line.get_Word()
                        if ((line.get_readingDirection() or
                             region.get_readingDirection() or
                             page.get_readingDirection()) ==
                            ReadingDirectionSimpleType.RIGHTTOLEFT):
                            words = list(reversed(words))
                        if level != 'word':
                            for word in words:
                                glyphs = word.get_Glyph()
                                if ((word.get_readingDirection() or
                                     line.get_readingDirection() or
                                     region.get_readingDirection() or
                                     page.get_readingDirection()) ==
                                    ReadingDirectionSimpleType.RIGHTTOLEFT):
                                    glyphs = list(reversed(glyphs))
                                word_unicode = ''.join(page_element_unicode0(glyph) for glyph in glyphs)
                                word_conf = sum(page_element_conf0(glyph) for glyph in glyphs)
                                if glyphs:
                                    word_conf /= len(glyphs)
                                if not word.get_TextEquiv() or overwrite:
                                    word.set_TextEquiv( # replace old, if any
                                        [TextEquivType(Unicode=word_unicode, conf=word_conf)])
                        line_unicode = ' '.join(page_element_unicode0(word) for word in words)
                        line_conf = sum(page_element_conf0(word) for word in words)
                        if words:
                            line_conf /= len(words)
                        if not line.get_TextEquiv() or overwrite:
                            line.set_TextEquiv( # replace old, if any
                                [TextEquivType(Unicode=line_unicode, conf=line_conf)])
                region_unicode = ''
                region_conf = 0
                if lines:
                    region_unicode = page_element_unicode0(lines[0])
                    for line, next_line in zip(lines, lines[1:]):
                        words = line.get_Word()
                        next_words = next_line.get_Word()
                        if not (words and next_words and (words[-1].id, next_words[0].id) in joins):
                            region_unicode += '\n'
                        region_unicode += page_element_unicode0(next_line)
                    region_conf = sum(page_element_conf0(line) for line in lines)
                    region_conf /= len(lines)
            if not region.get_TextEquiv() or overwrite:
                region.set_TextEquiv( # replace old, if any
                    [TextEquivType(Unicode=region_unicode, conf=region_conf)])

def page_get_reading_order(ro, rogroup):
    """Add all elements from the given reading order group to the given dictionary.

    Given a dict ``ro`` from layout element IDs to ReadingOrder element objects,
    and an object ``rogroup`` with additional ReadingOrder element objects,
    add all references to the dict, traversing the group recursively.
    """
    regionrefs = list()
    if isinstance(rogroup, (OrderedGroupType, OrderedGroupIndexedType)):
        regionrefs = (rogroup.get_RegionRefIndexed() +
                      rogroup.get_OrderedGroupIndexed() +
                      rogroup.get_UnorderedGroupIndexed())
    if isinstance(rogroup, (UnorderedGroupType, UnorderedGroupIndexedType)):
        regionrefs = (rogroup.get_RegionRef() +
                      rogroup.get_OrderedGroup() +
                      rogroup.get_UnorderedGroup())
    for elem in regionrefs:
        ro[elem.get_regionRef()] = elem
        if not isinstance(elem, (RegionRefType, RegionRefIndexedType)):
            page_get_reading_order(ro, elem)
