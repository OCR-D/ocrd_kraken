from __future__ import absolute_import
import os
import kraken.binarization
from ocrd import Processor
from ocrd_utils import getLogger, make_file_id, MIMETYPE_PAGE
from ocrd_models.ocrd_page import AlternativeImageType, to_xml
from ocrd_modelfactory import page_from_file

from ocrd_kraken.config import OCRD_TOOL


class KrakenBinarize(Processor):

    def __init__(self, *args, **kwargs):
        kwargs['ocrd_tool'] = OCRD_TOOL['tools']['ocrd-kraken-binarize']
        kwargs['version'] = OCRD_TOOL['version']
        super(KrakenBinarize, self).__init__(*args, **kwargs)

    def process(self):
        """Binarize the pages/regions/lines with Kraken.

        Open and deserialise PAGE input files and their respective images,
        then iterate over the element hierarchy down to the requested
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
        log = getLogger('processor.KrakenBinarize')
        log.debug('Level of operation: "%s"', self.parameter['level-of-operation'])
        log.debug('Input file group %s', self.input_file_grp)
        log.debug('Input files %s', [str(f) for f in self.input_files])
        for (n, input_file) in enumerate(self.input_files):
            log.info("INPUT FILE %i / %s", n, input_file.pageId or input_file.ID)
            file_id = make_file_id(input_file, self.output_file_grp)
            pcgts = page_from_file(self.workspace.download_file(input_file))
            page = pcgts.get_Page()
            page_id = pcgts.pcGtsId or input_file.pageId or input_file.ID # (PageType has no id)
            self.add_metadata(pcgts)

            page_image, page_coords, page_image_info = self.workspace.image_from_page(
                page, page_id, feature_filter='binarized')
            if self.parameter['level-of-operation'] == 'page':
                log.info("Binarizing page '%s'", page_id)
                bin_image = kraken.binarization.nlbin(page_image)
                file_path = self.workspace.save_image_file(
                    bin_image, file_id + '.IMG-BIN',
                    self.output_file_grp,
                    page_id=input_file.pageId)
                page.add_AlternativeImage(AlternativeImageType(
                    filename=file_path,
                    comments=page_coords['features'] + ',binarized'))
            else:
                for region in page.get_AllRegions(classes=['Text']):
                    region_image, region_coords = self.workspace.image_from_segment(
                        region, page_image, page_coords, feature_filter='binarized')
                    if self.parameter['level-of-operation'] == 'region':
                        log.info("Binarizing region '%s'", region.id)
                        bin_image = kraken.binarization.nlbin(region_image)
                        file_path = self.workspace.save_image_file(
                            bin_image, file_id + '_' + region.id + '.IMG-BIN',
                            self.output_file_grp,
                            page_id=input_file.pageId)
                        region.add_AlternativeImage(AlternativeImageType(
                            filename=file_path,
                            comments=region_coords['features'] + ',binarized'))
                    else:
                        for line in region.get_TextLine():
                            line_image, line_coords = self.workspace.image_from_segment(
                                line, region_image, region_coords, feature_filter='binarized')
                            log.info("Binarizing line '%s'", line.id)
                            bin_image = kraken.binarization.nlbin(line_image)
                            file_path = self.workspace.save_image_file(
                                bin_image, file_id + '_' + region.id + '_' + line.id + '.IMG-BIN',
                                self.output_file_grp,
                                page_id=input_file.pageId)
                            line.add_AlternativeImage(AlternativeImageType(
                                filename=file_path,
                                comments=line_coords['features'] + ',binarized'))
            # update METS (add the PAGE file):
            file_path = os.path.join(self.output_file_grp, file_id + '.xml')
            pcgts.set_pcGtsId(file_id)
            out = self.workspace.add_file(
                ID=file_id,
                file_grp=self.output_file_grp,
                pageId=input_file.pageId,
                local_filename=file_path,
                mimetype=MIMETYPE_PAGE,
                content=to_xml(pcgts))
