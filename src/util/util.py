import json

def handle_unserializable(obj):
    # Directly return any natively serializable value
    # if isinstance(obj, (int, float, str, bool, type(None))):
    #     return obj

    # Handle function objects
    if callable(obj):
        return f"<function {obj.__name__}>"

    # Handle custom objects by serializing their attributes
    elif hasattr(obj, "__dict__"):
        return {key: handle_unserializable(value) for key, value in obj.__dict__.items()}

    # Handle objects that are not directly serializable to JSON
    else:
        return obj
        # raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def custom_repr(obj):
    return json.dumps(obj, default=handle_unserializable, sort_keys=True, indent=4, ensure_ascii=False)
