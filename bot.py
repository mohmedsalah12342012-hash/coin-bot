import sqlite3
import discord
from discord.ext import commands

# إعداد قاعدة البيانات
db = sqlite3.connect("economy.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    wallet INTEGER DEFAULT 0,
    bank INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS shop (
    item_name TEXT PRIMARY KEY,
    price INTEGER
)
""")
db.commit()

# إعدادات البوت
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="", intents=intents)

# ----------------------------------------------------
# ضع هنا آي دي (ID) الروم المسموح للبوت العمل فيه فقط
ALLOWED_CHANNEL_ID = 1558280051546529853
# ----------------------------------------------------


# التحقق من أن الرسالة في الروم المسموح به فقط
@bot.check
async def globally_block_channels(ctx):
  if ctx.channel.id != ALLOWED_CHANNEL_ID:
    # يمكنك إلغاء تعليق السطر التالي إذا أردت أن يرد البوت بتنبيه، أو اتركه صامتاً
    # await ctx.send("هذا البوت مخصص للعمل في روم معين فقط!", delete_after=5)
    return False
  return True


@bot.event
async def on_ready():
  print(f"البوت يعمل الآن باسم {bot.user}")


def get_user(user_id):
  cursor.execute(
      "SELECT wallet, bank FROM users WHERE user_id = ?", (user_id,)
  )
  result = cursor.fetchone()
  if result is None:
    cursor.execute(
        "INSERT INTO users (user_id, wallet, bank) VALUES (?, 100, 0)",
        (user_id,),
    )
    db.commit()
    return 100, 0
  return result[0], result[1]


# 1. أمر الأوامر (لعرض قائمة الأوامر المتاحة)
@bot.command(name="الاوامر")
async def help_command(ctx):
  embed = discord.Embed(
      title="قائمة أوامر البوت",
      description="إليك الأوامر المتاحة للاستخدام في السيرفر:",
      color=discord.Color.blue(),
  )
  embed.add_field(name="الرصيد", value="لعرض رصيدك في المحفظة والبنك", inline=False)
  embed.add_field(name="عمل", value="للذهاب للعمل وكسب المال", inline=False)
  embed.add_field(
      name="تحويل @الشخص المبلغ",
      value="تحويل أموال لعضو آخر",
      inline=False,
  )
  embed.add_field(name="المتجر", value="عرض السلع المتاحة للشراء", inline=False)
  embed.add_field(
      name="اضافة_متجر السلعة السعر",
      value="إضافة سلعة جديدة (للمشرفين فقط)",
      inline=False,
  )
  await ctx.send(embed=embed)


# 2. أمر الرصيد
@bot.command(name="الرصيد")
async def balance(ctx, member: discord.Member = None):
  target = member or ctx.author
  wallet, bank = get_user(target.id)

  embed = discord.Embed(
      title=f"الحساب المالي لـ {target.name}", color=discord.Color.green()
  )
  embed.add_field(name="المحفظة", value=f"{wallet} قطعتك النقدية", inline=True)
  embed.add_field(name="البنك", value=f"{bank} قطعتك النقدية", inline=True)
  await ctx.send(embed=embed)


# 3. أمر العمل
@bot.command(name="عمل")
async def work(ctx):
  wallet, bank = get_user(ctx.author.id)
  earned = 50
  cursor.execute(
      "UPDATE users SET wallet = wallet + ? WHERE user_id = ?",
      (earned, ctx.author.id),
  )
  db.commit()

  embed = discord.Embed(
      title="انتهيت من العمل",
      description=f"ربحت {earned} وتم إضافتها إلى محفظتك",
      color=discord.Color.blue(),
  )
  await ctx.send(embed=embed)


# 4. أمر التحويل
@bot.command(name="تحويل")
async def pay(ctx, member: discord.Member, amount: int):
  if amount <= 0:
    await ctx.send("لا يمكنك تحويل مبالغ سالبة أو صفرية")
    return

  sender_wallet, _ = get_user(ctx.author.id)
  if sender_wallet < amount:
    await ctx.send("ليس لديك رصيد كاف في المحفظة")
    return

  get_user(member.id)

  cursor.execute(
      "UPDATE users SET wallet = wallet - ? WHERE user_id = ?",
      (amount, ctx.author.id),
  )
  cursor.execute(
      "UPDATE users SET wallet = wallet + ? WHERE user_id = ?",
      (amount, member.id),
  )
  db.commit()

  embed = discord.Embed(
      title="تمت العملية",
      description=f"تم تحويل {amount} بنجاح إلى {member.mention}",
      color=discord.Color.gold(),
  )
  await ctx.send(embed=embed)


# 5. إضافة سلعة للمتجر
@bot.command(name="اضافة_متجر")
async def add_shop(ctx, item_name: str, price: int):
  if not ctx.author.guild_permissions.administrator:
    await ctx.send("هذا الأمر مخصص للمشرفين فقط")
    return

  try:
    cursor.execute(
        "INSERT INTO shop (item_name, price) VALUES (?, ?)", (item_name, price)
    )
    db.commit()
    await ctx.send(f"تمت إضافة {item_name} إلى المتجر بسعر {price}")
  except sqlite3.IntegrityError:
    await ctx.send("هذه السلعة موجودة مسبقا في المتجر")


# 6. عرض المتجر
@bot.command(name="المتجر")
async def shop(ctx):
  cursor.execute("SELECT item_name, price FROM shop")
  items = cursor.fetchall()

  if not items:
    await ctx.send("المتجر فارغ حاليا")
    return

  embed = discord.Embed(title="متجر السيرفر", color=discord.Color.purple())
  for item, price in items:
    embed.add_field(name=item, value=f"السعر: {price}", inline=False)

  await ctx.send(embed=embed)


# ضع التوكن الخاص بك هنا
bot.run("TOKEN")