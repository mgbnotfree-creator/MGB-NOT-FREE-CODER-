import os
import asyncio
import aiohttp
import random
import string
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pyrogram import Client, filters, idle
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
import pyromod.listen  

# Securely load .env variables
load_dotenv()

# ================= 1. CONFIGURATIONS =================
API_ID = int(os.getenv("API_ID", 0))              
API_HASH = os.getenv("API_HASH", "")          
BOT_TOKEN = os.getenv("BOT_TOKEN", "")        
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))                

SMM_URL = "https://ldrsmm.com/api/v2"
SMM_KEY = os.getenv("SMM_KEY", "")  

# Base Margins
NORMAL_MARGIN = 40  
VIP_MARGIN = 20     

MONGO_URI = os.getenv("MONGO_URI", "")
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client["bot2_database"]  
users_col = db["users"]
orders_col = db["orders"]
promos_col = db["promos"]
tickets_col = db["tickets"]

app = Client("smm_pro_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ================= 2. MENUS & KEYBOARDS =================
main_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🛒 New Order"), KeyboardButton("🧾 All Services")],
        [KeyboardButton("💻 Profile"), KeyboardButton("🧾 Order History")],
        [KeyboardButton("💲 Add Funds"), KeyboardButton("💲 Referral")],
        [KeyboardButton("🪙 Daily Bonus"), KeyboardButton("🔍 Track Order")],
        [KeyboardButton("🔄 Check Refund"), KeyboardButton("🎧 Support")]
    ],
    resize_keyboard=True
)

# ================= 3. API & HELPER FUNCTIONS =================
async def smm_request(action: str, payload_data: dict = None):
    if payload_data is None:
        payload_data = {}
    payload = {"key": SMM_KEY, "action": action}
    payload.update(payload_data)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(SMM_URL, data=payload) as resp:
                return await resp.json()
        except Exception as e:
            return {"error": str(e)}

def generate_order_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

async def get_multiplier(user_id):
    user = await users_col.find_one({"_id": user_id})
    if user and user.get("is_vip", False):
        return 1 + (VIP_MARGIN / 100)
    return 1 + (NORMAL_MARGIN / 100)

async def auto_clean(message):
    """Auto-Clean / Ghost Mode: Deletes user message to keep chat clean"""
    try:
        await message.delete()
    except:
        pass

# ================= 4. BACKGROUND TASKS (Auto-Alert) =================
async def order_status_checker():
    """Background task to check pending orders and alert users when completed"""
    while True:
        await asyncio.sleep(300) # Checks every 5 minutes
        pending_orders = await orders_col.find({"last_known_status": {"$in": ["pending", "processing", "in progress"]}}).to_list(100)
        
        for ord in pending_orders:
            panel_id = ord.get("panel_id")
            if panel_id == "N/A": continue
            
            resp = await smm_request("status", {"order": panel_id})
            if "status" in resp:
                new_status = resp["status"].lower()
                if new_status != ord.get("last_known_status"):
                    await orders_col.update_one({"_id": ord["_id"]}, {"$set": {"last_known_status": new_status}})
                    
                    if new_status == "completed":
                        try:
                            await app.send_message(ord["user_id"], f"𓆩♛𓆪 **Auto-Alert: Order Completed!** 𓆩♛𓆪\n\n💻 Your Order `#{ord['internal_id']}` has been successfully completed by the server.")
                        except:
                            pass

# ================= 5. CORE COMMANDS =================
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    ref_id = None
    if len(message.command) > 1 and message.command[1].startswith("ref_"):
        try:
            ref_id = int(message.command[1].split("_")[1])
        except ValueError:
            pass

    user = await users_col.find_one({"_id": user_id})
    if not user:
        await users_col.insert_one({
            "_id": user_id, 
            "balance": 0.0, 
            "total_spent": 0.0,
            "referred_by": ref_id, 
            "last_bonus": None,
            "is_vip": False
        })
        if ref_id and ref_id != user_id:
            await users_col.update_one({"_id": ref_id}, {"$inc": {"balance": 10.0}})
            try:
                await client.send_message(ref_id, "𓆩♛𓆪 **Referral Success!** 10 Coins added to your account.")
            except:
                pass
                
    welcome_text = (
        "𓆩♛𓆪 **Premium SMM Bot (Ultimate)** 𓆩♛𓆪\n\n"
        "💻 Grow your Telegram, Instagram & YouTube instantly.\n"
        "💲 **1 Coin = ₹1**\n\n"
        "🧾 Please select an option below:"
    )
    await message.reply_text(welcome_text, reply_markup=main_menu)

