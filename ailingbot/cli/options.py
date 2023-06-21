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
    help=f'The minimum severity level from which logged messages should be sent to(read from environment variable {env_var_prefix}_LOG_LEVEL if is not passed into).',
    envvar=f'{env_var_prefix}_LOG__LEVEL',
    default='TRACE',
    show_default=True,
)

log_file_option = click.option(
    '--log-file',
    type=click.STRING,
    help=f'STDOUT, STDERR, or file path(read from environment variable {env_var_prefix}_LOG_FILE if is not passed into).',
    envvar=f'{env_var_prefix}_LOG__FILE',
    default='STDERR',
    show_default=True,
)
