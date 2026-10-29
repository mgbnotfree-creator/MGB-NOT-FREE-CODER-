import asyncio
import aiohttp
import random
import string
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
import pyromod.listen  

# ================= 1. CONFIGURATIONS =================
API_ID = "YOUR_API_ID"              
API_HASH = "YOUR_API_HASH"          
BOT_TOKEN = "YOUR_BOT_TOKEN"        
ADMIN_ID = 123456789                # Apna Telegram User ID yahan zaroor dalein

SMM_URL = "https://ldrsmm.com/api/v2"
SMM_KEY = "801c7386e0a5838dcd35051915500f0a"  

PROFIT_MARGIN = 40  
MULTIPLIER = 1 + (PROFIT_MARGIN / 100)  

MONGO_URI = "mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority"
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client["bot2_database"]  
users_col = db["users"]
orders_col = db["orders"]

app = Client("smm_pro_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ================= 2. MENUS & KEYBOARDS =================
main_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🛒 New Order"), KeyboardButton("🧾 All Services")],
        [KeyboardButton("💻 Profile"), KeyboardButton("🧾 Order History")],
        [KeyboardButton("💲 Referral"), KeyboardButton("💲 Add Funds")]
    ],
    resize_keyboard=True
)

# ================= 3. API HELPER FUNCTIONS =================
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

# ================= 4. USER COMMANDS =================
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
        await users_col.insert_one({"_id": user_id, "balance": 0.0, "referred_by": ref_id})
        
        if ref_id and ref_id != user_id:
            await users_col.update_one({"_id": ref_id}, {"$inc": {"balance": 10.0}})
            try:
                await client.send_message(ref_id, "𓆩♛𓆪 **Referral Success!** 10 Coins added to your account.")
            except:
                pass
                
    welcome_text = (
        "𓆩♛𓆪 **Premium SMM Bot (Advanced)** 𓆩♛𓆪\n\n"
        "💻 Grow your Telegram, Instagram & YouTube instantly.\n"
        "💲 **1 Coin = ₹1**\n\n"
        "🧾 Please select an option below:"
    )
    await message.reply_text(welcome_text, reply_markup=main_menu)

@app.on_message(filters.regex("💻 Profile") & filters.private)
async def profile_handler(client, message):
    user = await users_col.find_one({"_id": message.from_user.id})
    bal = round(user.get("balance", 0.0), 2)
    await message.reply_text(f"💻 **User Profile**\n\n💻 **ID:** `{message.from_user.id}`\n🪙 **Balance:** {bal} Coins")

@app.on_message(filters.regex("💲 Add Funds") & filters.private)
async def funds_handler(client, message):
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
        [InlineKeyboardButton("💲 Approve & Add Balance", callback_data=f"apprv_{message.from_user.id}_{amount}")],
        [InlineKeyboardButton("⏳ Reject Payment", callback_data=f"rej_{message.from_user.id}")]
    ])
    
    await client.send_message(ADMIN_ID, admin_text, reply_markup=buttons)

@app.on_message(filters.regex("💲 Referral") & filters.private)
async def referral_handler(client, message):
    bot = await client.get_me()
    link = f"https://t.me/{bot.username}?start=ref_{message.from_user.id}"
    await message.reply_text(f"💲 **Refer & Earn**\n\n💻 Invite friends and get **10 Coins** when they start!\n\n💻 Your Link:\n`{link}`")

@app.on_message(filters.regex("🧾 All Services") & filters.private)
async def services_handler(client, message):
    proc = await message.reply_text("⏳ Fetching live services with updated pricing...")
    services = await smm_request("services")
    
    if isinstance(services, dict) and "error" in services:
        return await proc.edit_text("⏳ API Error. Please try again later.")
        
    text = "𓆩♛𓆪 **Top Services (Live Pricing + 40% Margin)** 𓆩♛𓆪\n\n"
    
    for srv in services[:15]:
        retail_price = round(float(srv['rate']) * MULTIPLIER, 2)
        text += f"💻 **ID:** `{srv['service']}` | {srv['name']}\n"
        text += f"💲 Rate (per 1000): **{retail_price} Coins**\n"
        text += f"🧾 Min: {srv['min']} | Max: {srv['max']}\n"
        text += "🧾🧾🧾🧾🧾🧾🧾🧾\n"
        
    await proc.edit_text(text)

@app.on_message(filters.regex("🧾 Order History") & filters.private)
async def history_handler(client, message):
    cursor = orders_col.find({"user_id": message.from_user.id}).sort("timestamp", -1).limit(5)
    orders = await cursor.to_list(length=5)
    
    if not orders:
        return await message.reply_text("⏳ No orders found.")
        
    text = "🧾 **Last 5 Orders:**\n\n"
    for ord in orders:
        text += f"💻 **ID:** `#{ord['internal_id']}` | 🧾 **Qty:** {ord['qty']}\n"
        text += f"💲 **Cost:** {ord['cost']} Coins | 𓆩♛𓆪 **Status:** Sent to Server\n"
        text += f"💻 **Link:** {ord['link']}\n\n"
    await message.reply_text(text)

