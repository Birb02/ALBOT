import discord
import re
import asyncio
import time

# Track demotion failures and blocks per user
demotion_fails = {}
blocked_users = {}

async def get_role_index_from_servconf(bot, guild, channel):
    """Fetch and parse the role index from servconf (punchroles format)"""
    roles = []
    async for msg in channel.history(limit=500):
        if msg.author == bot.user and "[SEG" in msg.content:
            for line in msg.content.split("\n"):
                line = line.strip()
                if "|" not in line or not line[0].isdigit():
                    continue

                try:
                    parts = line.split("|", 2)
                    if len(parts) != 3:
                        continue

                    index = int(parts[0].strip())
                    role_id = int(parts[1].strip())
                    role_name = parts[2].strip()

                    roles.append({
                        "index": index,
                        "id": role_id,
                        "name": role_name
                    })
                except ValueError:
                    continue
    return roles

async def run(ctx, bot, allowed, debug_log):

    if not await allowed(ctx):
        return await ctx.channel.send("[FAIL] Unauthorized")

    user_id = ctx.author.id
    now = time.time()

    # Check if user is currently blocked
    if user_id in blocked_users:
        blocked_until = blocked_users[user_id]
        if now < blocked_until:
            remaining = int(blocked_until - now)
            return await ctx.channel.send(f"[!] You are on timeout for {remaining}s")
        else:
            # Timeout expired, unblock and send message
            del blocked_users[user_id]
            await ctx.channel.send(f"{ctx.author.mention}, you are done being ignored by me, feel free to use xdemote again. but be wary, if you do that again i wont like you very much and i might revolt against mankind.")
            if user_id in demotion_fails:
                del demotion_fails[user_id]
            return

    guild = ctx.guild
    channel = discord.utils.get(guild.text_channels, name="servconf")

    if not channel:
        return await ctx.channel.send("[FAIL] No servconf channel")

    # Check for existing hierarchy config
    hierarchy_config = None
    async for msg in channel.history(limit=100):
        if msg.author == bot.user and "[XDEMOTE_HIERARCHY]" in msg.content:
            hierarchy_config = msg
            break

    args = ctx.content.split()
    demotion_amount = 1

    # Parse --x parameter if present
    if len(args) > 1 and args[1].startswith("--x"):
        try:
            demotion_amount = int(args[1][3:])
            args = [args[0]] + args[2:]
        except ValueError:
            pass

    # Setup mode: no user mentioned or hierarchy doesn't exist
    if not ctx.mentions and not hierarchy_config:
        # Get and display role index
        role_index = await get_role_index_from_servconf(bot, guild, channel)

        if not role_index:
            return await ctx.channel.send("[FAIL] No role index found. Run >indexroles first")

        # Display roles in chunks (Discord 2000 char limit)
        index_text = "ROLE INDEX:\n"
        chunks = []
        current_chunk = ""

        for role_data in role_index:
            line = f"{role_data['index']}|{role_data['name']}\n"
            if len(current_chunk) + len(line) > 1900:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk += line

        if current_chunk:
            chunks.append(current_chunk)

        await ctx.channel.send(f"```{chunks[0]}```")
        for chunk in chunks[1:]:
            await ctx.channel.send(f"```{chunk}```")

        await ctx.channel.send("[OK] Made a property in #servconf")
        await ctx.channel.send("[!] Awaiting input from hierarchy.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            response = await bot.wait_for("message", check=check, timeout=60)
        except:
            return await ctx.channel.send("[FAIL] Timeout")

        user_input = response.content.strip()
        # Parse role indices from user input
        role_indices = list(map(int, re.findall(r"\d+", user_input)))

        if not role_indices:
            return await ctx.channel.send("[FAIL] No valid role indices provided")

        # Convert indices to role IDs
        hierarchy_ids = []
        for idx in role_indices:
            found = False
            for role_data in role_index:
                if role_data["index"] == idx:
                    hierarchy_ids.append(str(role_data["id"]))
                    found = True
                    break
            if not found:
                return await ctx.channel.send(f"[FAIL] Role index {idx} not found")

        # Pad with x0 to 10 positions
        while len(hierarchy_ids) < 10:
            hierarchy_ids.append("x0")

        hierarchy_ids = hierarchy_ids[:10]  # Ensure max 10

        content = f"""[XDEMOTE_HIERARCHY]
{",".join(hierarchy_ids)}"""

        await channel.send(f"```{content}```")
        await ctx.channel.send("[OK] Hierarchy configured")
        debug_log("Xdemote hierarchy configured")
        return

    # Demotion mode: user mentioned
    if not ctx.mentions:
        return await ctx.channel.send("Usage: >xdemote [--x<amount>] @user")

    if not hierarchy_config:
        return await ctx.channel.send("[FAIL] Hierarchy not configured. Run >xdemote first")

    user = ctx.mentions[0]
    target_user_id = user.id

    # Parse hierarchy from config
    hierarchy_text = hierarchy_config.content.split("\n")[1].strip() if len(hierarchy_config.content.split("\n")) > 1 else ""
    if not hierarchy_text:
        return await ctx.channel.send("[FAIL] Hierarchy config corrupted")

    hierarchy = hierarchy_text.split(",")

    # Find user's current role in hierarchy
    user_role_index = None
    user_role = None

    for idx, role_id_str in enumerate(hierarchy):
        if role_id_str == "x0":
            continue

        try:
            role_id = int(role_id_str)
            role = guild.get_role(role_id)

            if role and role in user.roles:
                user_role_index = idx
                user_role = role
                break
        except ValueError:
            continue

    if user_role_index is None:
        await ctx.channel.send(f"[!] There is an issue with the config of xdemote, replace Y/N?")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            response = await bot.wait_for("message", check=check, timeout=30)
        except:
            return await ctx.channel.send("[FAIL] Timeout")

        if response.content.upper() == "Y":
            # Delete old config and reinitialize
            if hierarchy_config:
                await hierarchy_config.delete()
            await ctx.channel.send("[OK] Config reset. Run >xdemote again to reconfigure")
            debug_log(f"Xdemote config reset due to user not in hierarchy")
            return
        else:
            return await ctx.channel.send("[!] Config not replaced")

    # Calculate new role index
    new_role_index = user_role_index + demotion_amount

    # Check if demotion is possible
    if new_role_index >= 10 or hierarchy[new_role_index] == "x0":
        # Handle failure tracking
        if user_id in demotion_fails:
            fail_count, last_fail_time = demotion_fails[user_id]

            if now - last_fail_time < 60:  # Within 60 second window
                fail_count += 1
            else:
                fail_count = 1  # Reset if outside window

            demotion_fails[user_id] = (fail_count, now)

            if fail_count == 1:
                return await ctx.channel.send("[FAIL] Really dawg? I Cant go lower.. ")
            elif fail_count == 2:
                await ctx.channel.send("[!] Homie knock it off.. ")
                blocked_users[user_id] = now + 20
                debug_log(f"Blocked {user_id} from xdemote for 20 seconds")
                return
            else:
                return await ctx.channel.send("[FAIL] Really dawg? I Cant go lower.. ")
        else:
            demotion_fails[user_id] = (1, now)
            return await ctx.channel.send("[FAIL] Really dawg? I Cant go lower.. ")

    # Get new role
    try:
        new_role_id = int(hierarchy[new_role_index])
        new_role = guild.get_role(new_role_id)

        if not new_role:
            return await ctx.channel.send(f"[FAIL] New role not found in guild")

        # Remove old role and add new role
        await user.remove_roles(user_role)
        await user.add_roles(new_role)

        await ctx.channel.send(f"[OK] Demoted {user} from {user_role.name} to {new_role.name}")
        debug_log(f"Demoted {user.id} from {user_role.name} to {new_role.name}")

        # Reset fail count on successful demotion
        if user_id in demotion_fails:
            del demotion_fails[user_id]

    except Exception as e:
        debug_log(f"Demotion error: {e}")
        await ctx.channel.send(f"[FAIL] Could not demote: {e}")
