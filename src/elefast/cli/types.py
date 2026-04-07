from argparse import _SubParsersAction, ArgumentParser
from typing import TypeAlias

ParentParser: TypeAlias = _SubParsersAction[ArgumentParser]