@app.on_message(filters.regex("💻 Profile") & filters.private)
async def profile_handler(client, message):
    await auto_clean(message)
    user = await users_col.find_one({"_id": message.from_user.id})
    bal = round(user.get("balance", 0.0), 2)
    spent = round(user.get("total_spent", 0.0), 2)
    vip_status = "VIP Member" if user.get("is_vip") else "Normal User"
    
    text = (
        f"💻 **User Profile**\n\n"
        f"💻 **ID:** `{message.from_user.id}`\n"
        f"🪙 **Balance:** {bal} Coins\n"
        f"🛒 **Total Spent:** {spent} Coins\n"
        f"𓆩♛𓆪 **Account Type:** {vip_status}\n\n"
        f"💲 **Redeem Promo:** `/redeem CODE`\n"
        f"🔄 **Refill Order:** `/refill ORDER_ID`\n"
        f"💸 **Transfer Funds:** `/transfer USER_ID AMOUNT`"
    )
    await message.reply_text(text)

@app.on_message(filters.regex("💲 Add Funds") & filters.private)
async def funds_handler(client, message):
    await auto_clean(message)
    text = (
        "💲 **Add Balance (UPI)**\n\n"
        "💻 Scan the QR Code above to pay.\n"
        "💻 After successful payment, please enter your details below.\n"
    )
    qr_url = "https://github.com/user-attachments/assets/52db898f-cd48-402b-863b-4226ec462f1c"
    await message.reply_photo(photo=qr_url, caption=text)

    amt_msg = await message.chat.ask("🪙 How much amount did you pay? (Example: 50):", timeout=120)
    if not amt_msg.text.isdigit():
        return await message.reply_text("⏳ Invalid amount. Request cancelled.")
    amount = int(amt_msg.text)

    utr_msg = await message.chat.ask("🧾 Enter the 12-digit UTR or Reference Number of your payment:", timeout=120)
    utr = utr_msg.text.strip()

    await message.reply_text("⏳ Your payment details have been sent to the Admin. Balance will be added after verification.")

    admin_text = (
        "𓆩♛𓆪 **New Payment Verification** 𓆩♛𓆪\n\n"
        f"💻 **User ID:** `{message.from_user.id}`\n"
        f"🪙 **Amount Paid:** {amount}\n"
        f"🧾 **UTR Number:** `{utr}`\n\n"
        "💻 Please verify in your bank and click Approve."
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💲 Approve & Add", callback_data=f"apprv_{message.from_user.id}_{amount}")],
        [InlineKeyboardButton("⏳ Reject", callback_data=f"rej_{message.from_user.id}")]
    ])
    await client.send_message(ADMIN_ID, admin_text, reply_markup=buttons)

@app.on_message(filters.regex("🧾 All Services") & filters.private)
async def services_handler(client, message):
    await auto_clean(message)
    proc = await message.reply_text("⏳ Fetching live services with your account rates...")
    services = await smm_request("services")
    
    if isinstance(services, dict) and "error" in services:
        return await proc.edit_text("⏳ API Error. Please try again later.")
        
    multiplier = await get_multiplier(message.from_user.id)
    text = "𓆩♛𓆪 **Top Services (Live Pricing)** 𓆩♛𓆪\n\n"
    
    for srv in services[:15]:
        retail_price = round(float(srv['rate']) * multiplier, 2)
        text += f"💻 **ID:** `{srv['service']}` | {srv['name']}\n"
        text += f"💲 Rate (per 1000): **{retail_price} Coins**\n"
        text += f"🧾 Min: {srv['min']} | Max: {srv['max']}\n"
        text += "🧾🧾🧾🧾🧾🧾🧾🧾\n"
    await proc.edit_text(text)

