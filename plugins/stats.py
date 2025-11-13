# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.
# -------- Imports for redeem system --------
import secrets
import string
from datetime import datetime, timedelta
from pymongo import ReturnDocument
# -------- redeem imports end here

# -------- Stats start from here --------
from datetime import timedelta, datetime
from shared_client import client as bot_client
from telethon import events
from utils.func import get_premium_details, is_private_chat, get_display_name, get_user_data, premium_users_collection, is_premium_user
from config import OWNER_ID
import logging
logging.basicConfig(format=
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger('teamspy')


@bot_client.on(events.NewMessage(pattern='/status'))
async def status_handler(event):
    if not await is_private_chat(event):
        await event.respond("This command can only be used in private chats for security reasons.")
        return
    
    """Handle /status command to check user session and bot status"""
    user_id = event.sender_id
    user_data = await get_user_data(user_id)
    
    session_active = False
    bot_active = False
    
    if user_data and "session_string" in user_data:
            session_active = True
    
    # Check if user has a custom bot
    if user_data and "bot_token" in user_data:
        bot_active = True
    
    # Add premium status check
    premium_status = "❌ Not a premium member"
    premium_details = await get_premium_details(user_id)
    if premium_details:
        # Convert to IST timezone
        expiry_utc = premium_details["subscription_end"]
        expiry_ist = expiry_utc + timedelta(hours=5, minutes=30)
        formatted_expiry = expiry_ist.strftime("%d-%b-%Y %I:%M:%S %p")
        premium_status = f"✅ Premium until {formatted_expiry} (IST)"
    
    await event.respond(
        f"""🧾 **Account Overview**  

        **🔐 Login Status:** {'✅ Active' if session_active else '❌ Inactive'}  
        **💎 Premium Status:** {premium_status}"""
        )


@bot_client.on(events.NewMessage(pattern='/transfer'))
async def transfer_premium_handler(event):
    if not await is_private_chat(event):
        await event.respond(
            'This command can only be used in private chats for security reasons.'
            )
        return
    user_id = event.sender_id
    sender = await event.get_sender()
    sender_name = get_display_name(sender)
    if not await is_premium_user(user_id):
        await event.respond(
            "❌ You don't have a premium subscription to transfer.")
        return
    args = event.text.split()
    if len(args) != 2:
        await event.respond(
    "⚙️ **Usage:** `/transfer <user_id>`\n💡 **Example:** `/transfer 123456789`")
        return
    try:
        target_user_id = int(args[1])
    except ValueError:
        await event.respond(
            '❌ Invalid user ID. Please provide a valid numeric user ID.')
        return
    if target_user_id == user_id:
        await event.respond('❌ You cannot transfer premium to yourself.')
        return
    if await is_premium_user(target_user_id):
        await event.respond(
            '❌ The target user already has a premium subscription.')
        return
    try:
        premium_details = await get_premium_details(user_id)
        if not premium_details:
            await event.respond('❌ Error retrieving your premium details.')
            return
        target_name = 'Unknown'
        try:
            target_entity = await bot_client.get_entity(target_user_id)
            target_name = get_display_name(target_entity)
        except Exception as e:
            logger.warning(f'Could not get target user name: {e}')
        now = datetime.now()
        expiry_date = premium_details['subscription_end']
        await premium_users_collection.update_one({'user_id':
            target_user_id}, {'$set': {'user_id': target_user_id,
            'subscription_start': now, 'subscription_end': expiry_date,
            'expireAt': expiry_date, 'transferred_from': user_id,
            'transferred_from_name': sender_name}}, upsert=True)
        await premium_users_collection.delete_one({'user_id': user_id})
        expiry_ist = expiry_date + timedelta(hours=5, minutes=30)
        formatted_expiry = expiry_ist.strftime('%d-%b-%Y %I:%M:%S %p')
        await event.respond(
            f"✅ **Premium Transfer Successful!**\n\n"
            f"Your premium access has been successfully transferred to **{target_name}** (`{target_user_id}`).\n"
            f"Your own premium privileges have now been deactivated."
        )

        try:
            await bot_client.send_message(
                target_user_id,
                f"""🎁 **Premium Subscription Received!**  

            You have received a premium transfer from **{sender_name}** (`{user_id}`).  
            📅 **Valid Until:** {formatted_expiry} _(IST)_  

            Enjoy your premium access! 🚀"""
            )

        except Exception as e:
            logger.error(f'Could not notify target user {target_user_id}: {e}')
        try:
            owner_id = int(OWNER_ID) if isinstance(OWNER_ID, str
                ) else OWNER_ID[0] if isinstance(OWNER_ID, list) else OWNER_ID
            await bot_client.send_message(owner_id,
                f'♻️ Premium Transfer: {sender_name} ({user_id}) has transferred their premium to {target_name} ({target_user_id}). Expiry: {formatted_expiry}'
                )
        except Exception as e:
            logger.error(f'Could not notify owner about premium transfer: {e}')
        return
    except Exception as e:
        logger.error(
            f'Error transferring premium from {user_id} to {target_user_id}: {e}'
            )
        await event.respond(f'❌ Error transferring premium: {str(e)}')
        return
@bot_client.on(events.NewMessage(pattern='/rem'))
async def remove_premium_handler(event):
    user_id = event.sender_id
    if not await is_private_chat(event):
        return
    if user_id not in OWNER_ID:
        return
    args = event.text.split()
    if len(args) != 2:
        await event.respond('Usage: /rem user_id\nExample: /rem 123456789')
        return
    try:
        target_user_id = int(args[1])
    except ValueError:
        await event.respond(
            '❌ Invalid user ID. Please provide a valid numeric user ID.')
        return
    if not await is_premium_user(target_user_id):
        await event.respond(
            f'❌ User {target_user_id} does not have a premium subscription.')
        return
    try:
        target_name = 'Unknown'
        try:
            target_entity = await bot_client.get_entity(target_user_id)
            target_name = get_display_name(target_entity)
        except Exception as e:
            logger.warning(f'Could not get target user name: {e}')
        result = await premium_users_collection.delete_one({'user_id':
            target_user_id})
        if result.deleted_count > 0:
            await event.respond(
                f'✅ Premium subscription successfully removed from {target_name} ({target_user_id}).'
                )
            try:
                await bot_client.send_message(target_user_id,
                    '⚠️ Your premium subscription has been removed by the administrator.'
                    )
            except Exception as e:
                logger.error(
                    f'Could not notify user {target_user_id} about premium removal: {e}'
                    )
        else:
            await event.respond(
                f'❌ Failed to remove premium from user {target_user_id}.')
        return
    except Exception as e:
        logger.error(f'Error removing premium from {target_user_id}: {e}')
        await event.respond(f'❌ Error removing premium: {str(e)}')
        return

# ---------- stats ends here -----------

# ---------- redeem main code starts here -----------
# -------- Collections & Setup (uses same DB as premium_users_collection) --------
redeem_codes_collection = None
redeemed_collection = None

async def _ensure_collections():
    """Ensure redeem collections exist and have indexes."""
    global redeem_codes_collection, redeemed_collection
    if redeem_codes_collection is None or redeemed_collection is None:
        db = premium_users_collection.database  # Motor async DB
        redeem_codes_collection = db["redeem_code"]
        redeemed_collection = db["redeemed"]
        # unique index on code
        try:
            await redeem_codes_collection.create_index("code", unique=True)
        except Exception:
            pass

def _owners_set():
    """Normalize OWNER_ID to a set of ints."""
    if isinstance(OWNER_ID, (list, tuple, set)):
        return set(OWNER_ID)
    return {OWNER_ID}

# -------- Helpers --------
def _gen_code(length: int = 10) -> str:
    """Generate uppercase alphanumeric code of given length."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

def _parse_kv_args(text: str):
    """
    Parse key=value style args (with simple positional fallback).
    Supported keys/aliases:
      - count / c                       (default: 10)
      - days / d / validity_days        (default: 1)
      - source / s                      (default: 'manual')
      - remarks / r / note              (default: '')
    Examples:
      /genCode
      /genCode count=20 days=3 source=promo remarks="Diwali Offer"
      /genCode 15 7 source=partner r=Welcome
    """
    tokens = (text or "").split()
    kv = {}
    positional = []
    for t in tokens[1:]:  # skip the command itself
        if "=" in t:
            k, v = t.split("=", 1)
            kv[k.strip().lower()] = v.strip().strip('"').strip("'")
        else:
            positional.append(t.strip())

    def get_any(*keys, default=None):
        for k in keys:
            if k in kv:
                return kv[k]
        return default

    count = get_any("count", "c")
    days = get_any("days", "d", "validity_days")
    source = get_any("source", "s")
    remarks = get_any("remarks", "r", "note")

    # positional fallback: [count?, days?]
    if positional:
        if count is None and positional and positional[0].isdigit():
            count = positional[0]
        if len(positional) > 1 and days is None and positional[1].isdigit():
            days = positional[1]

    # type sanitize
    try:
        count = int(count) if count is not None else None
    except Exception:
        count = None
    try:
        days = int(days) if days is not None else None
    except Exception:
        days = None

    return {
        "count": count,
        "validity_days": days,
        "source": source,
        "remarks": remarks,
    }

def _format_ist(dt_utc: datetime) -> str:
    return (dt_utc + timedelta(hours=5, minutes=30)).strftime("%d-%b-%Y %I:%M:%S %p (IST)")

# -------- /genCode (Owner-only) --------
@bot_client.on(events.NewMessage(pattern=r"^/genCode(?:\b.*)?$"))
async def gen_code_handler(event):
    """
    Owner-only.
    Usage:
      /genCode
      /genCode count=20 days=3
      /genCode 15 7 source=promo remarks="Holiday Blast"
    Defaults: count=10, days=1
    """
    sender_id = event.sender_id
    if sender_id not in _owners_set():
        await event.respond("❌ You are not allowed to use this command.")
        return

    await _ensure_collections()

    args = _parse_kv_args(event.raw_text or "")
    count = args.get("count") or 10
    validity_days = args.get("validity_days") or 1
    source = (args.get("source") or "manual").strip()
    remarks = (args.get("remarks") or "").strip()

    # clamps
    count = max(1, min(100, count))
    validity_days = max(1, min(365, validity_days))

    try:
        sender = await event.get_sender()
        generated_by_name = get_display_name(sender) or "Unknown"
    except Exception:
        generated_by_name = "Unknown"

    now = datetime.utcnow()
    codes, docs = [], []

    # Pre-generate + collision check
    for _ in range(count):
        code = _gen_code(10)
        # extremely rare collision check
        while await redeem_codes_collection.find_one({"code": code}):
            code = _gen_code(10)
        codes.append(code)
        docs.append({
            "code": code,
            "created_at": now,
            "used": False,
            "validity_days": validity_days,
            "source": source,
            "remarks": remarks,
            "generated_by": {"id": sender_id, "name": generated_by_name},
        })

    if docs:
        await redeem_codes_collection.insert_many(docs)

    preview = "\n".join(codes)
    await event.respond(
        "✅ Generated **{}** codes\n"
        "• validity_days: **{}**\n"
        "• source: **{}**\n"
        "• remarks: **{}**\n\n"
        "```\n{}\n```".format(len(codes), validity_days, source or "-", remarks or "-", preview)
    )

# -------- /redeem (User) --------
@bot_client.on(events.NewMessage(pattern=r"^/redeem(?:\s+(.+))?$"))
async def redeem_handler(event):
    """
    /redeem <CODE>
    Flow:
      1) If already premium -> block & show expiry
      2) Atomically claim code (used=False -> True)
      3) Grant premium for `validity_days`
      4) Log to `redeemed`
    """
    # (Optional) limit to private chat for safety
    if not await is_private_chat(event):
        await event.respond("Use this command in private for your account security.")
        return

    await _ensure_collections()

    user_id = event.sender_id
    parts = (event.raw_text or "").split(maxsplit=1)
    if len(parts) != 2 or not parts[1].strip():
        await event.respond("❌ Usage: /redeem <CODE>\nExample: `/redeem ABC123XYZ0`")
        return
    code = parts[1].strip().upper()
    now = datetime.utcnow()

    # 1) Already premium?
    try:
        premium_details = await get_premium_details(user_id)
    except Exception:
        premium_details = None

    if premium_details:
        expiry_utc = premium_details.get("subscription_end")
        if expiry_utc:
            await event.respond(
                "💎 You already have an active premium subscription.\n"
                f"⏳ Valid until: {_format_ist(expiry_utc)}\n"
                "ℹ️ Redeeming a new code isn’t necessary right now."
            )
        else:
            await event.respond("💎 You already have an active premium subscription.")
        return

    # 2) Atomically claim code (not used)
    claim = await redeem_codes_collection.find_one_and_update(
        {"code": code, "used": False},
        {"$set": {"used": True, "used_by": user_id, "used_at": now}},
        return_document=ReturnDocument.AFTER,
    )

    if not claim:
        existing = await redeem_codes_collection.find_one({"code": code})
        if not existing:
            await event.respond("❌ **Code Not Found**\nPlease double-check the code and try again.")
        else:
            msg = "❌ **Code Already Used**"
            ub = existing.get("used_by")
            if ub:
                msg += f"\n👤 **Used By:** `{ub}`"
            await event.respond(msg)
        return

    # 3) Grant premium
    validity_days = int(claim.get("validity_days", 1))
    validity_days = max(1, min(365, validity_days))
    sub_start = now
    sub_end = now + timedelta(days=validity_days)

    try:
        await premium_users_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "user_id": user_id,
                "subscription_start": sub_start,
                "subscription_end": sub_end,
                "expireAt": sub_end
            }},
            upsert=True
        )

        # 4) Log redeemed snapshot
        await redeemed_collection.insert_one({
            "user_id": user_id,
            "code": code,
            "redeemed_at": now,
            "validity_days": validity_days,
            "premium_start": sub_start,
            "premium_end": sub_end,
            "source": claim.get("source"),
            "remarks": claim.get("remarks"),
            "generated_by": claim.get("generated_by"),
        })

        expiry_text = _format_ist(sub_end)
        await event.respond(
            f"✅ Successfully redeemed `{code}`.\n"
            f"🎟️ You have been granted *{validity_days} day(s)* premium access until {expiry_text}."
        )

        # notify owners (best-effort)
        for o in _owners_set():
            try:
                await bot_client.send_message(
                o,
                f"♻️ **Code Redeemed By an User!**\n\n"
                f"**User:** `{user_id}`\n"
                f"**Code:** `{code}`\n"
                f"**Validity:** {validity_days} days\n"
                f"**Source:** {claim.get('source') or '-'}\n"
                f"**Premium Valid Until:** {expiry_text}"
            )

            except Exception:
                pass

    except Exception as e:
        # revert claim on failure (so code isn't lost)
        try:
            await redeem_codes_collection.update_one(
                {"code": code},
                {"$set": {"used": False}, "$unset": {"used_by": "", "used_at": ""}},
            )
        except Exception:
            pass
        await event.respond("❌ Internal error while applying premium. Please contact admin.")
        return