import os

# Map of built-in module names to their package paths.
BUILTIN_MODULES = {
    "registration_printing": os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "registration_printing",
    ),
}