# ================= 6. NEW PREMIUM FEATURES =================

@app.on_message(filters.command("leaderboard") & filters.private)
async def show_leaderboard(client, message):
    await auto_clean(message)
    top_users = await users_col.find().sort("total_spent", -1).limit(5).to_list(5)
    text = "𓆩♛𓆪 **Top 5 VIP Spenders** 𓆩♛𓆪\n\n"
    for i, u in enumerate(top_users):
        text += f"**{i+1}.** 💻 User `{u['_id']}` - 🪙 {round(u.get('total_spent', 0), 2)} Coins\n"
    await message.reply_text(text)

@app.on_message(filters.command("transfer") & filters.private)
async def transfer_funds(client, message):
    await auto_clean(message)
    try:
        _, receiver_id, amount = message.text.split()
        receiver_id = int(receiver_id)
        amount = float(amount)
    except:
        return await message.reply_text("💻 Syntax: `/transfer USER_ID AMOUNT`")
        
    if amount <= 0:
        return await message.reply_text("⏳ Invalid amount.")
        
    sender_id = message.from_user.id
    if sender_id == receiver_id:
        return await message.reply_text("⏳ You cannot transfer to yourself.")
        
    sender = await users_col.find_one({"_id": sender_id})
    if sender.get("balance", 0) < amount:
        return await message.reply_text("⏳ Insufficient balance for transfer.")
        
    receiver = await users_col.find_one({"_id": receiver_id})
    if not receiver:
        return await message.reply_text("⏳ Receiver ID not found in database.")
        
    await users_col.update_one({"_id": sender_id}, {"$inc": {"balance": -amount}})
    await users_col.update_one({"_id": receiver_id}, {"$inc": {"balance": amount}})
    
    await message.reply_text(f"𓆩♛𓆪 **Transfer Successful!**\n\n🪙 Sent {amount} Coins to User `{receiver_id}`.")
    try:
        await client.send_message(receiver_id, f"𓆩♛𓆪 **Funds Received!**\n\n🪙 You received {amount} Coins from User `{sender_id}`.")
    except:
        pass

@app.on_message(filters.regex("🔄 Check Refund") & filters.private)
async def check_refund(client, message):
    await auto_clean(message)
    proc = await message.reply_text("⏳ Scanning your pending orders for refunds...")
    user_id = message.from_user.id
    
    orders = await orders_col.find({"user_id": user_id, "status_refunded": {"$ne": True}}).to_list(50)
    if not orders:
        return await proc.edit_text("⏳ No eligible orders found for refund scan.")

    total_refund = 0.0
    refunded_ids = []

    for ord in orders:
        panel_id = ord.get("panel_id")
        if panel_id == "N/A": continue
            
        status_resp = await smm_request("status", {"order": panel_id})
        if "error" in status_resp or "status" not in status_resp: continue

        status = status_resp["status"].lower()
        if status == "canceled":
            refund_amt = ord["cost"]
            total_refund += refund_amt
            await orders_col.update_one({"_id": ord["_id"]}, {"$set": {"status_refunded": True}})
            refunded_ids.append(ord['internal_id'])
            
        elif status == "partial":
            remains = float(status_resp.get("remains", 0))
            if remains > 0:
                qty = float(ord["qty"])
                refund_amt = round((remains / qty) * ord["cost"], 2)
                total_refund += refund_amt
                await orders_col.update_one({"_id": ord["_id"]}, {"$set": {"status_refunded": True}})
                refunded_ids.append(ord['internal_id'])
    
    if total_refund > 0:
        await users_col.update_one({"_id": user_id}, {"$inc": {"balance": total_refund}})
        text = (
            f"𓆩♛𓆪 **Refund Successful!** 𓆩♛𓆪\n\n"
            f"🪙 **Amount Added:** {total_refund} Coins\n"
            f"🧾 **Orders Refunded:** {', '.join(refunded_ids)}"
        )
        await proc.edit_text(text)
    else:
        await proc.edit_text("⏳ All your orders are running fine. No refunds required.")

