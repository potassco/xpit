"""
Test cases for main application functionality.
"""

from io import StringIO

from explanation_directory_prototype.utils import logging
from explanation_directory_prototype.utils.logging import configure_logging, get_logger
from explanation_directory_prototype.utils.parser import get_parser


class TestMain:
    """
    Test cases for main application functionality.
    """

    # def test_logger(self) -> None:
    #     """
    #     Test the logger.
    #     """
    #     sio = StringIO()
    #     configure_logging(sio, logging.INFO, True, True)
    #     log = get_logger("main")
    #     log.info("test123")
    #     self.assertRegex(sio.getvalue(), "test123")
    
    def test_logger_with_caplog(self, caplog):
        log = get_logger("main")
        caplog.set_level(logging.INFO, logger="main")
        log.info("test123")
        assert "test123" in caplog.text

    def test_parser(self) -> None:
        """
        Test the parser.
        """
        parser = get_parser()
        ret = parser.parse_args(["--log", "info"])
        self.assertEqual(ret.log, logging.INFO)
