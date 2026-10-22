"""Regression test for the <Space> leader in ../config.py.

<Space> is the leader: a prefix only, never a command of its own in normal
mode, so every <Space>x chain stays reachable. <Space>r restarts, <Space>b
toggles the tab bar, <Space>t enters tile mode (tiling build only).

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


def K(key):
    return keyutils.KeySequence.parse(key)


def _tiling():
    from qutebrowser.config import configdata
    if 'tabs.tiling.layout' not in configdata.DATA:
        pytest.skip('stock build without tab tiling')


def test_leader_r_restarts(bindings):
    assert bindings('normal')[RESTART] == 'restart'


def test_leader_b_toggles_tabbar(bindings):
    assert bindings('normal')[TABBAR] == 'config-cycle tabs.show always never'


def test_leader_t_enters_tile_mode(bindings):
    _tiling()
    assert bindings('normal')[TILE] == 'mode-enter tile'
    tile = bindings('tile')
    assert tile[K('z')] == 'tile-layout toggle'
    assert tile[K('s3')] == 'tag 3'


def test_bitwise_mode_is_gone(bindings):
    _tiling()
    from qutebrowser.utils import usertypes
    assert 'bitwise' not in usertypes.KeyMode.__members__
    assert K('<Space>T') not in bindings('normal')
    assert bindings('tile')[K('T')] == 'cmd-set-text -s :tab-select'


def test_tile_hints_like_normal(bindings):
    """f/F/gi follow hints in tile exactly as in normal mode."""
    _tiling()
    normal, tile = bindings('normal'), bindings('tile')
    for key in ['f', 'F', 'gi']:
        assert tile[K(key)] == normal[K(key)], key


def test_engage_tile_round_trip(bindings):
    """Leader in passthrough -> tile; a -> passthrough; Esc -> normal.

    j/k walk the stack of tabs while <Up>/<Down> and u/d scroll the page,
    so moving around never needs to disengage fully.
    """
    _tiling()
    leader = keyutils.KeySequence.parse('<Alt+Meta+Space>')
    assert bindings('passthrough')[leader] == 'mode-enter tile'
    tile = bindings('tile')
    assert tile[keyutils.KeySequence.parse('a')] == 'mode-enter passthrough'
    assert tile[keyutils.KeySequence.parse('<Escape>')] == 'mode-leave'
    assert tile[keyutils.KeySequence.parse('j')] == 'tile-focus next'
    assert tile[keyutils.KeySequence.parse('k')] == 'tile-focus prev'
    assert tile[keyutils.KeySequence.parse('<Up>')] == 'scroll up'
    assert tile[keyutils.KeySequence.parse('<Down>')] == 'scroll down'
    # u/d are the normal-mode smooth scrolls, copied over.
    normal = bindings('normal')
    assert tile[K('u')] == normal[K('u')]
    assert tile[K('d')] == normal[K('d')]
    assert tile[keyutils.KeySequence.parse('D')] == 'tile-nmaster -1'
    # Tile is normal mode with tab navigation: page navigation lives there too.
    assert tile[keyutils.KeySequence.parse('gg')] == 'scroll-to-perc 0'
    assert tile[keyutils.KeySequence.parse('G')] == 'scroll-to-perc'
    assert tile[keyutils.KeySequence.parse('<PgDown>')] == 'scroll-page 0 1'
    assert tile[K('H')] == normal[K('H')]
    assert tile[K('L')] == normal[K('L')]
    assert tile[keyutils.KeySequence.parse('+')] == 'zoom-in'
    assert tile[keyutils.KeySequence.parse('-')] == 'zoom-out'
    assert tile[keyutils.KeySequence.parse('x')] == 'tab-close'
    # The <Space> leader chains work from tile too.
    assert tile[TABBAR] == 'config-cycle tabs.show always never'
    assert tile[RESTART] == 'restart'


TILE_OWN = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '<Tab>',
            '<Return>', '<Escape>', '<Up>', '<Down>', 'z', 'j', 'k', 'h', 'l',
            'I', 'D', 'r', 'a', 'x', 't']


def test_tile_carries_every_normal_binding(bindings):
    """Tile is normal mode plus tab keys: each normal binding is in tile.

    The only exceptions are tile's own keys, chains starting with one of
    them (they would be shadowed), and s (prefix of the s1..s9 chains).
    """
    _tiling()
    normal, tile = bindings('normal'), bindings('tile')
    own = {str(K(k)) for k in TILE_OWN}
    normal_singles = {str(k) for k in normal if len(k) == 1}
    missing = []
    for key, cmd in normal.items():
        first = str(key[:1])
        if str(key) in own or first in own:
            continue
        if len(key) > 1 and first in normal_singles:
            continue  # dead in normal mode already
        if str(key) == 's':
            continue
        if tile.get(key) != cmd:
            missing.append(str(key))
    assert missing == []


def test_tile_has_no_shadowed_chains(bindings):
    """No tile chain sits under a single key that is itself bound."""
    _tiling()
    tile = bindings('tile')
    singles = {str(k) for k in tile if len(k) == 1}
    shadowed = [str(k) for k in tile if len(k) > 1 and str(k[:1]) in singles]
    assert shadowed == []


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