# ================= 7. ADVANCED ORDER PLACEMENT =================
@app.on_message(filters.regex("🛒 New Order") & filters.private)
async def place_order_flow(client, message):
    await auto_clean(message)
    user_id = message.from_user.id
    
    srv_msg = await message.chat.ask("🧾 Please enter the **Service ID** you want to order:\n*(Check 'All Services' for IDs)*", timeout=120)
    service_id = srv_msg.text.strip()
    if not service_id.isdigit():
        return await message.reply_text("⏳ Invalid ID. Order Cancelled.")
        
    proc = await message.reply_text("⏳ Verifying service...")
    services = await smm_request("services")
    
    target_service = next((s for s in services if str(s['service']) == service_id), None)
    if not target_service:
        return await proc.edit_text("⏳ Service ID not found. Order Cancelled.")
        
    multiplier = await get_multiplier(user_id)
    retail_rate = round(float(target_service['rate']) * multiplier, 2)
    min_qty, max_qty = int(target_service['min']), int(target_service['max'])
    await proc.delete()

    link_msg = await message.chat.ask(f"💻 Send the target link for **{target_service['name']}**:", timeout=120)
    target_link = link_msg.text.strip()

    qty_msg = await message.chat.ask(f"🧾 Enter Quantity (Min: {min_qty}, Max: {max_qty}):", timeout=120)
    if not qty_msg.text.isdigit():
        return await message.reply_text("⏳ Invalid Quantity.")
    qty = int(qty_msg.text)
    if qty < min_qty or qty > max_qty:
        return await message.reply_text(f"⏳ Quantity must be between {min_qty} and {max_qty}.")
        
    total_cost = round((qty / 1000) * retail_rate, 2)
    user = await users_col.find_one({"_id": user_id})
    if user.get("balance", 0) < total_cost:
        return await message.reply_text(f"⏳ Insufficient Balance.\n\n💲 Cost: {total_cost} Coins\n🪙 Your Balance: {round(user.get('balance',0),2)} Coins")

    final_proc = await message.reply_text("⏳ Placing your order on the server...")
    order_resp = await smm_request("add", {"service": service_id, "link": target_link, "quantity": qty})
    
    if "error" in order_resp:
        return await final_proc.edit_text(f"⏳ API Error: {order_resp['error']}\n*Your coins were not deducted.*")
        
    internal_id = generate_order_id()
    # Deduct balance and increase total_spent for leaderboard
    await users_col.update_one({"_id": user_id}, {"$inc": {"balance": -total_cost, "total_spent": total_cost}})
    
    await orders_col.insert_one({
        "internal_id": internal_id,
        "panel_id": order_resp.get("order", "N/A"),
        "user_id": user_id,
        "service_id": service_id,
        "link": target_link,
        "qty": qty,
        "cost": total_cost,
        "last_known_status": "pending",
        "status_refunded": False,
        "timestamp": message.date
    })
    
    await final_proc.edit_text(
        f"𓆩♛𓆪 **Order Placed Successfully!** 𓆩♛𓆪\n\n"
        f"💻 **Order ID:** `#{internal_id}`\n"
        f"🧾 **Service:** {target_service['name']}\n"
        f"🧾 **Quantity:** {qty}\n"
        f"🪙 **Total Cost:** {total_cost} Coins\n\n"
        f"🔍 You will be notified automatically when completed."
    )

