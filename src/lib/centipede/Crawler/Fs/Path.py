import os
import json
from ..Crawler import Crawler
from ...PathHolder import PathHolder
from collections import OrderedDict

# compatibility with python 2/3
try:
    basestring
except NameError:
    basestring = str

class TestCrawlerError(Exception):
    """Test crawler error."""

class CreateCrawlerError(Exception):
    """Create crawler error."""

class Path(Crawler):
    """
    Abstracted Path.
    """

    __registeredTypes = OrderedDict()

    def __init__(self, pathHolder, parentCrawler=None):
        """
        Create a crawler (use the factory function Path.create instead).
        """
        super(Path, self).__init__(pathHolder.baseName(), parentCrawler)

        self.__setPathHolder(pathHolder)
        self.setVar('filePath', pathHolder.path())
        self.setVar('ext', pathHolder.ext())
        self.setVar('baseName', pathHolder.baseName())
        self.setVar('name', os.path.splitext(pathHolder.baseName())[0])
        if 'sourceDirectory' not in self.varNames():
            path = pathHolder.path()
            if not pathHolder.isDirectory():
                path = os.path.dirname(path)
            self.setVar('sourceDirectory', path)
        self.__globCache = None

    def pathHolder(self):
        """
        Return the path holder object used to create the crawler.
        """
        return self.__pathHolder

    def clone(self):
        """
        Return a cloned instance about the current crawler.
        """
        return Path.createFromJson(self.toJson())

    def toJson(self):
        """
        Serialize the path crawler to json (it can be recovery later using fromJson).
        """
        crawlerContents = {
            "vars": {},
            "contextVarNames": [],
            "tags": {}
        }

        for varName in self.varNames():
            crawlerContents['vars'][varName] = self.var(varName)

        for varName in self.contextVarNames():
            crawlerContents['contextVarNames'].append(varName)

        for tagName in self.tagNames():
            crawlerContents['tags'][tagName] = self.tag(tagName)

        return json.dumps(
            crawlerContents,
            indent=4,
            separators=(',', ': ')
        )

    def glob(self, filterTypes=[], useCache=True):
        """
        Return a list of all crawlers found recursively under this path.

        Filter result list by crawler type (str) or class type (both include derived classes).
        """
        if self.__globCache is None or not useCache:
            # Recursively collect all crawlers for this path
            self.__globCache = Path.__collectCrawlers(self)

        if not filterTypes:
            return self.__globCache

        filteredCrawlers = set()
        for filterType in filterTypes:
            subClasses = tuple(Path.registeredSubclasses(filterType))
            filteredCrawlers.update(
                    filter(lambda x: isinstance(x, subClasses), self.__globCache)
            )
        return list(filteredCrawlers)

    def globFromParent(self, filterTypes=[], useCache=True):
        """
        Return a list of all crawlers found recursively under the parent directory of the given path.

        Filter result list by exact crawler type (str) or class type (includes derived classes).
        """
        parentDir = os.path.dirname(self.var("filePath"))
        return Path.createFromPath(parentDir).glob(filterTypes, useCache)

    @classmethod
    def test(cls, parentCrawler, pathInfo):
        """
        Tells if crawler implementation, can handle it.

        For re-implementation: Should return a boolean telling if the
        crawler implementation can crawler it.
        """
        raise NotImplementedError

    @staticmethod
    def register(name, crawlerClass):
        """
        Register a path type.

        The registration is used to tell the order that the crawler types
        are going to be tested. The test is done from the latest registrations to
        the first registrations (bottom top). The only exception is for types that
        get overriden where the position is going to be the same.
        """
        assert issubclass(crawlerClass, Path), \
            "Invalid crawler class!"

        Path.__registeredTypes[name] = crawlerClass

    @staticmethod
    def registeredNames():
        """
        Return a list of registered path types.
        """
        return Path.__registeredTypes.keys()

    @staticmethod
    def registeredSubclasses(baseClassOrTypeName):
        """
        Return a list of registered subClasses for the given class or class type name.
        """
        baseClass = Path.__baseClass(baseClassOrTypeName)
        result = set()
        for registeredType in Path.__registeredTypes.values():
            if issubclass(registeredType, baseClass):
                result.add(registeredType)
        return list(result)

    @staticmethod
    def registeredSubTypes(baseClassOrTypeName):
        """
        Return a list of registered names of all derived classes for the given class or class type name.
        """
        baseClass = Path.__baseClass(baseClassOrTypeName)
        result = set()
        for name, registeredType in Path.__registeredTypes.items():
            if issubclass(registeredType, baseClass):
                result.add(name)
        return list(result)

    @staticmethod
    def __baseClass(baseClassOrTypeName):
        """
        Return a valid base class for the given class or class type name.
        """
        if isinstance(baseClassOrTypeName, basestring):
            assert baseClassOrTypeName in Path.__registeredTypes
            baseClass = Path.__registeredTypes[baseClassOrTypeName]
        else:
            assert issubclass(baseClassOrTypeName, Path)
            baseClass = baseClassOrTypeName
        return baseClass

    @staticmethod
    def create(pathHolder, parentCrawler=None):
        """
        Create a crawler for the input path holder.
        """
        result = None
        for registeredName in reversed(Path.__registeredTypes.keys()):
            testCrawlerType = Path.__registeredTypes[registeredName]
            passedTest = False

            # testing crawler
            try:
                passedTest = testCrawlerType.test(pathHolder, parentCrawler)
            except Exception as err:
                raise TestCrawlerError(
                    'Error on testing a crawler "{}" for "{}"\n{}'.format(
                        registeredName,
                        pathHolder.path(),
                        str(err)
                    )
                )

            # creating crawler
            if passedTest:
                try:
                    result = testCrawlerType(pathHolder, parentCrawler)
                except Exception as err:
                    raise CreateCrawlerError(
                        'Error on creating a crawler "{}" for "{}"\n{}'.format(
                            registeredName,
                            pathHolder.path(),
                            str(err)
                        )
                    )
                else:
                    result.setVar('type', registeredName)
                break

        assert result, \
            "Don't know how to create a path crawler for \"{0}\"".format(
                pathHolder.path()
            )
        return result

    @staticmethod
    def createFromJson(jsonContents):
        """
        Create a crawler based on the jsonContents (serialized via toJson).
        """
        contents = json.loads(jsonContents)
        crawlerType = contents["vars"]["type"]
        filePath = contents["vars"]["filePath"]

        # creating crawler
        crawler = Path.__registeredTypes[crawlerType](
            PathHolder(filePath)
        )

        # setting vars
        for varName, varValue in contents["vars"].items():
            isContextVar = (varName in contents["contextVarNames"])
            crawler.setVar(varName, varValue, isContextVar)

        # setting tags
        for tagName, tagValue in contents["tags"].items():
            crawler.setTag(tagName, tagValue)

        return crawler

    @staticmethod
    def createFromPath(fullPath, crawlerType=None, parentCrawler=None):
        """
        Create a crawler directly from a path string.
        """
        if crawlerType:
            crawlerClass = Path.__registeredTypes.get(crawlerType)
            assert crawlerClass, "Invalid crawler type {} for {}".format(crawlerType, fullPath)

            result = crawlerClass(PathHolder(fullPath), parentCrawler)
            result.setVar('type', crawlerType)

            return result
        else:
            return Path.create(PathHolder(fullPath), parentCrawler)

    def __setPathHolder(self, pathHolder):
        """
        Set the path holder to the crawler.
        """
        assert isinstance(pathHolder, PathHolder), \
            "Invalid PathHolder type"

        self.__pathHolder = pathHolder

    @staticmethod
    def __collectCrawlers(crawler):
        """
        Resursively collect crawlers.
        """
        result = []
        result.append(crawler)

        if not crawler.isLeaf():
            for childCrawler in crawler.children():
                result += Path.__collectCrawlers(childCrawler)

        return result