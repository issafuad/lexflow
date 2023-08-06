from abc import ABC, abstractmethod

import logging

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


class Prompt:
    def __init__(self, text, placeholders, output):
        self.text = text
        self.placeholders = placeholders
        self.output = output
        self.filled_prompt = None

    def fill(self, placeholder_values):
        filled_text = self.text
        for placeholder in self.placeholders:
            value = placeholder_values[placeholder]
            filled_text = filled_text.format(**{placeholder: value})

        self.filled_prompt = filled_text
        return self.filled_prompt


class LanguageModel:
    def __init__(self, name):
        self.name = name
        self.memory = []

    def generate_response(self, prompt, callback):
        print(f'prompt: {prompt}')
        response = f"Response of {self.name}: to ({prompt})"
        self.memory.append((prompt, response))
        if callback is not None:
            callback(response)
        return response

    # add async later
    def generate_response_async(self, prompt, callback):
        return self.generate_response(prompt, callback)


class Ex(ABC):
    @abstractmethod
    def __init__(self, components=None):
        self.components = components
        self.memory = []

    @abstractmethod
    def run(self, inputted_placeholders, callback=None):
        pass

    @abstractmethod
    def _infer_initial_placeholders(self):
        pass

    @abstractmethod
    def validate_components(self):
        pass

    @abstractmethod
    def get_output_keys(self):
        pass

    def validate_initial_placeholders(self, inputted_placeholders):
        required_placeholders = self._infer_initial_placeholders()
        inputted_keys_set = set(inputted_placeholders.keys())
        required_keys_set = set(required_placeholders)

        # Check if all the elements in required_placeholders are present in inputted_placeholders.keys()
        if not required_keys_set.issubset(inputted_keys_set):
            missing_keys = required_keys_set - inputted_keys_set
            raise ValueError(
                f"The following required placeholders are missing: {list(missing_keys)}"
            )

        # Check for extra keys in inputted_placeholders that are not required
        extra_keys = inputted_keys_set - required_keys_set
        if extra_keys:
            LOGGER.warning(f"The following placeholders {list(extra_keys)} are provided but not required.")


class Comp(Ex):
    def __init__(self, model, prompt):
        super().__init__()
        LOGGER.debug('initialising Compo')
        self.model = model
        self.prompt = prompt

    def _infer_initial_placeholders(self):
        return self.prompt.placeholders

    def validate_components(self, available_placeholders=None):
        # A Component doesn't contain any subcomponents, so no validation is needed here
        # but we still define the method with the available_placeholders argument to ensure interface consistency
        pass

    def get_output_keys(self):
        return [self.prompt.output]

    def run(self, inputted_placeholders, callback=None):
        inputted_placeholders = inputted_placeholders.copy()
        self.prompt.fill(inputted_placeholders)
        response = self.model.generate_response(self.prompt.filled_prompt, callback)
        self.memory.append((self, response))
        return {self.prompt.output: response}


class Chai(Ex):
    def __init__(self, components=None):
        super().__init__(components)
        LOGGER.debug(f'initialising Chai with components {self.components}')
        # Validate components at instantiation
        self.validate_components()
        LOGGER.debug(f'Validated object Chai with components {self.components}')

    def _infer_initial_placeholders(self):
        return self.components[0]._infer_initial_placeholders()

    def get_output_keys(self):
        # This assumes you want the output key of the last component in the chain
        # You can change this logic if needed
        return self.components[-1].get_output_keys()

    def validate_components(self, available_placeholders=None):
        if not self.components:
            raise Exception('No components provided')

        if available_placeholders is None:
            available_placeholders = set(self._infer_initial_placeholders())

        LOGGER.debug(f'available placeholders for {self}: {available_placeholders}')
        for component in self.components:
            LOGGER.debug(f'going into component {component}')
            # Recursively validate the current component's subcomponents
            component.validate_components(available_placeholders)

            # Then validate its placeholders
            for placeholder in component._infer_initial_placeholders():
                if placeholder not in available_placeholders:
                    raise ValueError(
                        f"The placeholder '{placeholder}' is not provided in the initial placeholders "
                        f"or as an output from a previous component")

            # Once validated, add this component's output to available placeholders
            if hasattr(component, 'prompt'):
                available_placeholders.add(component.prompt.output)
        LOGGER.debug(f'succesfully validate {self}')

    def run(self, inputted_placeholders, callback=None):
        self.validate_initial_placeholders(inputted_placeholders)

        inputted_placeholders = inputted_placeholders.copy()
        responses = {}
        for component in self.components:
            response = component.run(inputted_placeholders, callback)

            # print(f'output keys {component.get_output_keys()}')
            for output_key in component.get_output_keys():
                inputted_placeholders[output_key] = response[output_key]
                self.memory.append((component, response))
        responses[output_key] = response[output_key]  # Added this line
        return responses


class Thre(Ex):
    def __init__(self, components=None):
        super().__init__(components)
        LOGGER.debug('initialising Thre')
        # Validate components at instantiation
        self.validate_components()

    def _infer_initial_placeholders(self):
        initial_placeholders = []
        for component in self.components:
            initial_placeholders.extend(component._infer_initial_placeholders())

        return list(set(initial_placeholders))  # remove duplicates

    def validate_components(self, available_placeholders=None):
        if not self.components:
            raise Exception('No components provided')

        if available_placeholders is None:
            available_placeholders = set(self._infer_initial_placeholders())

        LOGGER.debug(f'available placeholders for Thre: {available_placeholders}')
        for component in self.components:
            # Recursively validate the current component's subcomponents
            component.validate_components(available_placeholders.copy())

            # Then validate its placeholders
            for placeholder in component._infer_initial_placeholders():
                if placeholder not in available_placeholders:
                    raise ValueError(
                        f"The placeholder '{placeholder}' is not provided in the initial placeholders")

    def get_output_keys(self):
        # Fetch all output keys from all its components
        output_keys = []
        for component in self.components:
            output_keys.extend(component.get_output_keys())
        return list(set(output_keys))  # remove duplicates if any

    # later add async
    def run(self, inputted_placeholders, callback=None):
        self.validate_initial_placeholders(inputted_placeholders)

        inputted_placeholders = inputted_placeholders.copy()
        responses = {}
        for component in self.components:
            response = component.run(inputted_placeholders, callback)
            for output_key in component.get_output_keys():
                inputted_placeholders[output_key] = response[output_key]
                responses[output_key] = response[output_key]  # Added this line
                self.memory.append((component, response))
        return responses


# parsing output to list as callback