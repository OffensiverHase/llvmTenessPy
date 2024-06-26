from Context import Context
from Token import Position


class Error(Exception):
    """Base class for all the Heiabubu errors, subclass of Exception, so that it can be raised"""
    def __init__(self, name: str, details: str, pos: Position | None, context: Context, stage: str):
        self.name = name
        self.details = details
        self.pos = pos
        self.context = context
        self.stage = stage

    def __str__(self):
        if self.pos:
            return f'{self.name}: {self.details}, file {self.context.file}, line {self.pos.line + 1}, pos {self.pos.column}'
        else:
            return f'{self.name}: {self.details}, file {self.context.file}'


class IllegalCharError(Error):
    def __init__(self, details: str, pos: Position, context: Context, stage: str):
        super().__init__("Illegal Character", details, pos, context, stage)


class InvalidSyntaxError(Error):
    def __init__(self, details: str, pos: Position, context: Context, stage: str):
        super().__init__("Invalid Syntax", details, pos, context, stage)


class UnknownNodeError(Error):
    def __init__(self, details: str, pos: Position, context: Context, stage: str):
        super().__init__("Unknown Node", details, pos, context, stage)


class NoSuchVarError(Error):
    def __init__(self, details: str, pos: Position, context: Context, stage: str):
        super().__init__("No such Variable", details, pos, context, stage)


class TypeError(Error):
    def __init__(self, details: str, pos: Position, context: Context, stage: str):
        super().__init__("Type Error", details, pos, context, stage)


class RuntimeError(Error):
    def __init__(self, details: str, pos: Position, context: Context, stage: str):
        super().__init__("Runtime Exception", details, pos, context, stage)

class DuplicateNameError(Error):
    def __init__(self, details: str, pos: Position, context: Context, stage: str):
        super().__init__("Duplicate Name Error", details, pos, context, stage)


class IndexError(Error):
    def __init__(self, details: str, pos: Position, context: Context, stage: str):
        super().__init__("Invalid index Error", details, pos, context, stage)