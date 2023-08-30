from abc import ABC, abstractmethod
from pydantic import BaseModel, StrictStr, StrictInt, StrictFloat, StrictBool, validate_call
from pydantic.dataclasses import dataclass as pydantic_dataclass
from typing import Literal, List, Callable, Union, Dict, Optional, Iterable
import re
import pprint
import warnings
from contextlib import contextmanager

import logging

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


class RegistryAccessor:
    _current_registry = None

    @classmethod
    def set_current_registry(cls, registry):
        cls._current_registry = registry

    @classmethod
    def get_current_registry(cls):
        if cls._current_registry is None:
            raise ValueError("No registry has been set.")
        return cls._current_registry

@contextmanager
def use_registry(registry):
    RegistryAccessor.set_current_registry(registry)
    yield
    RegistryAccessor.set_current_registry(None)


def test_func():
    """this function is a test docstring"""
    return None

def listify_func(x):
    return x.split('\n')


class LanguageModel(BaseModel):
    name: StrictStr
    memory: List = []

    def __init__(self, name: StrictStr):
        super().__init__(name=name)
        self.memory = []
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


@pydantic_dataclass
class Prompt:
    template: StrictStr
    inputs: List[StrictStr] = None
    filled_prompt: Union[StrictStr, None] = None

    def __post_init__(self):
        self.inputs = re.findall(r'\{(.*?)\}', self.template)

    def fill(self, running_concepts: Dict[StrictStr, Concept]):
        try:
            format_dict = {e: running_concepts[e].get_value() for e in self.inputs}
        except KeyError as e:
            raise KeyError(f'Could not find the input {e} in available run concepts {running_concepts.keys()} in'
                           f'object {self} with __dict__ {self.__dict__}')
        self.filled_prompt = self.template.format(**format_dict)
        return self.filled_prompt

    def __repr__(self):
        return pprint.pformat(self.__dict__)



@pydantic_dataclass
class Concept:
    """
    A simple utility function that doubles the input value.

    Returns
    -------
    int or float
        Double the input value.

    Example
    -------
    # >>> utility_function(3)
    6
    """

    name: StrictStr
    type: Literal['identity', 'list'] = 'identity'
    choice: Literal['all', 'index', 'stringify', 'random'] = 'all'
    listify_func: Callable = listify_func
    string_content: Union[StrictStr, None] = None
    list_content: List[StrictStr] = None
    list_concepts: Optional[List['Concept']] = None
    inputted: bool = False
    level: int = 0

    def __post_init__(self):
        if self.string_content:
            self.inputted = True

    def get_value(self):
        """
        A simple utility function that doubles the input value.

        Returns
        -------
        int or float
            Double the input value.

        Example
        -------
        # >>> utility_function(3)
        6
        """
        if self.type == 'identity':
            if self.string_content:
                return self.string_content
            else:
                raise ValueError(f'no string value assigned to {self.__dict__}')
        else:
            # if list
            if self.choice == 'all':
                if self.list_content:
                    return self.list_content
                else:
                    raise ValueError(f'no list value assigned to {self.__dict__}')

    def assign_content(self, content):
        if self.type == 'identity':
            self.string_content = content
        elif self.type == 'list':
            self.list_content = self.listify_func(content)
            list_concepts = list()
            for index, val in enumerate(self.list_content):
                new_concept = Concept(name=f"{self.name}_{index}", type="identity", string_content=val)
                list_concepts.append(new_concept)
            self.list_concepts = list_concepts

    def iter_listed_concepts(self):
        if type != 'list':
            raise Exception('Concept not a list type')
        for each in self.list_concepts:
            yield each

    def __repr__(self):
        return pprint.pformat(self.__dict__)



@pydantic_dataclass
class ConceptRegistry:
    _initial_concepts: List[Concept]
    _concepts: Dict[StrictStr, Concept] = None

    def __post_init__(self):
        # Ensure that there are no duplicate concept names
        names = [concept.name for concept in self._initial_concepts]
        assert len(names) == len(set(names)), "Duplicate cencept names detected"
        self._concepts = {concept.name: concept for concept in self._initial_concepts}

    @property
    def concepts(self) -> Dict[StrictStr, Concept]:
        return self._concepts

    def update_concepts(self, concept: Concept):
        if concept.name in self.concepts and self.concepts[concept.name] is not concept:
            warnings.warn(f'Overwrite Warning: \n{self.concepts[concept.name]}\n\n Is being overwritten by:\n {concept}')
        self.concepts[concept.name] = concept

    # def __repr__(self):
    #     lines = ['ConceptRegistry:']
    #     for name, concept in self._concepts.items():
    #         lines.append(f"  - {name}:")
    #         lines.append(f"    String content: {concept.string_content}")
    #         lines.append(f"    List content: {concept.list_content}")
    #     return '\n'.join(lines)

    def __repr__(self):
        lines = ['ConceptRegistry:']

        # Sort the concepts by their level
        sorted_concepts = sorted(self._concepts.values(), key=lambda c: c.level)

        for concept in sorted_concepts:
            lines.append(f"  - {concept.name}:")
            for attr_name, attr_value in vars(concept).items():
                lines.append(f"    {attr_name.capitalize()}: {attr_value}")
        return '\n'.join(lines)


