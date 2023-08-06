# from abc import ABC, abstractmethod
#
# class Prompt:
#     def __init__(self, text, placeholders, output):
#         self.text = text
#         self.placeholders = placeholders
#         self.output = output
#
#     def fill(self, placeholder_values):
#         filled_text = self.text
#         for placeholder in self.placeholders:
#             value = placeholder_values[placeholder]
#             filled_text = filled_text.format(**{placeholder: value})
#
#         return filled_text
#
#
# class LanguageModel:
#     def __init__(self, name, provider):
#         self.name = name
#         self.provider = provider
#         self.memory = []
#
#     def generate_response(self, prompt, memory, callback):
#         print(f'prompt: {prompt}')
#         response = f"Response of {self.name}: to ({prompt})"
#         self.memory.append((prompt, response))
#         if callback is not None:
#             callback(response)
#         return response
#
#
# class Component:
#     def __init__(self, model, prompt):
#         self.model = model
#         self.prompt = prompt
#
#
# class Executable(ABC):
#     @property
#     def components(self):
#         """Subclasses must override this property and return a list of components."""
#         raise NotImplementedError
#
#     @abstractmethod
#     def run(self, initial_placeholders, callback=None):
#         pass
#
#     def infer_initial_placeholders(self):
#         # If there are no components, return an empty list
#         if not self.components:
#             return []
#
#         # Get the placeholders for the first component
#         initial_placeholders = self.components[0].prompt.placeholders
#         return initial_placeholders
#
#     def validate_components(self):
#         if self.components:
#             available_placeholders = set(self.infer_initial_placeholders())
#             for component in self.components:
#                 for placeholder in component.prompt.placeholders:
#                     if placeholder not in available_placeholders:
#                         raise ValueError(
#                             f"The placeholder '{placeholder}' is not provided in the initial placeholders or as an output from a previous component")
#                 # add this component's output to available placeholders
#                 available_placeholders.add(component.prompt.output)
#
#     def validate_initial_placeholders(self, initial_placeholders):
#         required_placeholders = self.infer_initial_placeholders()
#         if set(initial_placeholders.keys()) != set(required_placeholders):
#             raise ValueError("Provided initial placeholders do not match the required placeholders")
#
#
# class Chain(Executable):
#     def __init__(self, components=None):
#         self._components = components if components else []
#         self.memory = []
#         self.placeholders = {}
#
#         # Validate components at instantiation
#         if self._components:
#             self.validate_components()
#
#     @property
#     def components(self):
#         return self._components
#
#     @components.setter
#     def components(self, value):
#         self._components = value
#
#     def run(self, initial_placeholders, callback=None):
#         # Validate the initial placeholders before running
#         self.validate_initial_placeholders(initial_placeholders)
#
#         self.placeholders = initial_placeholders.copy()
#         response = None
#         for component in self.components:
#             filled_prompt = component.prompt.fill(self.placeholders)
#             response = component.model.generate_response(filled_prompt, self.memory, callback)
#             self.placeholders[component.prompt.output] = response
#             self.memory.append((filled_prompt, response))
#         return response
#
#
# # =========
# # other version
# from abc import ABC, abstractmethod
#
# class Prompt:
#     def __init__(self, text, placeholders, output):
#         self.text = text
#         self.placeholders = placeholders
#         self.output = output
#
#     def fill(self, placeholder_values):
#         filled_text = self.text
#         for placeholder in self.placeholders:
#             value = placeholder_values[placeholder]
#             filled_text = filled_text.format(**{placeholder: value})
#
#         return filled_text
#
#
# class LanguageModel:
#     def __init__(self, name, provider):
#         self.name = name
#         self.provider = provider
#         self.memory = []
#
#     def generate_response(self, prompt, memory, callback):
#         print(f'prompt: {prompt}')
#         response = f"Response of {self.name}: to ({prompt})"
#         self.memory.append((prompt, response))
#         if callback is not None:
#             callback(response)
#         return response
#
#
# class Component:
#     def __init__(self, model, prompt):
#         self.model = model
#         self.prompt = prompt
#
#
# class Executable(ABC):
#     @property
#     def components(self):
#         """Subclasses must override this property and return a list of components."""
#         raise NotImplementedError
#
#     @property
#     def memory(self):
#         """Subclasses must override this property and return a list of components."""
#         raise NotImplementedError
#
#     @property
#     def placeholders(self):
#         """Subclasses must override this property and return a list of components."""
#         raise NotImplementedError
#
#     @abstractmethod
#     def run(self, initial_placeholders, callback=None):
#         pass
#
#     def infer_initial_placeholders(self):
#         # If there are no components, return an empty list
#         if not self.components:
#             return []
#
#         # Get the placeholders for the first component
#         initial_placeholders = self.components[0].prompt.placeholders
#         return initial_placeholders
#
#     def validate_components(self):
#         if self.components:
#             available_placeholders = set(self.infer_initial_placeholders())
#             for component in self.components:
#                 for placeholder in component.prompt.placeholders:
#                     if placeholder not in available_placeholders:
#                         raise ValueError(
#                             f"The placeholder '{placeholder}' is not provided in the initial placeholders or as an output from a previous component")
#                 # add this component's output to available placeholders
#                 available_placeholders.add(component.prompt.output)
#
#     def validate_initial_placeholders(self, initial_placeholders):
#         required_placeholders = self.infer_initial_placeholders()
#         if set(initial_placeholders.keys()) != set(required_placeholders):
#             raise ValueError("Provided initial placeholders do not match the required placeholders")
#
#
# class Chain(Executable):
#     def __init__(self, components=None):
#         self._components = components if components else []
#         self.memory = []
#         self.placeholders = {}
#
#         # Validate components at instantiation
#         if self._components:
#             self.validate_components()
#
#     @property
#     def components(self):
#         return self._components
#
#     @components.setter
#     def components(self, value):
#         self._components = value
#
#     @property
#     def memory(self):
#         return self._memory
#
#     @memory.setter
#     def memory(self, value):
#         self._memory = value
#
#     @property
#     def placeholders(self):
#         return self._placeholders
#
#     @placeholders.setter
#     def placeholders(self, value):
#         self._placeholders = value
#
#     def run(self, initial_placeholders, callback=None):
#         # Validate the initial placeholders before running
#         self.validate_initial_placeholders(initial_placeholders)
#
#         self.placeholders = initial_placeholders.copy()
#         response = None
#         for component in self.components:
#             filled_prompt = component.prompt.fill(self.placeholders)
#             response = component.model.generate_response(filled_prompt, self.memory, callback)
#             self.placeholders[component.prompt.output] = response
#             self.memory.append((filled_prompt, response))
#         return response
#
#
# =====
# from abc import ABC, abstractmethod
# from pydantic import BaseModel, StrictStr, StrictInt, StrictFloat, StrictBool, validate_call
# from pydantic.dataclasses import dataclass as pydantic_dataclass
# from typing import Literal, List, Callable, Union, Dict
#
# import logging
#
# logging.basicConfig(level=logging.DEBUG)
# LOGGER = logging.getLogger(__name__)
#
#
# @pydantic_dataclass
# class Placeholder:
#     name: StrictStr
#     type: Literal['identity', 'list'] = 'identity'
#     choice: Literal['all', 'index', 'stringify', 'random'] = 'all'
#     listify_func: Callable = lambda x: x.split('\n')
#     string_content: Union[StrictStr, None] = None
#     list_content: List[StrictStr] = None
#
#     def get_value(self):
#         if self.type == 'identity':
#             if self.string_content:
#                 return self.string_content
#             else:
#                 raise ValueError(f'no string value assigned to {self.__dict__}')
#         else:
#             if self.choice == 'all':
#                 if self.list_content:
#                     return self.list_content
#                 else:
#                     raise ValueError(f'no list value assigned to {self.__dict__}')
#
#     def get_name(self) -> StrictStr:
#         return self.name
#
#     def assign_string_content(self, string_content):
#         self.string_content = string_content
#
#     def assign_list_content(self, list_content):
#         self.list_content = list_content
#
#
# @pydantic_dataclass
# class Prompt:
#     text: StrictStr
#     inputs: List[StrictStr]
#     output: Placeholder
#     filled_prompt: Union[StrictStr, None] = None
#
#     def fill(self, run_placeholders):
#         format_dict = {e: run_placeholders[e].get_value() for e in self.inputs}
#         self.filled_prompt = self.text.format(**format_dict)
#         return self.filled_prompt
#
#     def assign_output_as_string(self, output: StrictStr):
#         self.output.assign_string_content(string_content=output)
#
#     def return_output(self) -> Placeholder:
#         return self.output
#
#     def return_output_name(self) -> StrictStr:
#         return self.output.get_name()
#
#
# class LanguageModel(BaseModel):
#     name: StrictStr
#     memory: List = []
#
#     # didn't use a datacclass here as it complaind about a list as a default value. it wanted to have a factory method to set it to a list to avoid setting any instance of the class to teh same list.
#     # this was an example where using dataclasses is not suitable for things that are not data structures
#
#     @validate_call
#     def generate_response(self, prompt_string: StrictStr) -> StrictStr:
#         print(f'prompt: {prompt_string}')
#         response = f"Response of {self.name}: to ({prompt_string})"
#         self.memory.append((prompt_string, response))
#         return response
#
#     # add async later
#     @validate_call
#     def generate_response_async(self, prompt_string: StrictStr) -> StrictStr:
#         return self.generate_response(prompt_string)
#
#
# class Ex(ABC):
#     @abstractmethod
#     def __init__(self, components=None):
#         self.components = components
#         self.memory = []
#
#     @abstractmethod
#     def run(self, inputted_placeholders, callback=None):
#         pass
#
#     # @abstractmethod
#     # def _infer_initial_placeholders(self):
#     #     pass
#     #
#     # @abstractmethod
#     # def validate_components(self):
#     #     pass
#     #
#     # @abstractmethod
#     # def get_output_keys(self):
#     #     pass
#     #
#     # def validate_initial_placeholders(self, inputted_placeholders):
#     #     required_placeholders = self._infer_initial_placeholders()
#     #     inputted_keys_set = set(inputted_placeholders.keys())
#     #     required_keys_set = set(required_placeholders)
#     #
#     #     # Check if all the elements in required_placeholders are present in inputted_placeholders.keys()
#     #     if not required_keys_set.issubset(inputted_keys_set):
#     #         missing_keys = required_keys_set - inputted_keys_set
#     #         raise ValueError(
#     #             f"The following required placeholders are missing: {list(missing_keys)}"
#     #         )
#     #
#     #     # Check for extra keys in inputted_placeholders that are not required
#     #     extra_keys = inputted_keys_set - required_keys_set
#     #     if extra_keys:
#     #         LOGGER.warning(f"The following placeholders {list(extra_keys)} are provided but not required.")
#
#
# class Comp(Ex):
#     def __init__(self, model, prompt):
#         super().__init__()
#         LOGGER.debug('initialising Compo')
#         self.model = model
#         self.prompt = prompt
#
#     # def _infer_initial_placeholders(self):
#     #     return self.prompt.placeholders
#     #
#     # def validate_components(self, available_placeholders=None):
#     #     # A Component doesn't contain any subcomponents, so no validation is needed here
#     #     # but we still define the method with the available_placeholders argument to ensure interface consistency
#     #     pass
#     #
#     # def get_output_keys(self):
#     #     return [self.prompt.output]
#
#     def run(self, running_placeholders: Dict[StrictStr, Placeholder], callback=None):
#         running_placeholders = running_placeholders.copy()
#         self.prompt.fill(running_placeholders)
#         response = self.model.generate_response(self.prompt.filled_prompt)
#         self.prompt.assign_output_as_string(response)
#         output = self.prompt.return_output()
#         output_name = self.prompt.return_output_name()
#         running_placeholders.update({output_name: output})
#
#         # TODO fix what is added to the memory
#         self.memory.append((self, response))
#         return running_placeholders
#
#
# class Chai(Ex):
#     def __init__(self, components=None):
#         super().__init__(components)
#
#     #     LOGGER.debug(f'initialising Chai with components {self.components}')
#     #     # Validate components at instantiation
#     #     self.validate_components()
#     #     LOGGER.debug(f'Validated object Chai with components {self.components}')
#     #
#     # def _infer_initial_placeholders(self):
#     #     return self.components[0]._infer_initial_placeholders()
#     #
#     def get_output_keys(self):
#         # This assumes you want the output key of the last component in the chain
#         # You can change this logic if needed
#         return self.components[-1].get_output_keys()
#
#     #
#     # def validate_components(self, available_placeholders=None):
#     #     if not self.components:
#     #         raise Exception('No components provided')
#     #
#     #     if available_placeholders is None:
#     #         available_placeholders = set(self._infer_initial_placeholders())
#     #
#     #     LOGGER.debug(f'available placeholders for {self}: {available_placeholders}')
#     #     for component in self.components:
#     #         LOGGER.debug(f'going into component {component}')
#     #         # Recursively validate the current component's subcomponents
#     #         component.validate_components(available_placeholders)
#     #
#     #         # Then validate its placeholders
#     #         for placeholder in component._infer_initial_placeholders():
#     #             if placeholder not in available_placeholders:
#     #                 raise ValueError(
#     #                     f"The placeholder '{placeholder}' is not provided in the initial placeholders "
#     #                     f"or as an output from a previous component")
#     #
#     #         # Once validated, add this component's output to available placeholders
#     #         if hasattr(component, 'prompt'):
#     #             available_placeholders.add(component.prompt.output)
#     #     LOGGER.debug(f'succesfully validate {self}')
#
#     def run(self, name2placeholder_inputted, callback=None):
#         # self.validate_initial_placeholders(inputted_placeholders)
#
#         name2placeholder_inputted = name2placeholder_inputted.copy()
#         responses = {}
#         for component in self.components:
#             response = component.run(name2placeholder_inputted, callback)
#             # run the component
#             # go through all of the ouputted
#             for output_key in component.get_output_keys():
#                 name2placeholder_inputted[output_key] = response[output_key]
#                 self.memory.append((component, response))
#         responses[output_key] = response[output_key]  # Added this line
#
#         # the output of component is always a dict of a list of strings.
#         # the key of the dict is the name of the output in the prompt
#         return responses
#
#
# class Thre(Ex):
#     def __init__(self, components=None):
#         super().__init__(components)
#
#     #     LOGGER.debug('initialising Thre')
#     #     # Validate components at instantiation
#     #     self.validate_components()
#     #
#     # def _infer_initial_placeholders(self):
#     #     initial_placeholders = []
#     #     for component in self.components:
#     #         initial_placeholders.extend(component._infer_initial_placeholders())
#     #
#     #     return list(set(initial_placeholders))  # remove duplicates
#     #
#     # def validate_components(self, available_placeholders=None):
#     #     if not self.components:
#     #         raise Exception('No components provided')
#     #
#     #     if available_placeholders is None:
#     #         available_placeholders = set(self._infer_initial_placeholders())
#     #
#     #     LOGGER.debug(f'available placeholders for Thre: {available_placeholders}')
#     #     for component in self.components:
#     #         # Recursively validate the current component's subcomponents
#     #         component.validate_components(available_placeholders.copy())
#     #
#     #         # Then validate its placeholders
#     #         for placeholder in component._infer_initial_placeholders():
#     #             if placeholder not in available_placeholders:
#     #                 raise ValueError(
#     #                     f"The placeholder '{placeholder}' is not provided in the initial placeholders")
#     #
#     # def get_output_keys(self):
#     #     # Fetch all output keys from all its components
#     #     output_keys = []
#     #     for component in self.components:
#     #         output_keys.extend(component.get_output_keys())
#     #     return list(set(output_keys))  # remove duplicates if any
#
#     # later add async
#     def run(self, name2placeholder_inputted, callback=None):
#         self.validate_initial_placeholders(name2placeholder_inputted)
#
#         name2placeholder_inputted = name2placeholder_inputted.copy()
#         responses = {}
#         for component in self.components:
#             response = component.run(name2placeholder_inputted, callback)
#             for output_key in component.get_output_keys():
#                 name2placeholder_inputted[output_key] = response[output_key]
#                 responses[output_key] = response[output_key]  # Added this line
#                 self.memory.append((component, response))
#         return responses
#
# # parsing output to list as callback