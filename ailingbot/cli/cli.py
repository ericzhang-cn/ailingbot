from __future__ import annotations

import asyncio
import os.path
import sys
import typing
import uuid
from functools import wraps

import click
import emoji
import tomlkit
import uvicorn
from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from rich.console import Console

import ailingbot.shared.errors
from ailingbot.channels.channel import ChannelAgent, ChannelWebhookFactory
from ailingbot.chat.chatbot import ChatBot, BotRunMode
from ailingbot.chat.messages import (
    TextRequestMessage,
    FallbackResponseMessage,
    OptionsResponseMessage,
    InputRequestMessage,
    InputResponseMessage,
    MessageScope,
)
from ailingbot.cli import options
from ailingbot.cli.render import render, display_radio_prompt
from ailingbot.config import settings


def _coro_cmd(f: typing.Callable) -> typing.Callable:
    """Decorator that wraps an async command to run with asyncio.

    :param f: Async function.
    :type f: typing.Callable
    :return: Wrapped function.
    :rtype: typing.Callable
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def _set_logger(*, sink: str, level: str) -> None:
    """Set logger sink and level.

    :param sink:
    :type sink:
    :param level:
    :type level:
    :return:
    :rtype:
    """
    logger.remove()

    if sink.lower() == 'stderr':
        logger.add(sys.stderr, level=level.upper())
    elif sink.lower() == 'stdout':
        logger.add(sys.stdout, level=level.upper())
    else:
        logger.add(sink, level=level.upper())


@click.group(name='cli', help='AilingBot command line tools.')
def command_line_tools():
    """AilingBot command line tools."""
    pass


@command_line_tools.group(name='bot', help='Bot commands.')
def bot_group():
    """Bot commands."""
    pass


@bot_group.command(
    name='serve', help='Run chatbot task(s) to serve request messages.'
)
@click.option(
    '-n',
    '--number-of-tasks',
    default=1,
    show_default=True,
    type=click.IntRange(min=1),
    help='Number of concurrently executed tasks.',
)
@click.option('--debug', is_flag=True, help='Enable debug mode.')
@options.log_level_option
@options.log_file_option
def bot_serve(
    number_of_tasks: int,
    debug: bool,
    log_level: str,
    log_file: str,
):
    """Run chatbot task(s) to serve request messages.

    :param number_of_tasks: Number of concurrently executed tasks.
    :type number_of_tasks: int
    :param debug: Whether to enable debug mode.
    :type debug: bool
    :param log_level:
    :type log_level:
    :param log_file:
    :type log_file:
    """
    _set_logger(sink=log_file, level=log_level)

    chatbot = ChatBot(
        num_of_tasks=number_of_tasks,
        run_mode=BotRunMode.Broker,
        debug=debug,
    )

    try:
        chatbot.run()
    except ailingbot.shared.errors.AilingBotError as e:
        raise click.ClickException(e.reason)


@bot_group.command(
    name='chat', help='Start an interactive bot conversation environment.'
)
@click.option('--debug', is_flag=True, help='Enable debug mode.')
@_coro_cmd
async def bot_chat(
    debug: bool,
):
    """Start an interactive bot conversation environment.

    :param debug: Whether to enable debug mode.
    :type debug: bool
    """
    chatbot = ChatBot(
        run_mode=BotRunMode.Standalone,
        debug=debug,
    )
    try:
        await chatbot.startup()
    except ailingbot.shared.errors.AilingBotError as e:
        raise click.ClickException(e.reason)

    conversation_id = str(uuid.uuid4())

    click.echo(
        click.style(
            text='Start a conversation with bot, type `exit` to quit',
            fg='blue',
        )
    )
    click.echo(
        click.style(
            text=f'{emoji.emojize(":light_bulb:")} Policy: {settings.policy.name}',
            fg='cyan',
        )
    )

    session = PromptSession()
    request = None
    while True:
        # Default path: no more request to send, start a new conversation round.
        if request is None:
            input_ = await session.prompt_async(
                FormattedText([('skyblue', '> Input: ')])
            )
            if input_ == '':
                continue
            if input_ == 'exit':
                break
            request = TextRequestMessage(
                text=input_,
                scope=MessageScope.USER,
            )

        # Sends request and processes different types response.
        try:
            response = await chatbot.respond(
                conversation_id=conversation_id, message=request
            )
            request = None
            if isinstance(response, OptionsResponseMessage):
                selected_value = await render(response)
                if selected_value is None:
                    continue
                request = InputRequestMessage(
                    value=selected_value,
                )
            elif isinstance(response, InputResponseMessage):
                text = await render(response)
                if text is None:
                    continue
                request = InputRequestMessage(
                    value=text,
                )
            else:
                await render(response)
        except ailingbot.shared.errors.AilingBotError as e:
            if e.critical:
                raise click.exceptions.ClickException(e.reason)
            else:
                request = None

                response = FallbackResponseMessage(
                    reason=e.reason, suggestion=e.suggestion
                )
                await render(response)


@command_line_tools.group(name='channel', help='Channel commands.')
def channel_group():
    """Channel commands."""
    pass


@channel_group.command(
    name='serve_agent',
    help='Run channel agent task(s) to serve response messages.',
)
@click.option(
    '-n',
    '--number-of-tasks',
    default=1,
    show_default=True,
    type=click.IntRange(min=1),
    help='Number of concurrently executed tasks.',
)
@options.log_level_option
@options.log_file_option
def channel_serve_agent(
    number_of_tasks: int,
    log_level: str,
    log_file: str,
):
    """Run channel agent task(s) to serve response messages.

    :param number_of_tasks: Number of concurrently executed tasks.
    :type number_of_tasks: int
    :param log_level:
    :type log_level:
    :param log_file:
    :type log_file:
    """
    _set_logger(sink=log_file, level=log_level)

    agent = ChannelAgent.get_agent(
        settings.channel.name,
        num_of_tasks=number_of_tasks,
    )
    try:
        agent.run()
    except ailingbot.shared.errors.AilingBotError as e:
        raise click.ClickException(e.reason)


@channel_group.command(
    name='serve_webhook', help='Run webhook server to receive events.'
)
@options.log_level_option
@options.log_file_option
@_coro_cmd
async def channel_serve_webhook(
    log_level: str,
    log_file: str,
):
    _set_logger(sink=log_file, level=log_level)

    webhook = await ChannelWebhookFactory.get_webhook(settings.channel.name)

    config = uvicorn.Config(app=webhook, **settings.uvicorn)
    server = uvicorn.Server(config)
    await server.serve()


@command_line_tools.group(name='config', help='Configuration commands.')
def config_group():
    """Configuration commands."""
    pass


@config_group.command(
    name='show', help='Show current configuration information.'
)
@click.option(
    '-k',
    '--config-key',
    type=click.STRING,
    help='Configuration key.',
)
def config_show(
    config_key: str,
):
    console = Console()
    if config_key is None:
        console.print(settings.as_dict())
    else:
        try:
            console.print(settings[config_key].to_dict())
        except AttributeError:
            console.print(settings[config_key])
        except KeyError:
            console.print(None)


@command_line_tools.command(
    name='init', help='Initialize the AilingBot environment.'
)
@click.option('--silence', is_flag=True, help='Without asking the user.')
@click.option(
    '--overwrite',
    is_flag=True,
    help='Overwrite existing file if a file with the same name already exists.',
)
@_coro_cmd
async def init(silence: bool, overwrite: bool):
    """Initialize the AilingBot environment."""
    file_path = os.path.join('.', 'settings.toml')
    if not overwrite:
        if os.path.exists(file_path):
            click.echo(
                click.style(
                    text=f'Configuration file {file_path} already exists.',
                    fg='yellow',
                )
            )
            raise click.Abort()

    config: dict = {
        'lang': 'zh_CN',
        'tz': 'Asia/Shanghai',
        'policy': {},
        'broker': {},
        'channel': {},
        'uvicorn': {
            'host': '0.0.0.0',
            'port': 8080,
        },
    }
    if silence:
        config['policy'] = {
            'name': 'lc_conversation_chain',
            'llm': {
                '_type': 'openai',
                'model_name': 'gpt-3.5-turbo',
                'openai_api_key': '',
                'temperature': 0,
            },
        }
        config['broker'] = {
            'name': 'pika',
            'port': 5672,
            'user': '',
            'password': '',
            'timeout': 5,
            'queue_name_prefix': '',
        }
        config['channel'] = {
            'name': 'wechatwork',
            'corpid': '',
            'corpsecret': '',
            'agentid': 0,
            'token': '',
            'aes_key': '',
        }
    else:
        policy = await display_radio_prompt(
            title='Select chat policy:',
            values=[
                (x, x)
                for x in [
                    'lc_llm_chain',
                    'lc_conversation_chain',
                    'Configure Later',
                ]
            ],
            cancel_value='Configure Later',
        )
        if policy == 'lc_llm_chain':
            config['policy'] = {
                'name': 'lc_llm_chain',
                '_type': 'llm_chain',
                'llm': {
                    '_type': 'openai',
                    'model_name': 'gpt-3.5-turbo',
                    'openai_api_key': '',
                    'temperature': 0,
                },
                'prompt': {
                    '_type': 'prompt',
                    'template': tomlkit.string(
                        """Human: {input}

