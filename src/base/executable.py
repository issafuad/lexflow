from abc import ABC, abstractmethod
from pydantic import BaseModel, StrictStr, StrictInt, StrictFloat, StrictBool, validate_call, model_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass
from typing import Literal, List, Callable, Union, Dict, Optional, Iterable
import re
import pprint
import warnings
from contextlib import contextmanager
import logging

from src.util.util import custom_repr

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


class Concept(BaseModel):
    name: StrictStr
    content: Union[StrictStr, None] = None
    inputted: bool = False
    level: int = 0

    # put name here explicitly so that concept can take the first positional arugment as the name
    def __init__(self, name: StrictStr, **data):
        super().__init__(name=name, **data)

        # Setting `inputted` based on `content`
        if self.content:
            self.inputted = True

    def get_value(self):
        return self.content

    def assign_content(self, content):
        self.content = content

    # In Python, the __str__ method is used to define a human-readable representation of an object, which is returned by the built-in str() function and is used by built-in functions like print(). On the other hand, the __repr__ method returns the "official" string representation of an object, which ideally is an expression that would recreate the same object if passed to eval().
    def __str__(self):
        return custom_repr(self)

    def __repr__(self):
        return self.__str__()


class Prompt(BaseModel):
    template: StrictStr
    inputs: List[StrictStr] = None
    filled_prompt: Union[StrictStr, None] = None

    def __init__(self, template: StrictStr, **data):
        super().__init__(template=template, **data)
        self.inputs = re.findall(r'\{(.*?)\}', self.template)

    def fill(self, running_concepts: Dict[StrictStr, Concept]):
        try:
            format_dict = {e: running_concepts[e].get_value() for e in self.inputs}
            # look into list concepts as well
        except KeyError as e:
            raise KeyError(f'Could not find the input {e} in available run concepts {running_concepts.keys()} in'
                           f'object {self} with __dict__ {self.__dict__}')
        self.filled_prompt = self.template.format(**format_dict)
        return self.filled_prompt

    def __repr__(self):
        return pprint.pformat(self.__dict__)


class ConceptRegistry(BaseModel):
    initial_concepts: List[Concept]
    concepts: Dict[StrictStr, Concept] = None

    def __init__(self, initial_concepts: List[Concept], **data):
        super().__init__(initial_concepts=initial_concepts, **data)
        names = [concept.name for concept in self.initial_concepts]
        assert len(names) == len(set(names)), "Duplicate concept names detected"
        self.concepts = {concept.name: concept for concept in self.initial_concepts}

    @property
    def concepts(self) -> Dict[StrictStr, Concept]:
        return self.concepts

    @property
    def concepts_flattened(self) -> Dict[StrictStr, Concept]:
        flattened_concepts = {}

        def _flatten_concept(concept: Concept):
            if concept.name in flattened_concepts:
                return
            flattened_concepts[concept.name] = concept
            if concept.list_concepts:
                for sub_concept in concept.list_concepts:
                    _flatten_concept(sub_concept)

        for concept in self.concepts.values():
            _flatten_concept(concept)

        return flattened_concepts

    def update_concepts(self, concept: Concept):
        if concept.name in self.concepts and self.concepts[concept.name] is not concept:
            warnings.warn(f'Overwrite Warning: \n{self.concepts[concept.name]}\n\n Is being overwritten by:\n {concept}')
        self.concepts[concept.name] = concept

    def __repr__(self):
        return custom_repr(self.__dict__)

    def __str__(self):
        self.__repr__()


class Executable(BaseModel, ABC):
    memory: List = []

    @abstractmethod
    def run(self, callback: Optional = None) -> List[Concept]:
        pass


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
    # input_concepts:
    output_concept_name: StrictStr
    # the inputs names are specified in the template.
    # the inputs are always specified by strings. because they've already been created

    @classmethod
    def create_iterable_from_concept(cls, concept_name: StrictStr, language_model: LanguageModel, prompt: Prompt, output: Concept):
        concept_registry = RegistryAccessor.get_current_registry()
        concept = concept_registry.concepts[concept_name]
        if concept.type != 'list':
            raise Exception(
                f'You need to feed in a concept of type list. Current concept {concept_name} is of type {concept.type}')
        if output.type != 'list':
            raise Exception(f'Output concept needs to be of type list.')

        import re

        def replace_with_suffix(s, suffix="_1"):
            return re.sub(r'\{(.*?)\}', lambda m: '{' + m.group(1) + suffix + '}', s)

        print(concept_name)
        print(concept)
        output.list_concepts = list()
        for index, sub_concept in enumerate(concept.iter_listed_concepts()):
            sub_output = Concept(name=f"{output.name}_{index}", type="identity", string_content=None)
            output.list_concepts.append(sub_output)
            yield cls(model=language_model, prompt=Prompt(replace_with_suffix(prompt.template, suffix=f'_{index}')), output_concept_name=sub_output)

    def __init__(self, model, prompt, output_concept_name):
        super().__init__(model=model, prompt=prompt, output_concept_name=output_concept_name)

    # @validate_call
    def run(self, callback=None) -> List[Concept]:
        concept_registry = RegistryAccessor.get_current_registry()
        LOGGER.debug(f'Running object: {self.__dict__}')

        self.prompt.fill(concept_registry.concepts)
        response = self.model.generate_response(self.prompt.filled_prompt)
        output_concept = Concept(self.output_concept_name)
        output_concept.assign_content(content=response)

        # TODO fix what is added to the memory
        self.memory.append(response)
        return [output_concept]


class SymbolicComponent(Executable):
    function: Callable
    # the function should return the same number of the number o the list of output concepts
    input_concept_names: List[StrictStr]
    output_concept_names: List[StrictStr]

    def __init__(self, function, input_concept_names, output_concept_names):
        super().__init__(function=function, input_concept_names=input_concept_names, output_concept_names=output_concept_names)

    def run(self, callback=None) -> List[Concept]:
        concept_registry = RegistryAccessor.get_current_registry()
        LOGGER.debug(f'Running object: {self.__dict__}')
        print(self.input_concept_names)
        print(concept_registry.concepts)
        input_concepts = {name: concept_registry.concepts[name] for name in self.input_concept_names}
        output_concepts = list()
        for output_string, output_concept_name in zip(self.function(input_concepts), self.output_concept_names):
            output_concept = Concept(output_concept_name)
            output_concept.assign_content(output_string)
            output_concepts.append(output_concept)
        return output_concepts


class Chain(ExecutableOrchestrator):
    def __init__(self, components: Iterable[Union[Executable, 'ExecutableOrchestrator']] = None):
        super().__init__(components)

    # @validate_call
    def _run(self, callback=None, level=0):
        concept_registry = RegistryAccessor.get_current_registry()
        LOGGER.debug(f'Running object: {self.__dict__}')

        for component in self.components:
            if isinstance(component, Executable):
                output_concept_list: List[Concept] = component.run(callback)
                for output_concept in output_concept_list:
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
                output_concept_list: List[Concept] = component.run(callback)
                for output_concept in output_concept_list:
                    output_concept.level = level
                    outputted_concepts_list.append(output_concept)

            elif isinstance(component, ExecutableOrchestrator):
                level = component._run(callback=callback, level=level)

        for concept in outputted_concepts_list:
            concept_registry.update_concepts(concept)

        return level