class Executable(BaseModel, ABC):
    memory: List = []

    @abstractmethod
    def run(self, callback: Optional = None) -> Concept:
        pass

    @classmethod
    def create(cls,*args, **kwargs):
        # Creates a single instance of Executable
        return cls(*args, **kwargs)

    @classmethod
    def create_iterable(cls, configs: List[Dict]):
        """
        Creates an iterable of Executable instances based on the list of configurations
        """
        return (cls(**config) for config in configs)


class ExecutableOrchestrator(BaseModel, ABC):
    # Iterator[Union[Executable, 'ExecutableOrchestrator']]
    components: Iterable[Union[Executable, 'ExecutableOrchestrator']]

    def __init__(self, components: Iterable[Union[Executable, 'ExecutableOrchestrator']] = None):
        super().__init__(components=components if components else [])

    @abstractmethod
    def _run(self, callback: Optional = None, level=0):
        pass


class ProbabilisticComponent(Executable):
    model: LanguageModel
    prompt: Prompt
    output_concept: Concept
    # the inputs names are specified in the template.
    # the inputs are always specified by strings. because they've already been created
    #

    def __init__(self, model, prompt, output_concept):
        super().__init__(model=model, prompt=prompt, output_concept=output_concept)

    # @validate_call
    def run(self, callback=None) -> Concept:
        concept_registry = RegistryAccessor.get_current_registry()
        LOGGER.debug(f'Running object: {self.__dict__}')

        self.prompt.fill(concept_registry.concepts)
        response = self.model.generate_response(self.prompt.filled_prompt)
        self.output_concept.assign_content(content=response)

        # TODO fix what is added to the memory
        self.memory.append(response)
        return self.output_concept


class SymbolicComponent(Executable):
    function: Callable
    # the function should return the same number of the number o the list of output concepts
    input_concept_names: List[StrictStr]
    output_concepts: List[Concept]

    def __init__(self, function, input_concepts, output_concepts):
        super().__init__(function=function, input_concepts=input_concepts, output_concepts=output_concepts)

    def run(self, callback=None) -> List[Concept]:
        concept_registry = RegistryAccessor.get_current_registry()
        LOGGER.debug(f'Running object: {self.__dict__}')
        input_concepts = {concept_registry.concepts[name] for name in self.input_concept_names}
        for output_string, output_concept in zip(self.function(input_concepts), self.output_concepts):
            output_concept.assign_content(output_string)
        return self.output_concepts




class Chain(ExecutableOrchestrator):
    def __init__(self, components: Iterable[Union[Executable, 'ExecutableOrchestrator']] = None):
        super().__init__(components)

    # @validate_call
    def _run(self, callback=None, level=0):
        concept_registry = RegistryAccessor.get_current_registry()
        LOGGER.debug(f'Running object: {self.__dict__}')

        for component in self.components:
            if isinstance(component, Executable):
                output_concept: Concept = component.run(callback)
                output_concept.level = level
                concept_registry.update_concepts(output_concept)
                level += 1
            elif isinstance(component, ExecutableOrchestrator):
                level = component._run(callback, level=level)

        return level

    def run(self, callback=None, level=0):
        self._run(callback, level)


class Threads(ExecutableOrchestrator):
    def __init__(self, components: Iterable[Union[Executable, 'ExecutableOrchestrator']] = None):
        super().__init__(components)

    # later add async
    # @validate_call
    def _run(self, callback=None, level=0):
        concept_registry = RegistryAccessor.get_current_registry()
        LOGGER.debug(f'Running object: {self.__dict__}')

        # TODO this will run asyncronously all together at some point
        level += 1
        outputted_concepts_list = list()
        for component in self.components:
            if isinstance(component, Executable):
                output_concept: Concept = component.run(callback)
                output_concept.level = level
                outputted_concepts_list.append(output_concept)

            elif isinstance(component, ExecutableOrchestrator):
                level = component._run(callback=callback, level=level)

        for concept in outputted_concepts_list:
            concept_registry.update_concepts(concept)

        return level
