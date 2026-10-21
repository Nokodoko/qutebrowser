"""Regression test for the <Space> leader in ../config.py.

<Space> is the leader: a prefix only, never a command of its own in normal
mode, so every <Space>x chain stays reachable. <Space>r restarts, <Space>b
toggles the tab bar, <Space>t / <Space>T enter tile / bitwise mode (tiling
build only).

Space is bound to selection-toggle in CARET mode by default; that is a
different mode and is untouched, which is why the leader is a normal-mode
statement. <Shift+Space> (tab-select) is a separate key in the trie, not a
<Space> chain, so it survives too.

Run with the qutebrowser source build:
    QT_QPA_PLATFORM=offscreen ~/Programs/qutebrowser/.venv/bin/python -m pytest \
        ~/.config/qutebrowser/tests
"""

import pytest

from qutebrowser.keyinput import keyutils

LEADER = keyutils.KeySequence.parse('<Space>')
RESTART = keyutils.KeySequence.parse('<Space>r')
TABBAR = keyutils.KeySequence.parse('<Space>b')
TILE = keyutils.KeySequence.parse('<Space>t')
BITWISE = keyutils.KeySequence.parse('<Space>T')


def test_leader_r_restarts(bindings):
    assert bindings('normal')[RESTART] == 'restart'


def test_leader_b_toggles_tabbar(bindings):
    assert bindings('normal')[TABBAR] == 'config-cycle tabs.show always never'


def test_leader_t_enters_tile_modes(bindings):
    from qutebrowser.config import configdata
    if 'tabs.tiling.layout' not in configdata.DATA:
        pytest.skip('stock build without tab tiling')
    assert bindings('normal')[TILE] == 'mode-enter tile'
    assert bindings('normal')[BITWISE] == 'mode-enter bitwise'
    tile = bindings('tile')
    assert tile[keyutils.KeySequence.parse('f')] == 'tile-layout toggle'
    assert tile[keyutils.KeySequence.parse('s3')] == 'tag 3'
    assert bindings('bitwise')[keyutils.KeySequence.parse('<Return>')] == 'mode-enter tile'


def test_engage_tile_round_trip(bindings):
    """Leader in passthrough -> tile; a -> passthrough; Esc -> normal.

    j/k walk the stack of tabs while <Up>/<Down> and u/d scroll the page,
    so moving around never needs to disengage fully.
    """
    from qutebrowser.config import configdata
    if 'tabs.tiling.layout' not in configdata.DATA:
        pytest.skip('stock build without tab tiling')
    leader = keyutils.KeySequence.parse('<Alt+Meta+Space>')
    assert bindings('passthrough')[leader] == 'mode-enter tile'
    tile = bindings('tile')
    assert tile[keyutils.KeySequence.parse('a')] == 'mode-enter passthrough'
    assert tile[keyutils.KeySequence.parse('<Escape>')] == 'mode-leave'
    assert tile[keyutils.KeySequence.parse('j')] == 'tile-focus next'
    assert tile[keyutils.KeySequence.parse('k')] == 'tile-focus prev'
    assert tile[keyutils.KeySequence.parse('<Up>')] == 'scroll up'
    assert tile[keyutils.KeySequence.parse('<Down>')] == 'scroll down'
    assert tile[keyutils.KeySequence.parse('u')] == 'scroll-page 0 -0.5'
    assert tile[keyutils.KeySequence.parse('d')] == 'scroll-page 0 0.5'
    assert tile[keyutils.KeySequence.parse('D')] == 'tile-nmaster -1'
    # Tile is normal mode with tab navigation: page navigation lives there too.
    assert tile[keyutils.KeySequence.parse('gg')] == 'scroll-to-perc 0'
    assert tile[keyutils.KeySequence.parse('G')] == 'scroll-to-perc'
    assert tile[keyutils.KeySequence.parse('<PgDown>')] == 'scroll-page 0 1'
    assert tile[keyutils.KeySequence.parse('H')] == 'back'
    assert tile[keyutils.KeySequence.parse('L')] == 'forward'
    assert tile[keyutils.KeySequence.parse('+')] == 'zoom-in'
    assert tile[keyutils.KeySequence.parse('-')] == 'zoom-out'
    assert tile[keyutils.KeySequence.parse('x')] == 'tab-close'
    # The <Space> leader chains work from tile too.
    assert tile[TABBAR] == 'config-cycle tabs.show always never'
    assert tile[RESTART] == 'restart'


def test_t_enters_tile_and_shadows_nothing(bindings):
    """Plain t enters tile mode; every stock t-chain is gone so none is dead."""
    from qutebrowser.config import configdata
    if 'tabs.tiling.layout' not in configdata.DATA:
        pytest.skip('stock build without tab tiling')
    normal = bindings('normal')
    t = keyutils.KeySequence.parse('t')
    assert normal[t] == 'mode-enter tile'
    chains = [str(k) for k in normal if len(k) > 1 and k[0] == t[0]]
    assert chains == []


def test_leader_alone_is_a_prefix_not_a_command(bindings):
    # Bound to a command, <Space> would shadow every <Space>x chain.
    assert LEADER not in bindings('normal')


def test_leader_is_not_a_dead_prefix(bindings):
    """At least one <Space>x chain exists, so the leader does something."""
    chains = [str(k) for k in bindings('normal')
              if len(k) > 1 and k[0] == LEADER[0]]
    assert '<Space>r' in chains
    assert '<Space>b' in chains


def test_shift_space_still_bound(bindings):
    """A distinct key, not a <Space> chain: unaffected by the leader."""
    shift_space = keyutils.KeySequence.parse('<Shift+Space>')
    assert bindings('normal')[shift_space] == 'cmd-set-text -s :tab-select'


def test_caret_space_untouched(bindings):
    assert bindings('caret')[LEADER] == 'selection-toggle'
