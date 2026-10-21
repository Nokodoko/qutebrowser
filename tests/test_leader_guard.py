"""Regression test for the Alt+Super+Space leader guard in ../config.py.

The leader toggles between passthrough (locked) and qutebrowser's own modes
(unlocked). It must be bound in every mode reachable while unlocked: insert is
auto-entered by clicking or loading into a text field, and before the fix the
leader was unbound there, so presses were swallowed until Esc.

Ctrl+Space is icarus's leader. A qutebrowser chain starting with it (there was
<Ctrl+Space>f) made Ctrl+Space a pending keychain while unlocked: icarus never
saw it, and the next leader press within input.partial_timeout was appended to
the chain and thrown away.

Run with the qutebrowser source build:
    QT_QPA_PLATFORM=offscreen ~/Programs/qutebrowser/.venv/bin/python -m pytest \
        ~/.config/qutebrowser/tests

The `bindings` fixture comes from conftest.py: config.py can only be loaded
once per process (objreg singletons), so all modules in this directory share
one session-scoped load.
"""

import pytest

from qutebrowser.config import config
from qutebrowser.keyinput import keyutils

LEADER = keyutils.KeySequence.parse('<Alt+Meta+Space>')
ICARUS_LEADER = keyutils.KeySequence.parse('<Ctrl+Space>')
UNLOCKED_MODES = ['normal', 'insert', 'caret']


def test_leader_unlocks_from_passthrough(bindings):
    from qutebrowser.config import configdata
    # The tiling build disengages into tile mode; stock has no such mode.
    if 'tabs.tiling.layout' in configdata.DATA:
        assert bindings('passthrough') == {LEADER: 'mode-enter tile'}
    else:
        assert bindings('passthrough') == {LEADER: 'mode-leave'}


@pytest.mark.parametrize('mode', ['tile', 'bitwise'])
def test_leader_locks_from_tile_modes(bindings, mode):
    """Tile modes are unlocked states too: the leader must not be swallowed."""
    from qutebrowser.config import configdata
    if 'tabs.tiling.layout' not in configdata.DATA:
        pytest.skip('stock build without tab tiling')
    assert bindings(mode).get(LEADER) == 'mode-enter passthrough'


@pytest.mark.parametrize('mode', UNLOCKED_MODES)
def test_leader_locks_from_unlocked_modes(bindings, mode):
    assert bindings(mode).get(LEADER) == 'mode-enter passthrough'


@pytest.mark.parametrize('mode', ['normal', 'insert', 'passthrough'])
def test_icarus_leader_never_starts_a_keychain(bindings, mode):
    chains = [str(key) for key in bindings(mode)
              if len(key) > 1 and key[0] == ICARUS_LEADER[0]]
    assert not chains


def test_state_survives_tab_switches_and_page_loads(bindings):
    assert config.val.tabs.mode_on_change == 'persist'
    assert config.val.input.mode_override is None
