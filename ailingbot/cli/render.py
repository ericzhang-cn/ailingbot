from __future__ import annotations

import functools
import typing

import click
from prompt_toolkit import Application
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.layout import Layout, HSplit
from prompt_toolkit.widgets import RadioList, Label, TextArea
from tabulate import tabulate

from ailingbot.chat.messages import (
    ResponseMessage,
    TextResponseMessage,
    FallbackResponseMessage,
    TabularResponseMessage,
    OptionsResponseMessage,
    SilenceResponseMessage,
    InputResponseMessage,
)


async def display_input_prompt(
    *,
    title: str = '',
    visible: bool = True,
    required: bool = True,
    cancel_value: typing.Any = None,
) -> typing.Optional[str]:
    text_area = TextArea(password=not visible)

    bindings = KeyBindings()

    @bindings.add('enter')
    def exit_with_value(event):
        """Pressing Enter will exit the user interface, returning the highlighted value."""
        event.app.exit(result=text_area.text)

    @bindings.add('c-c')
    def backup_exit_with_value(event):
        """Pressing Ctrl-C will exit the user interface with the cancel_value."""
        event.app.exit(result=cancel_value)

    if required:
        title_ = f'{title} (Required)'
    else:
        title_ = f'{title} (Optional, press Enter to skip)'

    application = Application(
        layout=Layout(HSplit([Label(title_), text_area])),
        key_bindings=merge_key_bindings([load_key_bindings(), bindings]),
        mouse_support=True,
        full_screen=False,
    )

    return await application.run_async()


async def display_radio_prompt(
    *,
    title: str = '',
    values: typing.Optional[list[tuple[typing.Any, AnyFormattedText]]] = None,
    cancel_value: typing.Any = None,
) -> typing.Any:
    """Displays radio boxes for users to select.

    :param title: Radio title.
    :type title: str
    :param values: Radio values.
    :type values: typing.Optional[typing.List[typing.Tuple[str, AnyFormattedText]]]
    :param cancel_value: Value that returns when Pressing Ctrl-C.
    :type cancel_value: str
    :return: Selected value.
    :rtype: str
    """
    radio_list = RadioList(values)
    radio_list.control.key_bindings.remove('enter')

    bindings = KeyBindings()

    @bindings.add('enter')
    def exit_with_value(event):
        """Pressing Enter will exit the user interface, returning the highlighted value."""
        radio_list._handle_enter()
        event.app.exit(result=radio_list.current_value)

    @bindings.add('c-c')
    def backup_exit_with_value(event):
        """Pressing Ctrl-C will exit the user interface with the cancel_value."""
        event.app.exit(result=cancel_value)

    application = Application(
        layout=Layout(HSplit([Label(title), radio_list])),
        key_bindings=merge_key_bindings([load_key_bindings(), bindings]),
        mouse_support=True,
        full_screen=False,
    )

    return await application.run_async()


@functools.singledispatch
async def render(response: ResponseMessage) -> None:
    """Virtual function of all response message renders.

    Converts response message to command tools content.

    :param response: Response message.
    :type response: ResponseMessage
    :return: Render result.
    :rtype: typing.List[Line]:
    """
    raise NotImplementedError()


@render.register
async def _render(response: SilenceResponseMessage) -> None:
    """Renders silence response message."""
    pass


@render.register
async def _render(response: TextResponseMessage) -> None:
    """Renders text response message."""
    click.secho(response.text)


@render.register
async def _render(response: FallbackResponseMessage) -> None:
    """Renders error fallback response message."""
    click.secho('Error occurred', fg='red')
    click.secho('----------', fg='red')
    click.secho(f'Cause: {response.reason}', italic=True)
    click.secho(f'Suggestion: {response.suggestion}', italic=True)


@render.register
async def _render(response: TabularResponseMessage) -> None:
    """Renders tabular response message."""
    click.secho(response.title)
    click.secho(
        tabulate(
            tabular_data=response.data,
            headers=response.headers,
            tablefmt='grid',
        )
    )


@render.register
async def _render(response: InputResponseMessage) -> str:
    """Renders input dialogue response message."""
    click.secho(
        'Tips: Enter - Submit and exit | Ctrl+c - Cancel and exit',
        fg='blue',
    )
    click.secho('----------', fg='blue')
    return await display_input_prompt(
        title=response.title,
        visible=response.visible,
        required=response.required,
    )


@render.register
async def _render(response: OptionsResponseMessage) -> typing.Any:
    """Renders options response message."""
    click.secho(
        'Tips: Space - Select option | Enter - Select option and exit | Ctrl+c - Cancel and exit',
        fg='blue',
    )
    click.secho('----------', fg='blue')
    values = [(x.value, x.text) for x in response.options]
    return await display_radio_prompt(title=response.title, values=values)
