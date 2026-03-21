# Vulture whitelist - suppress false positives

# pytest hook parameter (required by pytest API signature)
pluginmanager  # noqa: F821

# Protocol parameter (required by type system, used by callers not definition)
base_repo_def  # noqa: F821

# pytest fixture dependency (consumed by name for side effects)
init_example_monorepo  # noqa: F821
