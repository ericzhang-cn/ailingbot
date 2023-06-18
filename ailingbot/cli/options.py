import typing

import click
import tomli


class TableParamType(click.ParamType):
    """Represents the type of table parameter, using TOML table format: {key=value,key=value,...,key=value}"""

    name = 'table'

    def convert(
        self,
        value: typing.Any,
        param: typing.Optional[click.Parameter],
        ctx: typing.Optional[click.Context],
    ) -> typing.Any:
        if value is None:
            return None
        if type(value) is dict:
            return value
        if type(value) is not str:
            raise ValueError('Type of value should be `str`.')

        value = f'value={value}'

        try:
            dict_ = tomli.loads(value)
            return dict_['value']
        except tomli.TOMLDecodeError:
            raise click.BadParameter('Value is not a valid TOML table value.')

    def __repr__(self) -> str:
        return 'Table'


env_var_prefix = 'AILINGBOT'

config_file_option = click.option(
    '-c',
    '--config-file',
    type=click.Path(),
    help='Configuration file path.',
)

broker_name_option = click.option(
    '--broker',
    type=click.STRING,
    help=f'Broker name or class(read from environment variable {env_var_prefix}_BROKER__NAME if is not passed into).',
    envvar=f'{env_var_prefix}_BROKER__NAME',
)

broker_args_option = click.option(
    '--broker-args',
    type=TableParamType(),
    help=f'Broker arguments(read from environment variable {env_var_prefix}_BROKER__ARGS if is not passed into).',
    envvar=f'{env_var_prefix}_BROKER__ARGS',
)

policy_name_option = click.option(
    '--policy',
    type=click.STRING,
    help=f'Policy name or class(read from environment variable {env_var_prefix}_POLICY__NAME if is not passed into).',
    envvar=f'{env_var_prefix}_POLICY__NAME',
)

policy_args_option = click.option(
    '--policy-args',
    type=TableParamType(),
    help=f'Policy arguments(read from environment variable {env_var_prefix}_POLICY__ARGS if is not passed into).',
    envvar=f'{env_var_prefix}_POLICY__ARGS',
)

channel_agent_name_option = click.option(
    '--channel-agent',
    type=click.STRING,
    help=f'Channel agent name or class(read from environment variable {env_var_prefix}_CHANNEL__AGENT__NAME if is not passed into).',
    envvar=f'{env_var_prefix}_CHANNEL__AGENT__NAME',
)

channel_agent_args_option = click.option(
    '--channel-agent-args',
    type=TableParamType(),
    help=f'Channel agent arguments(read from environment variable {env_var_prefix}_CHANNEL__AGENT__ARGS if is not passed into).',
    envvar=f'{env_var_prefix}_CHANNEL__AGENT__ARGS',
)

channel_webhook_name_option = click.option(
    '--channel-webhook',
    type=click.STRING,
    help=f'Channel webhook name or class(read from environment variable {env_var_prefix}_CHANNEL__WEBHOOK__NAME if is not passed into).',
    envvar=f'{env_var_prefix}_CHANNEL__WEBHOOK__NAME',
)

channel_webhook_args_option = click.option(
    '--channel-webhook-args',
    type=TableParamType(),
    help=f'Channel webhook arguments(read from environment variable {env_var_prefix}_CHANNEL__WEBHOOK__ARGS if is not passed into).',
    envvar=f'{env_var_prefix}_CHANNEL__WEBHOOK__ARGS',
)

channel_uvicorn_args_option = click.option(
    '--channel-uvicorn-args',
    type=TableParamType(),
    help=f'Channel uvicorn arguments(read from environment variable {env_var_prefix}_CHANNEL__UVICORN__ARGS if is not passed into).',
    envvar=f'{env_var_prefix}_CHANNEL__UVICORN__ARGS',
)

log_level_option = click.option(
    '--log-level',
    type=click.Choice(
        choices=[
            'TRACE',
            'DEBUG',
            'INFO',
            'SUCCESS',
            'WARNING',
            'ERROR',
            'CRITICAL',
        ],
        case_sensitive=False,
    ),
    help=f'The minimum severity level from which logged messages should be sent to(read from environment variable {env_var_prefix}_LOG__LEVEL if is not passed into).',
    envvar=f'{env_var_prefix}_LOG__LEVEL',
    default='TRACE',
    show_default=True,
)

log_file_option = click.option(
    '--log-file',
    type=click.STRING,
    help=f'STDOUT, STDERR, or file path(read from environment variable {env_var_prefix}_LOG__FILE if is not passed into).',
    envvar=f'{env_var_prefix}_LOG__FILE',
    default='STDERR',
    show_default=True,
)
