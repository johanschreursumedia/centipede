import os
import json
import time
import shutil
from ..Task import Task

class FileNotUnderDataDirectoryError(Exception):
    """File Not Under Data Directory Error."""

class MetadataNotFoundError(Exception):
    """Metadata Not Found Error."""

class CreateVersion(Task):
    """
    ABC for creating a version.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a version.
        """
        super(CreateVersion, self).__init__(*args, **kwargs)
        self.__files = {}
        self.__info = {}
        self.__assetName = None
        self.__variant = None
        self.__startTime = time.time()
        self.__loadedPublishedData = False

    def version(self):
        """
        Return an integer containing the published version.
        """
        self.__loadPublishData()

        return self.__version

    def variant(self):
        """
        Return the name for a variant or None.
        """
        self.__loadPublishData()

        return self.__assetName

    def assetName(self):
        """
        Return the name for the asset or None.
        """
        self.__loadPublishData()

        return self.__assetName

    def versionPath(self):
        """
        Return the path for the version base folder.
        """
        self.__loadPublishData()

        return self.__versionPath

    def dataPath(self):
        """
        Return the path where the data should be stored for the version.
        """
        self.__loadPublishData()

        return self.__dataPath

    def configPath(self):
        """
        Return the path about the location for the configuration used by the ingestor.
        """
        self.__loadPublishData()

        return self.__configPath

    def addFile(self, filePath, metadata=None):
        """
        Add a published file that is under the 'data' directory to the version.

        This information is used to write "data.json" where metadata information
        can be associated with the file through metadata parameter
        passed as dictionary.
        """
        # making sure the file is under the data directory
        if not filePath.startswith(self.dataPath() + os.sep):
            raise FileNotUnderDataDirectoryError(
                'File "{0}" is not under data directory "{1}"'.format(
                    filePath,
                    self.dataPath()
                )
            )

        if metadata is None:
            metadata = {}

        assert isinstance(metadata, dict), "metadata needs to be a dict or None"

        # making metadata immutable
        metadata = dict(metadata)

        # getting file size
        metadata['size'] = os.stat(filePath).st_size

        # adding type based on the file ext when it's not defined
        if 'type' not in metadata:
            metadata['type'] = os.path.splitext(filePath)[-1][1:]

        self.__files[filePath] = metadata

    def files(self):
        """
        Return a list of published file names under version data.
        """
        return list(self.__files.keys())

    def fileMetadata(self, filePath):
        """
        Return the metadata for the input file path.
        """
        if filePath in self.__files:
            # we don't want to share implicitly the metadata object.
            return dict(self.__files[filePath])

        raise MetadataNotFoundError(
            'Could not find metadata for the file "{0}"'.format(filePath)
        )

    def addInfo(self, key, value):
        """
        Associate an info to the published version.

        This information is used to write "info.json".
        """
        self.__info[key] = value

    def _perform(self):
        """
        Perform the task.
        """
        self.__writeEnv()
        self.__writeInfo()
        self.__writeData()
        self.__copyIngestorConfig()

    def __copyIngestorConfig(self):
        """
        Copy the configuration used by the ingestor to the current version.
        """
        shutil.copytree(
            self.configPath(),
            os.path.join(self.versionPath(), "ingestorConfig")
        )

    def __writeInfo(self):
        """
        Write info.json file.
        """
        totalSize = 0
        for fileName, metadata in self.__files.items():
            totalSize += metadata['size']
        self.addInfo('size', totalSize)
        self.addInfo('version', self.version())
        self.addInfo('user', os.environ.get('USERNAME', ''))
        self.addInfo('totalTime', int(time.time() - self.__startTime))
        if self.assetName():
            self.addInfo('assetName', self.assetName())
            self.addInfo('variant', self.variant())

        # writing info json file
        infoJsonFilePath = os.path.join(self.versionPath(), "info.json")
        with open(infoJsonFilePath, 'w') as jsonOutFile:
            json.dump(self.__info, jsonOutFile, indent=4, sort_keys=True)

    def __writeEnv(self):
        """
        Write env.json file.
        """
        envJsonFilePath = os.path.join(self.versionPath(), "env.json")
        with open(envJsonFilePath, 'w') as jsonOutFile:
            json.dump(dict(os.environ), jsonOutFile, indent=4, sort_keys=True)

    def __writeData(self):
        """
        Write data.json file.
        """
        dataJsonFilePath = os.path.join(self.versionPath(), "data.json")
        with open(dataJsonFilePath, 'w') as jsonOutFile:
            filesData = {}

            for filePath, metadata in self.__files.items():
                relativePath = filePath[len(self.versionPath()) + 1:]
                filesData[relativePath] = metadata

            json.dump(filesData, jsonOutFile, indent=4, sort_keys=True)

    def __loadPublishData(self):
        """
        Load the static information about the publish.
        """
        if not self.__loadedPublishedData and self.pathCrawlers():
            self.__loadedPublishedData = True

            # all crawlers must contain the same information about assetName,
            # variant and version. For this reason looking only in the first one
            pathCrawler = self.pathCrawlers()[0]

            # may contain asset name, if that is the case it should
            # also contain variant.
            if "assetName" in pathCrawler.varNames():
                self.__assetName = pathCrawler.var("assetName")
                self.__variant = pathCrawler.var("variant")

            self.__versionPath = os.path.dirname(self.filePath(pathCrawler))
            self.__dataPath = os.path.join(self.__versionPath, "data")
            self.__configPath = pathCrawler.var('configPath')

            # looking for the version based on the version folder name
            # that follows the convention "v001"
            self.__version = int(
                os.path.basename(self.__versionPath)[1:]
            )


# registering task
Task.register(
    'createVersion',
    CreateVersion
)
