from attrs import field, define
from typing import List, Optional

@define(kw_only=True)
class State:
    """
    State class which contains a 'label' and defines a 'default' and 'possible_states'
    """
    label: str = field()
    default: str = field()
    possible_states:Optional[List] = field(factory=list)

    def describe(self):
        return {
            "label": self.label,
            "type": self.__class__.__name__,
        }