from ocrd import Processor
from os.path import join
from ocrd_utils import (
    getLogger,
    make_file_id,
    assert_file_grp_cardinality,
    coordinates_of_segment,
    coordinates_for_segment,
    bbox_from_polygon,
    points_from_polygon,
    points_from_bbox,
    polygon_from_points,
    bbox_from_points,
    MIMETYPE_PAGE,
)
from ocrd_modelfactory import page_from_file
from ocrd_models.ocrd_page import TextEquivType, WordType, GlyphType, CoordsType, to_xml

from ocrd_kraken.config import OCRD_TOOL

class KrakenRecognize(Processor):

    def __init__(self, *args, **kwargs):
        kwargs['ocrd_tool'] = OCRD_TOOL['tools']['ocrd-kraken-recognize']
        kwargs['version'] = OCRD_TOOL['version']
        super().__init__(*args, **kwargs)
        if hasattr(self, 'output_file_grp'):
            # processing context
            self.setup()

    def setup(self):
        """
        Load models
        """
        log = getLogger('processor.KrakenRecognize')
        from kraken.rpred import rpred
        from kraken.lib.models import load_any
        model_fname = self.resolve_resource(self.parameter['model'])
        log.info("loading model '%s'", model_fname)
        self.model = load_any(model_fname, device=self.parameter['device'])
        def predict(page_image, bounds):
            return rpred(self.model, page_image, bounds,
                         self.parameter['pad'],
                         self.parameter['bidi_reordering'])
        self.predict = predict

    def process(self):
        """
        Recognize with kraken
        """
        log = getLogger('processor.KrakenRecognize')
        assert_file_grp_cardinality(self.input_file_grp, 1)
        assert_file_grp_cardinality(self.output_file_grp, 1)

        for n, input_file in enumerate(self.input_files):
            page_id = input_file.pageId or input_file.ID
            log.info("INPUT FILE %i / %s of %s", n, page_id, len(self.input_files))
            pcgts = page_from_file(self.workspace.download_file(input_file))
            self.add_metadata(pcgts)
            page = pcgts.get_Page()
            page_image, page_coords, _ = self.workspace.image_from_page(
                page, page_id,
                feature_selector="binarized" if self.model.one_channel_mode == '1' else '')

            log.info("Converting PAGE to kraken 'bounds' format")
            bounds = {'boxes': [], 'script_detection': True, 'text_direction': 'horizontal-lr'}
            all_lines = page.get_AllTextLines()
            for line in all_lines:
                # FIXME: see whether model needs baselines or bbox crops (seg_type)
                # FIXME: if we have baselines, pass 'lines' (baseline+boundary) instead of 'boxes'
                poly = coordinates_of_segment(line, None, page_coords)
                xmin, ymin, xmax, ymax = bbox_from_polygon(poly)
                bbox = (max(xmin, 0), max(ymin, 0), min(page_image.width, xmax), min(page_image.height, ymax))
                bounds['boxes'].append(bbox)

            idx_line = 0
            def _make_word(id_line, idx_word):
                word = WordType(id='%s_word_%s' % (id_line, idx_word),
                        Coords=CoordsType(points=''))
                word.add_TextEquiv(TextEquivType(Unicode=''))
                return word
            for ocr_record in self.predict(page_image, bounds):
                idx_word = 0
                current_word = _make_word(all_lines[idx_line].id, idx_word)
                idx_glyph = 0
                for text, poly, conf in ocr_record:
                    poly = coordinates_for_segment(poly, None, page_coords)
                    if text == ' ':
                        if idx_glyph == 0:
                            continue
                        idx_glyph = 0
                        idx_word += 1
                        all_lines[idx_line].add_Word(current_word)
                        current_word.get_Coords().points = points_from_bbox(*bbox_from_polygon(polygon_from_points(current_word.get_Coords().points.strip())))
                        current_word = _make_word(all_lines[idx_line].id, idx_word)
                    else:
                        idx_glyph += 1
                        current_word.get_TextEquiv()[0].Unicode += text
                        current_word.get_Coords().points += ' ' + points_from_polygon(poly)
                        # TODO word coordinates
                        glyph = GlyphType(
                            id='%s_glyph_%s' % (current_word.id, idx_glyph),
                            Coords=CoordsType(points=points_from_polygon(poly)))
                        glyph.add_TextEquiv(TextEquivType(Unicode=text, conf=conf))
                        current_word.add_Glyph(glyph)
                if idx_glyph > 0:
                    current_word.get_Coords().points = points_from_bbox(*bbox_from_polygon(polygon_from_points(current_word.get_Coords().points.strip())))
                    all_lines[idx_line].add_Word(current_word)
                log.info('Recognized line %s ' % all_lines[idx_line].id)
                all_lines[idx_line].add_TextEquiv(TextEquivType(
                    Unicode=ocr_record.prediction))
                idx_line += 1

            log.info("Finished recognition, serializing")
            file_id = make_file_id(input_file, self.output_file_grp)
            pcgts.set_pcGtsId(file_id)
            self.workspace.add_file(
                ID=file_id,
                file_grp=self.output_file_grp,
                pageId=input_file.pageId,
                mimetype=MIMETYPE_PAGE,
                local_filename=join(self.output_file_grp, f'{file_id}.xml'),
                content=to_xml(pcgts))
