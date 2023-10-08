from discord.ext import commands


class ErrorHandler(commands.Cog):
    """A cog for global error handling."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """A global error handler cog."""

        if isinstance(error, commands.CommandNotFound):
            message = "Inavlid Command"
        elif isinstance(error, commands.CommandOnCooldown):
            message = f"This command is on cooldown. Please try again after {round(error.retry_after, 1)} seconds."
        elif isinstance(error, commands.MissingPermissions):
            message = "You are missing the required permissions to run this command!"
        elif isinstance(error, commands.UserInputError):
            message = "Something about your input was wrong, please check your input and try again!"
        elif isinstance(error, commands.ConversionError):
            message = "Conversion Error!"
        elif isinstance(error, commands.MissingRequiredArgument):
            message = "Missing Required Argument"
        elif isinstance(error, commands.ArgumentParsingError):
            message = "Argument Parsing Error"
        elif isinstance(error, commands.UnexpectedQuoteError):
            message = "Unexpected Quote Error"
        elif isinstance(error, commands.InvalidEndOfQuotedStringError):
            message = "Invalid End Of Quoted String Error"
        elif isinstance(error, commands.ExpectedClosingQuoteError):
            message = "Expected Closing Quote Error"
        elif isinstance(error, commands.BadArgument):
            message = "Bad Argument"
        elif isinstance(error, commands.BadUnionArgument):
            message = "Bad Union Argument"
        elif isinstance(error, commands.PrivateMessageOnly):
            message = "PrivateMessageOnly"
        elif isinstance(error, commands.NoPrivateMessage):
            message = "NoPrivateMessage"
        elif isinstance(error, commands.CheckFailure):
            message = "CheckFailure"
        elif isinstance(error, commands.CheckAnyFailure):
            message = "CheckAnyFailure"
        elif isinstance(error, commands.DisabledCommand):
            message = "DisabledCommand"
        elif isinstance(error, commands.CommandInvokeError):
            message = "CommandInvokeError"
        elif isinstance(error, commands.TooManyArguments):
            message = "TooManyArguments"
        elif isinstance(error, commands.MaxConcurrencyReached):
            message = "MaxConcurrencyReached"
        elif isinstance(error, commands.NotOwner):
            message = "NotOwner"
        elif isinstance(error, commands.MessageNotFound):
            message = "MessageNotFound"
        elif isinstance(error, commands.MemberNotFound):
            message = "MemberNotFound"
        elif isinstance(error, commands.GuildNotFound):
            message = "GuildNotFound"
        elif isinstance(error, commands.UserNotFound):
            message = "UserNotFound"
        elif isinstance(error, commands.ChannelNotFound):
            message = "ChannelNotFound"
        elif isinstance(error, commands.ChannelNotReadable):
            message = "ChannelNotReadable"
        elif isinstance(error, commands.BadColourArgument):
            message = "BadColourArgument"
        elif isinstance(error, commands.RoleNotFound):
            message = "RoleNotFound"
        elif isinstance(error, commands.BadInviteArgument):
            message = "BadInviteArgument"
        elif isinstance(error, commands.EmojiNotFound):
            message = "EmojiNotFound"
        elif isinstance(error, commands.PartialEmojiConversionFailure):
            message = "PartialEmojiConversionFailure"
        elif isinstance(error, commands.BadBoolArgument):
            message = "BadBoolArgument"
        elif isinstance(error, commands.MissingPermissions):
            message = "MissingPermissions"
        elif isinstance(error, commands.BotMissingPermissions):
            message = "BotMissingPermissions"
        elif isinstance(error, commands.MissingRole):
            message = "MissingRole"
        elif isinstance(error, commands.BotMissingRole):
            message = "BotMissingRole"
        elif isinstance(error, commands.MissingAnyRole):
            message = "MissingAnyRole"
        elif isinstance(error, commands.BotMissingAnyRole):
            message = "BotMissingAnyRole"
        elif isinstance(error, commands.NSFWChannelRequired):
            message = "NSFWChannelRequired"
        elif isinstance(error, commands.ExtensionError):
            message = "ExtensionError"
        elif isinstance(error, commands.ExtensionAlreadyLoaded):
            message = "ExtensionAlreadyLoaded"
        elif isinstance(error, commands.ExtensionNotLoaded):
            message = "ExtensionNotLoaded"
        elif isinstance(error, commands.NoEntryPointError):
            message = "NoEntryPointError"
        elif isinstance(error, commands.ExtensionFailed):
            message = "ExtensionFailed"
        elif isinstance(error, commands.ExtensionNotFound):
            message = "ExtensionNotFound"
        elif isinstance(error, commands.CommandRegistrationError):
            message = "CommandRegistrationError"
        else:
            message = "Oh no! Something went wrong while running the command! " + error

        await ctx.send(message, delete_after=5)
        await ctx.message.delete(delay=5)


async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorHandler(bot))