# ================= 8. STANDARD FEATURES (History, Bonus, Tickets) =================
@app.on_message(filters.regex("🪙 Daily Bonus") & filters.private)
async def daily_bonus(client, message):
    await auto_clean(message)
    user_id = message.from_user.id
    user = await users_col.find_one({"_id": user_id})
    now = datetime.utcnow()
    last_bonus = user.get("last_bonus")

    if last_bonus and now < last_bonus + timedelta(days=1):
        wait_time = (last_bonus + timedelta(days=1)) - now
        hours, remainder = divmod(int(wait_time.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        return await message.reply_text(f"⏳ Come back in {hours}h {minutes}m.")

    bonus_amount = random.randint(1, 5)
    await users_col.update_one({"_id": user_id}, {"$set": {"last_bonus": now}, "$inc": {"balance": bonus_amount}})
    await message.reply_text(f"𓆩♛𓆪 **Daily Bonus Claimed!** 𓆩♛𓆪\n\n🪙 You received **{bonus_amount} Coins** today.")

@app.on_message(filters.regex("🔍 Track Order") & filters.private)
async def track_order_flow(client, message):
    await auto_clean(message)
    track_msg = await message.chat.ask("🧾 Enter your Order ID (For example: AB12CD3):", timeout=60)
    order_id = track_msg.text.strip().replace("#", "")
    order = await orders_col.find_one({"internal_id": order_id, "user_id": message.from_user.id})
    if not order:
        return await message.reply_text("⏳ Order ID not found.")

    proc = await message.reply_text("⏳ Fetching live status...")
    if order.get("panel_id") == "N/A":
        return await proc.edit_text("⏳ Status unavailable.")

    status_resp = await smm_request("status", {"order": order.get("panel_id")})
    status = status_resp.get("status", "Unknown").capitalize()
    remains = status_resp.get("remains", "N/A")

    await proc.edit_text(f"𓆩♛𓆪 **Live Status** 𓆩♛𓆪\n\n💻 **ID:** `#{order_id}`\n🧾 **Status:** **{status}**\n⏳ **Remaining:** {remains}")

@app.on_message(filters.regex("🧾 Order History") & filters.private)
async def history_handler(client, message):
    await auto_clean(message)
    cursor = orders_col.find({"user_id": message.from_user.id}).sort("timestamp", -1).limit(5)
    orders = await cursor.to_list(length=5)
    if not orders:
        return await message.reply_text("⏳ No orders found.")
    text = "🧾 **Last 5 Orders:**\n\n"
    for ord in orders:
        text += f"💻 **ID:** `#{ord['internal_id']}` | 🧾 **Qty:** {ord['qty']}\n💲 **Cost:** {ord['cost']} Coins\n💻 **Link:** {ord['link']}\n\n"
    await message.reply_text(text)

@app.on_message(filters.regex("🎧 Support") & filters.private)
async def support_ticket(client, message):
    await auto_clean(message)
    query_msg = await message.chat.ask("🎧 Please describe your issue or question in one message:", timeout=300)
    user_query = query_msg.text
    
    ticket_id = generate_order_id()
    await tickets_col.insert_one({"ticket_id": ticket_id, "user_id": message.from_user.id, "query": user_query})
    await message.reply_text(f"𓆩♛𓆪 **Ticket Created!**\n\n💻 **Ticket ID:** `#{ticket_id}`\n⏳ Admin will reply to you shortly.")
    
    admin_text = (
        f"🎧 **New Support Ticket** 🎧\n\n"
        f"💻 **User ID:** `{message.from_user.id}`\n"
        f"🧾 **Ticket ID:** `#{ticket_id}`\n"
        f"✉️ **Message:**\n{user_query}"
    )
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("💻 Reply to User", callback_data=f"replytk_{message.from_user.id}_{ticket_id}")]])
    await client.send_message(ADMIN_ID, admin_text, reply_markup=buttons)

@app.on_message(filters.regex("💲 Referral") & filters.private)
async def referral_handler(client, message):
    await auto_clean(message)
    bot = await client.get_me()
    await message.reply_text(f"💲 **Refer & Earn**\n\n💻 Get 10 Coins per invite:\n`https://t.me/{bot.username}?start=ref_{message.from_user.id}`")

# ================= 9. ADMIN SYSTEM & CONTROLS =================

@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def admin_stats(client, message):
    await auto_clean(message)
    total_users = await users_col.count_documents({})
    total_orders = await orders_col.count_documents({})
    pipeline = [{"$group": {"_id": None, "total_balance": {"$sum": "$balance"}}}]
    bal_result = await users_col.aggregate(pipeline).to_list(1)
    total_balance = bal_result[0]["total_balance"] if bal_result else 0
    
    await message.reply_text(
        f"𓆩♛𓆪 **Dashboard** 𓆩♛𓆪\n\n"
        f"💻 **Users:** {total_users}\n"
        f"🛒 **Orders:** {total_orders}\n"
        f"🪙 **Liabilities (Users Bal):** {round(total_balance, 2)} Coins"
    )

