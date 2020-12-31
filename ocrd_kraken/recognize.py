from ocrd import Processor
from os.path import join
from ocrd_utils import (
    getLogger,
    make_file_id,
    assert_file_grp_cardinality,
    points_from_polygon,
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
        super(KrakenRecognize, self).__init__(*args, **kwargs)

    def process(self):
        """
        Recognize with kraken
        """
        from kraken.rpred import rpred
        from kraken.lib.models import load_any
        log = getLogger('processor.KrakenRecognize')
        assert_file_grp_cardinality(self.input_file_grp, 1)
        assert_file_grp_cardinality(self.output_file_grp, 1)
        model_fname = self.resolve_resource(self.parameter['model'])
        pad = self.parameter['pad']
        bidi_reordering = self.parameter['bidi_reordering']
        device = self.parameter['device']

        log.info("loading model %s" % model_fname)
        model = load_any(model_fname, device=device)

        for n, input_file in enumerate(self.input_files):
            page_id = input_file.pageId or input_file.ID
            log.info("INPUT FILE %i / %s of %s", n, page_id, len(self.input_files))
            pcgts = page_from_file(self.workspace.download_file(input_file))
            self.add_metadata(pcgts)
            page = pcgts.get_Page()
            page_image, _, _ = self.workspace.image_from_page(page, page_id, feature_selector="binarized")

            log.info("Converting PAGE to kraken 'bounds' format")
            bounds = {'boxes': [], 'script_detection': True, 'text_direction': 'horizontal-lr'}
            all_lines = page.get_AllTextLine()
            for line in all_lines:
                bounds['boxes'].append(bbox_from_points(line.get_Coords().points))

            idx_line = 0
            def _make_word(id_line, idx_word):
                word = WordType(id='%s_word_%s' % (id_line, idx_word),
                        Coords=CoordsType(points=''))
                word.add_TextEquiv(TextEquivType(Unicode=''))
                return word
            for ocr_record in rpred(model, page_image, bounds, pad, bidi_reordering):
                idx_word = 0
                current_word = _make_word(all_lines[idx_line].id, idx_word)
                for text, coords, conf in ocr_record:
                    idx_glyph = 0
                    if text == ' ':
                        idx_glyph = 0
                        idx_word += 1
                        all_lines[idx_line].add_Word(current_word)
                        current_word = _make_word(all_lines[idx_line].id, idx_word)
                    else:
                        current_word.get_TextEquiv()[0].Unicode += text
                        # TODO word coordinates
                        glyph = GlyphType(
                            id='%s_glyph_%s' % (current_word.id, idx_glyph),
                            Coords=CoordsType(points=points_from_polygon(coords)))
                        glyph.add_TextEquiv(TextEquivType(Unicode=text, conf=conf))
                        current_word.add_Glyph(glyph)
                all_lines[idx_line].add_Word(current_word)
                log.info('Recognizing line %s ' % all_lines[idx_line].id)
                # TODO line coordinates
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
