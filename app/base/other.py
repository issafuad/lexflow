from abc import ABC, abstractmethod

class Prompt:
    def __init__(self, text, placeholders, output):
        self.text = text
        self.placeholders = placeholders
        self.output = output

    def fill(self, placeholder_values):
        filled_text = self.text
        for placeholder in self.placeholders:
            value = placeholder_values[placeholder]
            filled_text = filled_text.format(**{placeholder: value})

        return filled_text


class LanguageModel:
    def __init__(self, name, provider):
        self.name = name
        self.provider = provider
        self.memory = []

    def generate_response(self, prompt, memory, callback):
        print(f'prompt: {prompt}')
        response = f"Response of {self.name}: to ({prompt})"
        self.memory.append((prompt, response))
        if callback is not None:
            callback(response)
        return response


class Component:
    def __init__(self, model, prompt):
        self.model = model
        self.prompt = prompt


class Executable(ABC):
    @property
    def components(self):
        """Subclasses must override this property and return a list of components."""
        raise NotImplementedError

    @abstractmethod
    def run(self, initial_placeholders, callback=None):
        pass

    def infer_initial_placeholders(self):
        # If there are no components, return an empty list
        if not self.components:
            return []

        # Get the placeholders for the first component
        initial_placeholders = self.components[0].prompt.placeholders
        return initial_placeholders

    def validate_components(self):
        if self.components:
            available_placeholders = set(self.infer_initial_placeholders())
            for component in self.components:
                for placeholder in component.prompt.placeholders:
                    if placeholder not in available_placeholders:
                        raise ValueError(
                            f"The placeholder '{placeholder}' is not provided in the initial placeholders or as an output from a previous component")
                # add this component's output to available placeholders
                available_placeholders.add(component.prompt.output)

    def validate_initial_placeholders(self, initial_placeholders):
        required_placeholders = self.infer_initial_placeholders()
        if set(initial_placeholders.keys()) != set(required_placeholders):
            raise ValueError("Provided initial placeholders do not match the required placeholders")


class Chain(Executable):
    def __init__(self, components=None):
        self._components = components if components else []
        self.memory = []
        self.placeholders = {}

        # Validate components at instantiation
        if self._components:
            self.validate_components()

    @property
    def components(self):
        return self._components

    @components.setter
    def components(self, value):
        self._components = value

    def run(self, initial_placeholders, callback=None):
        # Validate the initial placeholders before running
        self.validate_initial_placeholders(initial_placeholders)

        self.placeholders = initial_placeholders.copy()
        response = None
        for component in self.components:
            filled_prompt = component.prompt.fill(self.placeholders)
            response = component.model.generate_response(filled_prompt, self.memory, callback)
            self.placeholders[component.prompt.output] = response
            self.memory.append((filled_prompt, response))
        return response


# =========
# other version
from abc import ABC, abstractmethod

class Prompt:
    def __init__(self, text, placeholders, output):
        self.text = text
        self.placeholders = placeholders
        self.output = output

    def fill(self, placeholder_values):
        filled_text = self.text
        for placeholder in self.placeholders:
            value = placeholder_values[placeholder]
            filled_text = filled_text.format(**{placeholder: value})

        return filled_text


class LanguageModel:
    def __init__(self, name, provider):
        self.name = name
        self.provider = provider
        self.memory = []

    def generate_response(self, prompt, memory, callback):
        print(f'prompt: {prompt}')
        response = f"Response of {self.name}: to ({prompt})"
        self.memory.append((prompt, response))
        if callback is not None:
            callback(response)
        return response


class Component:
    def __init__(self, model, prompt):
        self.model = model
        self.prompt = prompt


class Executable(ABC):
    @property
    def components(self):
        """Subclasses must override this property and return a list of components."""
        raise NotImplementedError

    @property
    def memory(self):
        """Subclasses must override this property and return a list of components."""
        raise NotImplementedError

    @property
    def placeholders(self):
        """Subclasses must override this property and return a list of components."""
        raise NotImplementedError

    @abstractmethod
    def run(self, initial_placeholders, callback=None):
        pass

    def infer_initial_placeholders(self):
        # If there are no components, return an empty list
        if not self.components:
            return []

        # Get the placeholders for the first component
        initial_placeholders = self.components[0].prompt.placeholders
        return initial_placeholders

    def validate_components(self):
        if self.components:
            available_placeholders = set(self.infer_initial_placeholders())
            for component in self.components:
                for placeholder in component.prompt.placeholders:
                    if placeholder not in available_placeholders:
                        raise ValueError(
                            f"The placeholder '{placeholder}' is not provided in the initial placeholders or as an output from a previous component")
                # add this component's output to available placeholders
                available_placeholders.add(component.prompt.output)

    def validate_initial_placeholders(self, initial_placeholders):
        required_placeholders = self.infer_initial_placeholders()
        if set(initial_placeholders.keys()) != set(required_placeholders):
            raise ValueError("Provided initial placeholders do not match the required placeholders")


class Chain(Executable):
    def __init__(self, components=None):
        self._components = components if components else []
        self.memory = []
        self.placeholders = {}

        # Validate components at instantiation
        if self._components:
            self.validate_components()

    @property
    def components(self):
        return self._components

    @components.setter
    def components(self, value):
        self._components = value

    @property
    def memory(self):
        return self._memory

    @memory.setter
    def memory(self, value):
        self._memory = value

    @property
    def placeholders(self):
        return self._placeholders

    @placeholders.setter
    def placeholders(self, value):
        self._placeholders = value

    def run(self, initial_placeholders, callback=None):
        # Validate the initial placeholders before running
        self.validate_initial_placeholders(initial_placeholders)

        self.placeholders = initial_placeholders.copy()
        response = None
        for component in self.components:
            filled_prompt = component.prompt.fill(self.placeholders)
            response = component.model.generate_response(filled_prompt, self.memory, callback)
            self.placeholders[component.prompt.output] = response
            self.memory.append((filled_prompt, response))
        return response

