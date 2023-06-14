from dynaconf import Dynaconf, Validator

validators = {
    'broker.name': Validator(
        'broker.name',
        must_exist=True,
        condition=lambda v: isinstance(v, str),
    ),
    'broker.args': Validator(
        'broker.args',
        must_exist=True,
        condition=lambda v: isinstance(v, dict),
    ),
    'channel.agent.name': Validator(
        'channel.agent.name',
        must_exist=True,
        condition=lambda v: isinstance(v, str),
    ),
    'channel.agent.args': Validator(
        'channel.agent.args',
        must_exist=True,
        condition=lambda v: isinstance(v, dict),
    ),
    'channel.webhook.name': Validator(
        'channel.webhook.name',
        must_exist=True,
        condition=lambda v: isinstance(v, str),
    ),
    'channel.webhook.args': Validator(
        'channel.webhook.args',
        must_exist=True,
        condition=lambda v: isinstance(v, dict),
    ),
    'channel.uvicorn.args': Validator(
        'channel.uvicorn.args',
        must_exist=True,
        condition=lambda v: isinstance(v, dict),
    ),
    'policy.name': Validator(
        'policy.name',
        must_exist=True,
        condition=lambda v: isinstance(v, str),
    ),
    'policy.args': Validator(
        'policy.args',
        must_exist=True,
        condition=lambda v: isinstance(v, dict),
    ),
}

# Settings entrypoint, loads settings from environment variables.
settings = Dynaconf(
    envvar_prefix='AILINGBOT',
    load_dotenv=True,
)
