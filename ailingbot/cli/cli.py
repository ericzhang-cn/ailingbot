from __future__ import annotations

import asyncio
import sys
import typing
import uuid
from functools import wraps

import click
import emoji
import uvicorn
from dynaconf import ValidationError
from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText

import ailingbot.shared.errors
from ailingbot.channels.channel import ChannelAgent, ChannelWebhookFactory
from ailingbot.chat.chatbot import ChatBot, BotRunMode
from ailingbot.chat.messages import (
    TextRequestMessage,
    FallbackResponseMessage,
    OptionsResponseMessage,
    InputRequestMessage,
    InputResponseMessage,
)
from ailingbot.cli import options
from ailingbot.cli.render import render
from ailingbot.config import settings, validators


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
@options.config_file_option
@options.broker_name_option
@options.broker_args_option
@options.policy_name_option
@options.policy_args_option
@options.log_level_option
@options.log_file_option
def bot_serve(
        number_of_tasks: int,
        config_file: str,
        debug: bool,
        broker: str,
        broker_args: dict,
        policy: str,
        policy_args: dict,
        log_level: str,
        log_file: str,
):
    """Run chatbot task(s) to serve request messages.

    :param number_of_tasks: Number of concurrently executed tasks.
    :type number_of_tasks: int
    :param debug: Whether to enable debug mode.
    :type debug: bool
    :param broker:
    :type broker:
    :param broker_args:
    :type broker_args:
    :param policy:
    :type policy:
    :param policy_args:
    :type policy_args:
    :param log_level:
    :type log_level:
    :param log_file:
    :type log_file:
    """
    _set_logger(sink=log_file, level=log_level)

    if config_file:
        settings.load_file(config_file)

    if broker:
        settings.set('broker.name', broker)
    if broker_args:
        settings.set('broker.args', broker_args)
    if policy:
        settings.set('policy.name', policy)
    if policy_args:
        settings.set('policy.args', policy_args)

    settings.validators.clear()
    settings.validators.register(validators['broker.name'])
    settings.validators.register(validators['broker.args'])
    settings.validators.register(validators['policy.name'])
    settings.validators.register(validators['policy.args'])
    try:
        settings.validators.validate()
    except ValidationError as e:
        click.echo(
            click.style(
                text=f'Configuration validation failed. Detail: {e.message}',
                fg='red',
            )
        )
        raise click.Abort()

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
@options.config_file_option
@options.policy_name_option
@options.policy_args_option
@click.option('--debug', is_flag=True, help='Enable debug mode.')
@_coro_cmd
async def bot_chat(
        config_file: str,
        policy: str,
        policy_args: dict,
        debug: bool,
):
    """Start an interactive bot conversation environment.

    :param config_file:
    :type config_file:
    :param policy:
    :type policy:
    :param policy_args:
    :type policy_args:
    :param debug: Whether to enable debug mode.
    :type debug: bool
    """
    if config_file:
        settings.load_file(config_file)

    if policy:
        settings.set('policy.name', policy)
    if policy_args:
        settings.set('policy.args', policy_args)

    settings.validators.clear()
    settings.validators.register(validators['policy.name'])
    settings.validators.register(validators['policy.args'])
    try:
        settings.validators.validate()
    except ValidationError as e:
        click.echo(
            click.style(
                text=f'Configuration validation failed. Detail: {e.message}',
                fg='red',
            )
        )
        raise click.Abort()

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
            request = TextRequestMessage(text=input_)

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
@options.config_file_option
@options.channel_agent_name_option
@options.channel_agent_args_option
@options.broker_name_option
@options.broker_args_option
@options.log_level_option
@options.log_file_option
def channel_serve_agent(
        number_of_tasks: int,
        config_file: str,
        channel_agent: str,
        channel_agent_args: dict,
        broker: str,
        broker_args: dict,
        log_level: str,
        log_file: str,
):
    """Run channel agent task(s) to serve response messages.

    :param number_of_tasks: Number of concurrently executed tasks.
    :type number_of_tasks: int
    :param channel_agent: Channel name.
    :type channel_agent: str
    :param channel_agent_args: Channel arguments.
    :type channel_agent_args: dict
    :param broker:
    :type broker:
    :param broker_args:
    :type broker_args:
    :param log_level:
    :type log_level:
    :param log_file:
    :type log_file:
    """
    _set_logger(sink=log_file, level=log_level)

    if config_file:
        settings.load_file(config_file)

    if channel_agent:
        settings.set('channel.agent.name', channel_agent)
    if channel_agent_args:
        settings.set('channel.agent.args', channel_agent_args)
    if broker:
        settings.set('broker.name', broker)
    if broker_args:
        settings.set('broker.args', broker_args)

    settings.validators.clear()
    settings.validators.register(validators['broker.name'])
    settings.validators.register(validators['broker.args'])
    settings.validators.register(validators['channel.agent.name'])
    settings.validators.register(validators['channel.agent.args'])
    try:
        settings.validators.validate()
    except ValidationError as e:
        click.echo(
            click.style(
                text=f'Configuration validation failed. Detail: {e.message}',
                fg='red',
            )
        )
        raise click.Abort()

    agent = ChannelAgent.get_agent(
        settings.channel.agent.name,
        num_of_tasks=number_of_tasks,
    )
    try:
        agent.run()
    except ailingbot.shared.errors.AilingBotError as e:
        raise click.ClickException(e.reason)


@channel_group.command(
    name='serve_webhook', help='Run webhook server to receive events.'
)
@options.config_file_option
@options.channel_webhook_name_option
@options.channel_webhook_args_option
@options.broker_name_option
@options.broker_args_option
@options.channel_uvicorn_args_option
@options.log_level_option
@options.log_file_option
@_coro_cmd
async def channel_serve_webhook(
        config_file: str,
        channel_webhook: str,
        channel_webhook_args: dict,
        broker: str,
        broker_args: dict,
        channel_uvicorn_args: dict,
        log_level: str,
        log_file: str,
):
    _set_logger(sink=log_file, level=log_level)

    if config_file:
        settings.load_file(config_file)

    if channel_webhook:
        settings.set('channel.webhook.name', channel_webhook)
    if channel_webhook_args:
        settings.set('channel.webhook.args', channel_webhook_args)
    if channel_uvicorn_args:
        settings.set('channel.uvicorn.args', channel_uvicorn_args)
    if broker:
        settings.set('broker.name', broker)
    if broker_args:
        settings.set('broker.args', broker_args)

    settings.validators.clear()
    settings.validators.register(validators['broker.name'])
    settings.validators.register(validators['broker.args'])
    settings.validators.register(validators['channel.webhook.name'])
    settings.validators.register(validators['channel.webhook.args'])
    settings.validators.register(validators['channel.uvicorn.args'])
    try:
        settings.validators.validate()
    except ValidationError as e:
        click.echo(
            click.style(
                text=f'Configuration validation failed. Detail: {e.message}',
                fg='red',
            )
        )
        raise click.Abort()

    webhook = await ChannelWebhookFactory.get_webhook(
        settings.channel.webhook.name
    )

    config = uvicorn.Config(app=webhook, **settings.channel.uvicorn.args)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    command_line_tools(prog_name='ailingbot')
