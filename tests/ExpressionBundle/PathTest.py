import unittest
from ..BaseTestCase import BaseTestCase
from ingestor.ExpressionEvaluator import ExpressionEvaluator
from ingestor.ExpressionEvaluator import ExpressionNotFoundError

class PathTest(BaseTestCase):
    """Test Path expressions."""

    __path = "/test/path/example.ext"

    def testDirname(self):
        """
        Test that the dirname expression works properly.
        """
        result = ExpressionEvaluator.run("dirname", self.__path)
        self.assertEqual(result, "/test/path")

    def testParentDirname(self):
        """
        Test that the parentdirname expression works properly.
        """
        result = ExpressionEvaluator.run("parentdirname", self.__path)
        self.assertEqual(result, "/test")

    def testBasename(self):
        """
        Test that the basename expression works properly.
        """
        result = ExpressionEvaluator.run("basename", self.__path)
        self.assertEqual(result, "example.ext")

    def testRegistration(self):
        """
        Test that the expression registration works properly.
        """
        self.assertRaises(ExpressionNotFoundError, ExpressionEvaluator.run, "dummy")
        ExpressionEvaluator.register("dummy", print)
        self.assertIn("dummy", ExpressionEvaluator.registeredNames())

    def testParseRun(self):
        """
        Test that running an expression through string parsing works.
        """
        result = ExpressionEvaluator.parseRun("dirname {}".format(self.__path))
        self.assertEqual(result, "/test/path")
        self.assertRaises(AssertionError, ExpressionEvaluator.parseRun, True)


if __name__ == "__main__":
    unittest.main()