import os
import json
import tempfile
import subprocess
from ..Task import Task

class SGTexturePublish(Task):
    """
    Publish a texture to shotgun.

    Optional Options: publishedFileType and comment.
    """

    __defaultPublishedFileType = "Texture"
    __defaultComment = "texture publish"

    def __init__(self, *args, **kwargs):
        """
        Create a TexturePublish object.
        """
        super(SGTexturePublish, self).__init__(*args, **kwargs)

        self.setOption('publishedFileType', self.__defaultPublishedFileType)
        self.setOption('comment', self.__defaultComment)

    def _perform(self):
        """
        Perform the task.
        """
        currentFolder = os.path.dirname(os.path.realpath(__file__))
        infoCrawler = list(filter(lambda x: x.var('baseName') == "info.json", self.pathCrawlers()))[0]
        dataCrawler = list(filter(lambda x: x.var('baseName') == "data.json", self.pathCrawlers()))[0]

        # metadata information about the version
        info = infoCrawler.contents()
        assetName = info["assetName"]
        variant = info["variant"]
        version = info["version"]
        job = info["job"]

        # get version, assetName, variant from json contents under info
        output = {
            'job': job,
            'assetName': assetName,
            'name': "{0}-{1}".format(assetName, variant),
            'jsonFile': dataCrawler.var('filePath'),
            'publishedFileType': self.option('publishedFileType'),
            'version': version,
            'comment': self.option('comment')
        }

        # generating a temporary file that is going to contain the frames
        # that should be processed by ffmpeg
        shotgunTempFile = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".json",
            mode='w'
        )

        shotgunTempFile.write(json.dumps(output))
        shotgunTempFile.close()

        shotgunPythonFile = os.path.join(
            currentFolder,
            "aux",
            "runTexturePublish.py"
        )

        env = dict(os.environ)
        del env['PYTHONPATH']

        command = 'shotgunpython {pythonFile} {jsonFile}'.format(
            pythonFile=shotgunPythonFile,
            jsonFile=shotgunTempFile.name
        )

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            shell=True
        )

        # capturing the output
        output, error = process.communicate()

        # removing the temporary file
        os.unlink(shotgunTempFile.name)

        # in case of any erros
        if error:
            raise Exception(error)

        # this task does not return any crawlers as result
        return []


# registering task
Task.register(
    'sgTexturePublish',
    SGTexturePublish
)