from abc import ABC, abstractmethod
from pydantic import BaseModel, StrictStr, StrictInt, StrictFloat, StrictBool, validate_call
from pydantic.dataclasses import dataclass as pydantic_dataclass
from typing import Literal, List, Callable, Union, Dict, Optional
import re
import pprint
import warnings

import logging

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


@pydantic_dataclass
class Concept:
    name: StrictStr
    type: Literal['identity', 'list'] = 'identity'
    choice: Literal['all', 'index', 'stringify', 'random'] = 'all'
    listify_func: Callable = lambda x: x.split('\n')
    string_content: Union[StrictStr, None] = None
    list_content: List[StrictStr] = None
    inputted: bool = False
    level: int = 0

    def __post_init__(self):
        if self.string_content:
            self.inputted = True

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

    def __repr__(self):
        return pprint.pformat(self.__dict__)

@pydantic_dataclass
class Prompt:
    template: StrictStr
    output: Concept
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

    def assign_output_as_string(self, output: StrictStr):
        self.output.assign_string_content(string_content=output)

    def return_output_concept(self) -> Concept:
        return self.output

    def __repr__(self):
        return pprint.pformat(self.__dict__)

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
    #
    # def __repr__(self):
    #     return pprint.pformat(self.__dict__)

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
    def run(self, concept_registry: ConceptRegistry, callback: Optional = None) -> Concept:
        pass


class ExecutableOrchestrator(BaseModel, ABC):
    components: List[Union[Executable, 'ExecutableOrchestrator']]

    def __init__(self, components: List[Union[Executable, 'ExecutableOrchestrator']] = None):
        super().__init__(components=components if components else [])

    @abstractmethod
    def _run(self, concept_registry: ConceptRegistry, callback: Optional = None, level=0) -> ConceptRegistry:
        pass


class ProbabilisticComponent(Executable):
    model: LanguageModel
    prompt: Prompt

    def __init__(self, model, prompt):
        super().__init__(model=model, prompt=prompt)

    # @validate_call
    def run(self, concept_registry: ConceptRegistry, callback=None) -> Concept:
        LOGGER.debug(f'Running object: {self.__dict__}')

        self.prompt.fill(concept_registry.concepts)
        response = self.model.generate_response(self.prompt.filled_prompt)
        self.prompt.assign_output_as_string(response)

        # TODO fix what is added to the memory
        self.memory.append(response)
        return self.prompt.return_output_concept()


class Chain(ExecutableOrchestrator):
    def __init__(self, components: List[Union[Executable, ExecutableOrchestrator]] = None):
        super().__init__(components)

    # @validate_call
    def _run(self, concept_registry: ConceptRegistry, callback=None, level=0):
        LOGGER.debug(f'Running object: {self.__dict__}')

        for component in self.components:
            if isinstance(component, Executable):
                output_concept: Concept = component.run(concept_registry, callback)
                output_concept.level = level
                concept_registry.update_concepts(output_concept)
                level += 1
            elif isinstance(component, ExecutableOrchestrator):
                concept_registry, level = component._run(concept_registry, callback, level=level)

        return concept_registry, level

    def run(self, concept_registry: ConceptRegistry, callback=None, level=0):
        return self._run(concept_registry, callback, level)[0]


class Threads(ExecutableOrchestrator):
    def __init__(self, components: List[Union[Executable, ExecutableOrchestrator]] = None):
        super().__init__(components)

    # later add async
    # @validate_call
    def _run(self, concept_registry: ConceptRegistry, callback=None, level=0):
        LOGGER.debug(f'Running object: {self.__dict__}')

        # TODO this will run asyncronously all together at some point
        level += 1
        outputted_concepts_list = list()
        for component in self.components:
            if isinstance(component, Executable):
                output_concept: Concept = component.run(concept_registry, callback)
                output_concept.level = level
                outputted_concepts_list.append(output_concept)

            elif isinstance(component, ExecutableOrchestrator):
                concept_registry, level = component._run(concept_registry, callback, level=level)

        for concept in outputted_concepts_list:
            concept_registry.update_concepts(concept)

        return concept_registry, level
