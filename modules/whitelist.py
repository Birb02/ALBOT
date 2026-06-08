import discord

async def run(ctx, bot, allowed, debug_log):

    if not await allowed(ctx):
        return await ctx.channel.send("[FAIL] Unauthorized")

    args = ctx.content.split()

    if len(args) < 2:
        return await ctx.channel.send("Usage: >whitelist add @user | >whitelist remove @user | >whitelist list")

    action = args[1].lower()
    guild = ctx.guild
    channel = discord.utils.get(guild.text_channels, name="servconf")

    if not channel:
        return await ctx.channel.send("[FAIL] No servconf channel")

    if action == "add":
        if len(args) < 3 or not ctx.mentions:
            return await ctx.channel.send("Usage: >whitelist add @user")

        user = ctx.mentions[0]
        user_id = user.id

        # Check if already in hardcoded list (in start.py)
        async for msg in channel.history(limit=100):
            if msg.author == bot.user and "[WHITELIST_ADMINS]" in msg.content:
                if str(user_id) in msg.content:
                    return await ctx.channel.send(f"[FAIL] {user} is already whitelisted")
                break

        # Find or create whitelist message
        whitelist_msg = None
        async for msg in channel.history(limit=100):
            if msg.author == bot.user and "[WHITELIST_ADMINS]" in msg.content:
                whitelist_msg = msg
                break

        if whitelist_msg:
            updated_content = whitelist_msg.content + f"\n{user_id}|{user.name}"
            await whitelist_msg.edit(content=updated_content)
        else:
            content = f"""[WHITELIST_ADMINS]
{user_id}|{user.name}"""
            await channel.send(f"```{content}```")

        await ctx.channel.send(f"[OK] Added {user} to whitelist")
        debug_log(f"Added {user} ({user_id}) to whitelist")

    elif action == "remove":
        if len(args) < 3 or not ctx.mentions:
            return await ctx.channel.send("Usage: >whitelist remove @user")

        user = ctx.mentions[0]
        user_id = user.id

        # Find and update whitelist message
        async for msg in channel.history(limit=100):
            if msg.author == bot.user and "[WHITELIST_ADMINS]" in msg.content:
                lines = msg.content.split("\n")
                new_lines = [line for line in lines if not line.startswith(str(user_id) + "|")]

                if len(lines) == len(new_lines):
                    return await ctx.channel.send(f"[FAIL] {user} not found in whitelist")

                if len(new_lines) > 1:
                    await msg.edit(content="\n".join(new_lines))
                else:
                    await msg.delete()

                await ctx.channel.send(f"[OK] Removed {user} from whitelist")
                debug_log(f"Removed {user} ({user_id}) from whitelist")
                return

        await ctx.channel.send("[FAIL] No whitelist found")

    elif action == "list":
        async for msg in channel.history(limit=100):
            if msg.author == bot.user and "[WHITELIST_ADMINS]" in msg.content:
                await ctx.channel.send("**Current Additional Whitelisted Admins:**")
                await ctx.channel.send(msg.content)
                return

        await ctx.channel.send("[!] No additional admins whitelisted (core admins always active)")

    else:
        await ctx.channel.send("Usage: >whitelist add @user | >whitelist remove @user | >whitelist list")