AI:
""",
                        multiline=True,
                    ),
                    'input_variables': ['input'],
                },
            }
        elif policy == 'lc_conversation_chain':
            config['policy'] = {
                'name': 'lc_conversation_chain',
                'llm': {
                    '_type': 'openai',
                    'model_name': 'gpt-3.5-turbo',
                    'openai_api_key': '',
                    'temperature': 0,
                },
            }

        broker = await display_radio_prompt(
            title='Select broker:',
            values=[(x, x) for x in ['pika', 'Configure Later']],
            cancel_value='Configure Later',
        )
        if broker == 'pika':
            config['broker'] = {
                'name': 'pika',
                'port': 5672,
                'user': '',
                'password': '',
                'timeout': 5,
                'queue_name_prefix': '',
            }

        channel = await display_radio_prompt(
            title='Select channel:',
            values=[
                (x, x) for x in ['wechatwork', 'feishu', 'Configure Later']
            ],
            cancel_value='Configure Later',
        )
        if channel == 'wechatwork':
            config['channel'] = {
                'name': 'wechatwork',
                'corpid': '',
                'corpsecret': '',
                'agentid': 0,
                'token': '',
                'aes_key': '',
            }
        elif channel == 'feishu':
            config['channel'] = {
                'name': 'feishu',
                'app_id': '',
                'app_secret': '',
                'verification_token': 0,
            }

    with open(file_path, 'w') as f:
        f.write(tomlkit.dumps(config))
    click.echo(
        click.style(
            text=f'Configuration file {file_path} has been created.',
            fg='green',
        )
    )


if __name__ == '__main__':
    command_line_tools(prog_name='ailingbot')
