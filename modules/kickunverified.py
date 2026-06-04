import discord

async def run(ctx, bot, allowed, debug_log):

    if not allowed(ctx):
        return await ctx.channel.send("[FAIL] Unauthorized")

    guild = ctx.guild
    unverified_role = discord.utils.get(guild.roles, name="Unverified")

    if not unverified_role:
        return await ctx.channel.send("[FAIL] Unverified role not found")

    unverified_users = [member for member in guild.members if unverified_role in member.roles]

    if not unverified_users:
        return await ctx.channel.send("[FAIL] No unverified users found")

    await ctx.channel.send(f"Unverified Users: {len(unverified_users)}")
    for idx, user in enumerate(unverified_users, 1):
        await ctx.channel.send(f"{idx}: {user}")

    await ctx.channel.send("Proceed Y/N")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        response = await bot.wait_for("message", check=check, timeout=60)
    except:
        return await ctx.channel.send("[FAIL] Timeout")

    if response.content.upper() != "Y":
        return await ctx.channel.send("[FAIL] User input declared No")

    for user in unverified_users:
        try:
            await user.send("You are being kicked from the server due to not verifying. You may rejoin at a later date if you choose to verify.")
        except:
            debug_log(f"Could not DM {user}")

        try:
            await user.kick(reason="Not verified")
        except:
            debug_log(f"Could not kick {user}")

    await ctx.channel.send("[OK] Done.")
