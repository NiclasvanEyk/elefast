from argparse import ArgumentParser, _SubParsersAction
from typing import TypeAlias

ParentParser: TypeAlias = _SubParsersAction[ArgumentParser]
