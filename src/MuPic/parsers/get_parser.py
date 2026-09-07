from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

from lark import Lark


class _info(NamedTuple) :
    grammar : str
    start : str

_PARSERS = {
    'config' : _info('config.lark', 'mupic_config_file'),
    'position' : _info('position.lark', 'start'),
}

@lru_cache
def get_parser(name : str) -> Lark :

    if name not in _PARSERS :
        raise ValueError(f"Unknown parser: {name}")

    info = _PARSERS[name]

    grammar = Path(__file__).parent / info.grammar
    parser = Lark(grammar.read_text(), parser='lalr', debug=True, start=info.start, maybe_placeholders=True) #, strict=True)
    return parser
