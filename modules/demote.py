import discord

async def run(ctx, bot, allowed, debug_log):

    if not allowed(ctx):
        return await ctx.channel.send("[FAIL] Unauthorized")

    await ctx.channel.send("[!] Demote command is under construction")
