"""Shared fixture for the config.py regression tests.

Loading ../config.py requires a full qutebrowser init (standarddir +
configinit.early_init), and that registers singletons in objreg: doing it once
per test module fails with "Object 'config-commands' is already registered".
So the fixture lives here, at session scope, and every test module in this
directory shares the one loaded config.

Run with the qutebrowser source build:
    QT_QPA_PLATFORM=offscreen ~/Programs/qutebrowser/.venv/bin/python -m pytest \
        ~/.config/qutebrowser/tests
"""

import argparse
import os
import pathlib
import shutil

import pytest

from qutebrowser.config import config, configinit
from qutebrowser.qutebrowser import get_argparser
from qutebrowser.utils import standarddir

CONFIG_DIR = pathlib.Path(os.environ.get(
    'QB_CONFIG_DIR', pathlib.Path(__file__).resolve().parent.parent))


@pytest.fixture(scope='session')
def bindings(tmp_path_factory):
    """Load ../config.py into a throwaway basedir; return a bindings getter."""
    basedir = tmp_path_factory.mktemp('qb')
    shutil.copytree(CONFIG_DIR, basedir / 'config',
                    ignore=shutil.ignore_patterns('tests', '.git'))
    args = get_argparser().parse_args(['--basedir', str(basedir)])
    assert isinstance(args, argparse.Namespace)
    standarddir.init(args)
    configinit.early_init(args)
    assert configinit._init_errors is None, configinit._init_errors
    return config.key_instance.get_bindings_for
