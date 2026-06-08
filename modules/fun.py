import discord
import os

async def run(ctx, bot, allowed, debug_log):

    if not await allowed(ctx):
        return await ctx.channel.send("[FAIL] Unauthorized")

    guild = ctx.guild
    channel = discord.utils.get(guild.text_channels, name="servconf")

    revision = "0.1"
    try:
        with open("./modules/revision.txt", "r") as f:
            revision = f.read().strip()
    except:
        pass

    # Get hardcoded whitelist (from start.py WHITELIST)
    WHITELIST = {
        949748857351340062,
        479990917110038529
    }
    whitelist_count = len(WHITELIST)

    # Get additional whitelisted users from servconf
    additional_whitelist = set()
    if channel:
        async for msg in channel.history(limit=100):
            if msg.author == bot.user and "[WHITELIST_ADMINS]" in msg.content:
                for line in msg.content.split("\n"):
                    line = line.strip()
                    if "|" in line and not line.startswith("["):
                        try:
                            user_id = int(line.split("|")[0].strip())
                            additional_whitelist.add(user_id)
                        except ValueError:
                            continue
                break

    additional_count = len(additional_whitelist)

    # Get bot status
    bot_status = str(bot.status).replace("Status.", "").upper()

    # Get available subfun subsections
    subfun_path = "./modules/subfun"
    subfun_modules = []
    if os.path.exists(subfun_path):
        for file in os.listdir(subfun_path):
            if file.endswith(".py") and file != "__init__.py":
                module_name = file[:-3]
                subfun_modules.append(f">fun {module_name}")

    fun_text = f"""Fun/Misc Utilities
Version: {revision}
Status: {bot_status}

Core Admins: {whitelist_count}
Additional Admins: {additional_count} (Shadowed)

Available Commands:
>fun - This help menu
"""

    if subfun_modules:
        fun_text += "\nAvailable Subsections:\n"
        for idx, subsection in enumerate(sorted(subfun_modules), 1):
            fun_text += f"{subsection}\n"

    await ctx.channel.send(f"```\n{fun_text}\n```")