# ================= 5. ADVANCED ORDER PLACEMENT =================
@app.on_message(filters.regex("🛒 New Order") & filters.private)
async def place_order_flow(client, message):
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
        
    retail_rate = round(float(target_service['rate']) * MULTIPLIER, 2)
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
    await users_col.update_one({"_id": user_id}, {"$inc": {"balance": -total_cost}})
    
    await orders_col.insert_one({
        "internal_id": internal_id,
        "panel_id": order_resp.get("order", "N/A"),
        "user_id": user_id,
        "service_id": service_id,
        "link": target_link,
        "qty": qty,
        "cost": total_cost,
        "timestamp": message.date
    })
    
    await final_proc.edit_text(
        f"𓆩♛𓆪 **Order Placed Successfully!** 𓆩♛𓆪\n\n"
        f"💻 **Order ID:** `#{internal_id}`\n"
        f"🧾 **Service:** {target_service['name']}\n"
        f"🧾 **Quantity:** {qty}\n"
        f"🪙 **Total Cost:** {total_cost} Coins"
    )

# ================= 6. ADMIN PAYMENT APPROVAL & COMMANDS =================
@app.on_callback_query(filters.regex(r"^apprv_"))
async def approve_payment(client, callback_query):
    if callback_query.from_user.id != ADMIN_ID:
        return await callback_query.answer("⏳ Not allowed", show_alert=True)

    data = callback_query.data.split("_")
    user_id = int(data[1])
    amount = float(data[2])

    await users_col.update_one({"_id": user_id}, {"$inc": {"balance": amount}}, upsert=True)
    await callback_query.message.edit_text(f"{callback_query.message.text}\n\n𓆩♛𓆪 **Status: Payment Approved** 💲")
    
    try:
        await client.send_message(user_id, f"𓆩♛𓆪 **Payment Approved!**\n\n🪙 {amount} Coins have been added to your account.")
    except:
        pass

@app.on_callback_query(filters.regex(r"^rej_"))
async def reject_payment(client, callback_query):
    if callback_query.from_user.id != ADMIN_ID:
        return

    data = callback_query.data.split("_")
    user_id = int(data[1])

    await callback_query.message.edit_text(f"{callback_query.message.text}\n\n⏳ **Status: Payment Rejected**")
    try:
        await client.send_message(user_id, f"⏳ **Payment Rejected!**\n\n💻 Your UTR could not be verified. Please contact Admin.")
    except:
        pass

@app.on_message(filters.command("addbalance") & filters.user(ADMIN_ID))
async def add_balance_admin(client, message):
    try:
        _, target_id, amount = message.text.split()
        target_id, amount = int(target_id), float(amount)
        
        await users_col.update_one({"_id": target_id}, {"$inc": {"balance": amount}}, upsert=True)
        await message.reply_text(f"𓆩♛𓆪 Successfully added {amount} coins to User `{target_id}`.")
        
        try:
            await client.send_message(target_id, f"💲 **Admin added {amount} Coins to your account!**")
        except:
            pass
    except Exception:
        await message.reply_text("💻 Syntax: `/addbalance user_id amount`")

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID))
async def broadcast_admin(client, message):
    msg_text = message.text.replace("/broadcast ", "")
    if not msg_text or msg_text == "/broadcast":
        return await message.reply_text("💻 Please provide a message to broadcast.")
        
    users = await users_col.find({}).to_list(length=None)
    success, failed = 0, 0
    
    proc = await message.reply_text("⏳ Broadcasting message to all users...")
    for u in users:
        try:
            await client.send_message(u["_id"], f"𓆩♛𓆪 **Announcement** 𓆩♛𓆪\n\n{msg_text}")
            success += 1
            await asyncio.sleep(0.1) 
        except:
            failed += 1
            
    await proc.edit_text(f"𓆩♛𓆪 **Broadcast Complete!**\n\n💻 Delivered: {success}\n⏳ Failed: {failed}")

@app.on_message(filters.command("panel_balance") & filters.user(ADMIN_ID))
async def check_admin_panel_balance(client, message):
    resp = await smm_request("balance")
    if "balance" in resp:
        await message.reply_text(f"💲 **Provider Panel Balance:** {resp['balance']} {resp.get('currency', 'INR')}")
    else:
        await message.reply_text(f"⏳ Error fetching panel balance: {resp}")

if __name__ == "__main__":
    print("💻 Advanced SMM Bot Started Successfully!")
    app.run()
