import discord
import time
import os

DEBUG_ENABLED = False
START_TIME = None

async def run(ctx, bot, allowed, debug_log):
    global DEBUG_ENABLED, START_TIME

    if not allowed(ctx):
        return await ctx.channel.send("[FAIL] Unauthorized")

    args = ctx.content.split()

    if len(args) < 2:
        return await ctx.channel.send("Usage: >debug on/off")

    mode = args[1].lower()

    if mode == "on":
        DEBUG_ENABLED = True
        START_TIME = time.time()
        await ctx.channel.send("[OK] Debug mode enabled")
        await ctx.channel.send("[!] Debug logs will now be verbose")

    elif mode == "off":
        if START_TIME:
            elapsed = time.time() - START_TIME
            await ctx.channel.send(f"[OK] Debug mode disabled")
            await ctx.channel.send(f"[!] Execution time: {elapsed:.2f}s")
            DEBUG_ENABLED = False
            START_TIME = None
        else:
            DEBUG_ENABLED = False
            await ctx.channel.send("[OK] Debug mode disabled")

    else:
        await ctx.channel.send("Usage: >debug on/off")
