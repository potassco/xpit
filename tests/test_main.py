"""
Test cases for main application functionality.
"""

from io import StringIO

import pytest
from explanation_director_prototype.utils.logging import configure_logging, get_logger
from explanation_director_prototype.utils.parser import get_parser

from explanation_director_prototype.utils import logging


class TestMain:
    """
    Test cases for main application functionality.
    """

    def test_logger(self) -> None:
        """
        Test the logger.
        """
        sio = StringIO()
        configure_logging(sio, logging.INFO, True, True)
        log = get_logger("main")
        log.info("test123")
        assert "test123" in sio.getvalue()

    def test_logger_with_caplog(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        Test the logger with caplog.
        """
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
        assert ret.log == logging.INFO
