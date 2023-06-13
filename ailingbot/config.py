from dynaconf import Dynaconf

# Settings entrypoint, loads settings from environment variables.
settings = Dynaconf(
    envvar_prefix='AILINGBOT',
    load_dotenv=True,
)
