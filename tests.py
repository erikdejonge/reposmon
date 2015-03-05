# coding=utf-8
"""
unittester
erik@a8.nl (05-03-15)
license: GNU-GPL2
"""
from unittester import *
from reposmon import *


class ReposTestCase(unittest.TestCase):
    """
    @type unittest.TestCase: class
    @return: None
    """
    arguments = None

    def setUp(self):
        """
        setUp
        """
        self.myvar = "hello"

    def test_success(self):
        """
        test_assert_raises
        """
        self.assertIsNotNone(self.myvar)


def main():
    """
    main
    """
    unit_test_main(globals())


if __name__ == "__main__":
    main()