@app.on_message(filters.command("setvip") & filters.user(ADMIN_ID))
async def set_vip_status(client, message):
    await auto_clean(message)
    try:
        _, target_id, status = message.text.split()
        target_id = int(target_id)
        is_vip = status.lower() == "true"
        
        await users_col.update_one({"_id": target_id}, {"$set": {"is_vip": is_vip}}, upsert=True)
        status_text = "VIP (20% Margin)" if is_vip else "Normal (40% Margin)"
        await message.reply_text(f"𓆩♛𓆪 User `{target_id}` is now set to **{status_text}**.")
        
        try:
            msg = "𓆩♛𓆪 **Congratulations! You are now a VIP Member.**" if is_vip else "⏳ Your VIP status has been removed."
            await client.send_message(target_id, msg)
        except:
            pass
    except:
        await message.reply_text("💻 Syntax: `/setvip USER_ID True` or `/setvip USER_ID False`")

@app.on_message(filters.command("createpromo") & filters.user(ADMIN_ID))
async def create_promo(client, message):
    await auto_clean(message)
    try:
        _, code, amount, uses = message.text.split()
        amount = float(amount)
        uses = int(uses)
        await promos_col.insert_one({"code": code.upper(), "amount": amount, "uses": uses, "used_by": []})
        await message.reply_text(f"𓆩♛𓆪 **Promo Code Created!**\n\n💻 Code: `{code.upper()}`\n🪙 Amount: {amount}\n🧾 Max Uses: {uses}")
    except:
        await message.reply_text("💻 Syntax: `/createpromo CODE AMOUNT USES`")

@app.on_callback_query(filters.regex(r"^apprv_"))
async def approve_payment(client, callback_query):
    if callback_query.from_user.id != ADMIN_ID: return
    data = callback_query.data.split("_")
    user_id, amount = int(data[1]), float(data[2])
    await users_col.update_one({"_id": user_id}, {"$inc": {"balance": amount}}, upsert=True)
    await callback_query.message.edit_text(f"{callback_query.message.text}\n\n𓆩♛𓆪 **Status: Payment Approved** 💲")
    try: await client.send_message(user_id, f"𓆩♛𓆪 **Payment Approved!**\n\n🪙 {amount} Coins added.")
    except: pass

@app.on_callback_query(filters.regex(r"^rej_"))
async def reject_payment(client, callback_query):
    if callback_query.from_user.id != ADMIN_ID: return
    user_id = int(callback_query.data.split("_")[1])
    await callback_query.message.edit_text(f"{callback_query.message.text}\n\n⏳ **Status: Payment Rejected**")
    try: await client.send_message(user_id, f"⏳ **Payment Rejected!**\n\n💻 Please contact Admin.")
    except: pass

@app.on_callback_query(filters.regex(r"^replytk_"))
async def admin_reply_ticket(client, callback_query):
    if callback_query.from_user.id != ADMIN_ID: return
    data = callback_query.data.split("_")
    user_id, ticket_id = int(data[1]), data[2]
    reply_msg = await client.ask(ADMIN_ID, f"⌨️ Reply for Ticket `#{ticket_id}`:", timeout=120)
    try:
        await client.send_message(user_id, f"🎧 **Admin Reply (Ticket `#{ticket_id}`)** 🎧\n\n{reply_msg.text}")
        await callback_query.message.edit_text(f"{callback_query.message.text}\n\n𓆩♛𓆪 **Replied:** {reply_msg.text}")
    except:
        await reply_msg.reply_text("⏳ Failed. User blocked the bot.")
        
# ================= 10. MAIN START =================
async def main():
    await app.start()
    print("💻 Ultimate VIP SMM Bot Started Successfully!")
    
    # Start Background Alert Task
    asyncio.create_task(order_status_checker())
    
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())
