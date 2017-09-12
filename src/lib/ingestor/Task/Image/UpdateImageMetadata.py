import os
from datetime import datetime
import OpenImageIO as oiio
from ..Task import Task


class UpdateImageMetadata(Task):
    """
    Updates the image metadata using oiio.
    """

    def _perform(self):
        """
        Perform the task.
        """
        for pathCrawler in self.pathCrawlers():
            yield pathCrawler

            targetFilePath = self.filePath(pathCrawler)

            # converting image using open image io
            inputImageFilePath = pathCrawler.var('filePath')
            imageInput = oiio.ImageInput.open(inputImageFilePath)
            inputSpec = imageInput.spec()

            # updating umedia metadata
            self.updateUmediaMetadata(inputSpec, pathCrawler)

            # writting image with updated metadata
            outImage = oiio.ImageOutput.create(targetFilePath)
            outImage.open(
                targetFilePath,
                inputSpec,
                oiio.ImageOutputOpenMode.Create
            )

            outImage.copy_image(imageInput)
            outImage.close()

    @classmethod
    def updateUmediaMetadata(cls, spec, crawler):
        """
        Update the spec with the image metadata information.
        """
        headerInfo = {
            'sourceFile': crawler.var('filePath'),
            'fileUpdatedTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'uverVersion': os.environ.get('UVER_VERSION', ''),
            'ingestorUser': os.environ['USERNAME'],
            'ingestorVersion': os.environ.get('UVER_INGESTOR_VERSION', ''),
        }

        for headerName, headerValue in  headerInfo.items():
            spec.attribute(
                'umedia:{0}'.format(headerName),
                headerValue
            )


# registering task
Task.register(
    'updateImageMetadata',
    UpdateImageMetadata
)