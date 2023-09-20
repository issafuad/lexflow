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
#
# TODO seems to allow extra attributes with no errors. fix
# @pydantic_dataclass
# class Concept:
#     """
#     A simple utility function that doubles the input value.
#
#     Returns
#     -------
#     int or float
#         Double the input value.
#
#     Example
#     -------
#     # >>> utility_function(3)
#     6
#     """
#
#     name: StrictStr
#     content: Union[StrictStr, None] = None
#     inputted: bool = False
#     level: int = 0
#
#     def __post_init__(self):
#         if self.content:
#             self.inputted = True
#
#     def get_value(self):
#         """
#         A simple utility function that doubles the input value.
#
#         Returns
#         -------
#         int or float
#             Double the input value.
#
#         Example
#         -------
#         # >>> utility_function(3)
#         6
#         """
#         # if self.type == 'identity':
#         #     if self.content:
#         #         return self.content
#         #     else:
#         #         raise ValueError(f'no string value assigned to {self.__dict__}')
#         # else:
#         #     if list
#             # if self.choice == 'all':
#             #     if self.list_content:
#             #         return self.list_content
#             #     else:
#             #         raise ValueError(f'no list value assigned to {self.__dict__}')
#         return self.content
#
#     def assign_content(self, content):
#         # if self.type == 'identity':
#         #     self.content = content
#         # elif self.type == 'list':
#         #     self.list_content = self.listify_func(content)
#         #     list_concepts = list()
#         #     for index, val in enumerate(self.list_content):
#         #         new_concept = Concept(name=f"{self.name}_{index}", type="identity", string_content=val)
#         #         list_concepts.append(new_concept)
#         #     self.list_concepts = list_concepts
#         self.content = content
#
#     def iter_listed_concepts(self):
#         if self.type != 'list':
#             raise Exception(f'Concept {self} not a list type')
#         for each in self.list_concepts:
#             yield each
#
#     def __repr__(self):
#         import json
#
#         def handle_unserializable(obj):
#             # Directly return any natively serializable value
#             # if isinstance(obj, (int, float, str, bool, type(None))):
#             #     return obj
#
#             # Handle function objects
#             if callable(obj):
#                 return f"<function {obj.__name__}>"
#
#             # Handle custom objects by serializing their attributes
#             elif hasattr(obj, "__dict__"):
#                 return {key: handle_unserializable(value) for key, value in obj.__dict__.items()}
#
#             # Handle objects that are not directly serializable to JSON
#             else:
#                 return obj
#                 # raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
#
#         def custom_repr(obj):
#             return json.dumps(obj, default=handle_unserializable, sort_keys=True, indent=4, ensure_ascii=False)
#
#         return custom_repr(self.__dict__)
#         # return pprint.pformat(self.__dict__)
#

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
            # look into list concepts as well
        except KeyError as e:
            raise KeyError(f'Could not find the input {e} in available run concepts {running_concepts.keys()} in'
                           f'object {self} with __dict__ {self.__dict__}')
        self.filled_prompt = self.template.format(**format_dict)
        return self.filled_prompt

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

        for concept in self._concepts.values():
            _flatten_concept(concept)

        return flattened_concepts

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
        return custom_repr(self.__dict__)

    def __str__(self):
        self.__repr__()

    # def __repr__(self):
    #     lines = ['ConceptRegistry:']
    #
    #     # Sort the concepts by their level
    #     sorted_concepts = sorted(self._concepts.values(), key=lambda c: c.level)
    #
    #     for concept in sorted_concepts:
    #         lines.append(f"  - {concept.name}:")
    #         for attr_name, attr_value in vars(concept).items():
    #             lines.append(f"    {attr_name.capitalize()}: {attr_value}")
    #     return '\n'.join(lines)


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
