class AilingBotError(Exception):
    """Base class for all customized errors.

    All customized errors may send to user, so the reason field must be easy to understand.
    """

    def __init__(
        self, reason: str = '', *, critical: bool = False, suggestion: str = ''
    ):
        """Init.

        :param reason: Causes of error.
        :type reason: str
        :param critical: Whether the error is critical. Process should to exit if this is true.
        :type critical: bool
        :param suggestion: Suggestion that respond to user when error occurred.
        :type suggestion: str
        """
        self.reason = reason
        self.critical = critical
        self.suggestion = suggestion

    def __str__(self):
        return self.reason


class ExternalHTTPAPIError(AilingBotError):
    """Raised when calling external api failed."""

    pass


class EmptyQueueError(AilingBotError):
    """Raised when queue is empty no more message to consume."""

    pass


class FullQueueError(AilingBotError):
    """Raised when queue is full no more message could publish to."""

    pass


class BrokerError(AilingBotError):
    """Raised when connecting to broker or broker operation failed."""

    pass


class ChatPolicyError(AilingBotError):
    """Raised when chat policy error."""

    pass


class ConfigValidationError(AilingBotError):
    """Raised when configuration invalid."""

    pass


class ComponentNotFoundError(AilingBotError):
    """Raised when component not found."""

    pass


class UnsupportedMessageTypeError(AilingBotError):
    """Raised when there is an unsupported message type."""
