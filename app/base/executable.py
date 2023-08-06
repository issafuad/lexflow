from abc import ABC, abstractmethod
from pydantic import BaseModel, StrictStr, StrictInt, StrictFloat, StrictBool, validate_call
from pydantic.dataclasses import dataclass as pydantic_dataclass
from typing import Literal, List, Callable, Union, Dict
import re

import logging

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


@pydantic_dataclass
class Placeholder:
    name: StrictStr
    type: Literal['identity', 'list'] = 'identity'
    choice: Literal['all', 'index', 'stringify', 'random'] = 'all'
    listify_func: Callable = lambda x: x.split('\n')
    string_content: Union[StrictStr, None] = None
    list_content: List[StrictStr] = None

    def get_value(self):
        if self.type == 'identity':
            if self.string_content:
                return self.string_content
            else:
                raise ValueError(f'no string value assigned to {self.__dict__}')
        else:
            if self.choice == 'all':
                if self.list_content:
                    return self.list_content
                else:
                    raise ValueError(f'no list value assigned to {self.__dict__}')

    def get_name(self) -> StrictStr:
        return self.name

    def assign_string_content(self, string_content):
        self.string_content = string_content

    def assign_list_content(self, list_content):
        self.list_content = list_content


@pydantic_dataclass
class Prompt:
    # TODO make inputs inferred from text
    # TOOD rename text to template
    template: StrictStr
    output: Placeholder
    inputs: List[StrictStr] = None
    filled_prompt: Union[StrictStr, None] = None

    def __post_init__(self):
        self.inputs = re.findall(r'\{(.*?)\}', self.template)

    def fill(self, running_placeholders: Dict[StrictStr, Placeholder]):
        try:
            format_dict = {e: running_placeholders[e].get_value() for e in self.inputs}
        except KeyError as e:
            raise KeyError(f'Could not find the input {e} in available run placeholders {running_placeholders.keys()} in'
                           f'object {self} with __dict__ {self.__dict__}')
        self.filled_prompt = self.template.format(**format_dict)
        return self.filled_prompt

    def assign_output_as_string(self, output: StrictStr):
        self.output.assign_string_content(string_content=output)

    def return_output(self) -> Placeholder:
        return self.output

    def return_output_name(self) -> StrictStr:
        return self.output.get_name()


class LanguageModel(BaseModel):
    name: StrictStr
    memory: List = []
    # didn't use a datacclass here as it complaind about a list as a default value. it wanted to have a factory method to set it to a list to avoid setting any instance of the class to teh same list.
    # this was an example where using dataclasses is not suitable for things that are not data structures

    @validate_call
    def generate_response(self, prompt_string: StrictStr) -> StrictStr:
        response = f"Response of {self.name}: to ({prompt_string})"
        self.memory.append((prompt_string, response))
        return response

    # add async later
    @validate_call
    def generate_response_async(self, prompt_string: StrictStr) -> StrictStr:
        return self.generate_response(prompt_string)


class Ex(ABC):
    @abstractmethod
    def __init__(self, components=None):
        self.components = components
        self.memory = []

    @abstractmethod
    def run(self, inputted_placeholders, callback=None):
        pass


class Comp(Ex):
    def __init__(self, model, prompt):
        super().__init__()
        # LOGGER.debug('initialising Compo')
        self.model = model
        self.prompt = prompt

    def run(self, running_placeholders: Dict[StrictStr, Placeholder], callback=None) -> Dict[StrictStr, Placeholder]:
        LOGGER.debug(f'Running object: {self.__dict__}')
        # running_placeholders = running_placeholders.copy()
        self.prompt.fill(running_placeholders)
        response = self.model.generate_response(self.prompt.filled_prompt)
        self.prompt.assign_output_as_string(response)
        output = self.prompt.return_output()
        output_name = self.prompt.return_output_name()

        # TODO fix what is added to the memory
        self.memory.append(response)
        return {output_name: output}


class Chai(Ex):
    def __init__(self, components=None):
        super().__init__(components)

    def run(self, running_placeholders: Dict[StrictStr, Placeholder], callback=None):
        LOGGER.debug(f'Running object: {self.__dict__}')
        for component in self.components:
            new_running_placeholder: Dict[StrictStr, Placeholder] = component.run(running_placeholders, callback)
            self.memory.append((new_running_placeholder))
            # TODO add warning of some are being overwritten
            running_placeholders.update(new_running_placeholder)
        return running_placeholders


class Thre(Ex):
    def __init__(self, components=None):
        super().__init__(components)

    # later add async
    def run(self, running_placeholders: Dict[StrictStr, Placeholder], callback=None):
        LOGGER.debug(f'Running object: {self.__dict__}')
        # TODO this will run asyncronously all together at some point
        outputted_dicts = dict()
        for component in self.components:
            new_running_placeholder: Dict[StrictStr, Placeholder] = component.run(running_placeholders, callback)
            self.memory.append((new_running_placeholder))
            outputted_dicts.update(new_running_placeholder)
        running_placeholders.update(outputted_dicts)
        return running_placeholders
