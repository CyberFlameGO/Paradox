# from contextBot.CommandHandler import CommandHandler
from paraCH import paraCH
from botconf import Conf`

cmds = paraCH()


@cmds.cmd("test", aliases=["testy", "tst"])
@cmds.execute("flags", flags=["please", "c=="])
async def cmd_test(ctx):
    """
    Usage:
        {prefix}test [--please] [-c <stuff>]
    Examples:
        {prefix}test  ok --please -c test
    """
    if ctx.arg_str:
        await ctx.reply("I got args "+ctx.arg_str)
    await ctx.reply("I got params "+str(ctx.params))
    msg = "no "
    if ctx.flags["please"]:
        msg = "ok "
    if ctx.flags["c"]:
        msg += ctx.flags["c"]
    await ctx.reply(msg)
