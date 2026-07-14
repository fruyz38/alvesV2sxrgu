import os
import threading
import aiohttp
import json
import logging
import discord
from discord import app_commands
from discord.ext import commands, tasks
from flask import Flask

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FLASK SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Sorgu Botu Aktif! ✅"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Flask server {port} portunda başlatılıyor...")
    app.run(host="0.0.0.0", port=port, debug=False)

# --- DISCORD BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ============ API SORGULAMA FONKSİYONU ============
async def api_sorgula(url):
    """API'ye sorgu gönderir ve sonucu döndürür"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        logger.info(f"API sorgusu: {url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as response:
                logger.info(f"Yanıt kodu: {response.status_code}")
                
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return {"error": "404", "message": "API bulunamadı. Lütfen daha sonra tekrar deneyin."}
                elif response.status == 403:
                    return {"error": "403", "message": "API erişimi engellendi. Lütfen daha sonra tekrar deneyin."}
                elif response.status == 503:
                    return {"error": "503", "message": "API şu anda hizmet veremiyor. Lütfen daha sonra tekrar deneyin."}
                else:
                    return {"error": str(response.status), "message": f"API hatası: {response.status}"}
    except aiohttp.ClientError as e:
        logger.error(f"Bağlantı hatası: {e}")
        return {"error": "connection", "message": "API'ye bağlanılamadı. Lütfen daha sonra tekrar deneyin."}
    except Exception as e:
        logger.error(f"API hatası: {e}")
        return {"error": "unknown", "message": f"Beklenmeyen hata: {str(e)}"}

# ============ FORMATLAYICI ============
def format_sonuc(data, sorgu_turu):
    """API sonucunu formatlar"""
    embed = discord.Embed(
        title=f"📊 {sorgu_turu} Sorgu Sonucu",
        color=discord.Color.blue()
    )
    
    # Hata kontrolü
    if data.get("error"):
        embed.color = discord.Color.red()
        embed.description = f"❌ {data.get('message', 'Hata oluştu.')}"
        return embed
    
    # Başarılı sonuç
    if isinstance(data, dict):
        for anahtar, deger in data.items():
            if anahtar not in ["error", "message"]:
                embed.add_field(
                    name=f"🔹 {anahtar}", 
                    value=str(deger) if deger else "Bulunamadı", 
                    inline=False
                )
    elif isinstance(data, list) and len(data) > 0:
        embed.description = "**Sonuçlar:**"
        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                embed.add_field(
                    name=f"📌 Sonuç {i}", 
                    value="\n".join([f"**{k}:** {v}" for k, v in item.items()]), 
                    inline=False
                )
            else:
                embed.add_field(name=f"📌 Sonuç {i}", value=str(item), inline=False)
    else:
        embed.description = "❌ Sonuç bulunamadı."
    
    return embed

# ============ KEEP ALIVE ============
@tasks.loop(minutes=10)
async def keep_alive_ping():
    self_url = os.environ.get("RENDER_EXTERNAL_URL")
    if self_url:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self_url, timeout=10) as resp:
                    logger.info(f"[Keep-Alive] Ping OK: {resp.status}")
        except Exception as e:
            logger.warning(f"[Keep-Alive] Hata: {e}")

@keep_alive_ping.before_loop
async def before_keep_alive_ping():
    await bot.wait_until_ready()

# ============ MODAL'LAR ============

# --- TWITTER MODALLARI ---
class TwitterUserModal(discord.ui.Modal, title='🐦 Twitter Kullanıcı Sorgu'):
    kullanici = discord.ui.TextInput(
        label='Kullanıcı Adı',
        placeholder='abowie',
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        kullanici = self.kullanici.value.strip()
        url = f"https://ajanss.tr/api/twitter.php?type=user&q={kullanici}"
        data = await api_sorgula(url)
        embed = format_sonuc(data, "🐦 Twitter Kullanıcı")
        await interaction.followup.send(embed=embed, ephemeral=True)

class TwitterEmailModal(discord.ui.Modal, title='🐦 Twitter Mail Sorgu'):
    email = discord.ui.TextInput(
        label='E-posta Adresi',
        placeholder='bowie_2000@yahoo.com',
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        email = self.email.value.strip()
        url = f"https://ajanss.tr/api/twitter.php?type=email&q={email}"
        data = await api_sorgula(url)
        embed = format_sonuc(data, "🐦 Twitter Mail")
        await interaction.followup.send(embed=embed, ephemeral=True)

class TwitterPassModal(discord.ui.Modal, title='🐦 Twitter Şifre Sorgu'):
    sifre = discord.ui.TextInput(
        label='Şifre',
        placeholder='1234567y',
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        sifre = self.sifre.value.strip()
        url = f"https://ajanss.tr/api/twitter.php?type=pass&q={sifre}"
        data = await api_sorgula(url)
        embed = format_sonuc(data, "🐦 Twitter Şifre")
        await interaction.followup.send(embed=embed, ephemeral=True)

# --- DISCORD MODALLARI ---
class DiscordIDModal(discord.ui.Modal, title='💬 Discord ID Sorgu'):
    discord_id = discord.ui.TextInput(
        label='Discord ID',
        placeholder='1006067526339399711',
        required=True,
        max_length=30
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        discord_id = self.discord_id.value.strip()
        url = f"https://ajanss.tr/api/discordid.php?id={discord_id}"
        data = await api_sorgula(url)
        embed = format_sonuc(data, "💬 Discord ID")
        await interaction.followup.send(embed=embed, ephemeral=True)

# --- INSTAGRAM MODALLARI ---
class InstaUserModal(discord.ui.Modal, title='📸 Instagram Kullanıcı Sorgu'):
    kullanici = discord.ui.TextInput(
        label='Kullanıcı Adı',
        placeholder='pompomiller',
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        kullanici = self.kullanici.value.strip()
        url = f"https://ajanss.tr/api/instagram.php?type=user&q={kullanici}"
        data = await api_sorgula(url)
        embed = format_sonuc(data, "📸 Instagram Kullanıcı")
        await interaction.followup.send(embed=embed, ephemeral=True)

class InstaEmailModal(discord.ui.Modal, title='📸 Instagram Mail Sorgu'):
    email = discord.ui.TextInput(
        label='E-posta Adresi',
        placeholder='pompopr@gmail.com',
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        email = self.email.value.strip()
        url = f"https://ajanss.tr/api/instagram.php?type=email&q={email}"
        data = await api_sorgula(url)
        embed = format_sonuc(data, "📸 Instagram Mail")
        await interaction.followup.send(embed=embed, ephemeral=True)

class InstaIDModal(discord.ui.Modal, title='📸 Instagram ID Sorgu'):
    insta_id = discord.ui.TextInput(
        label='Instagram ID',
        placeholder='581959613',
        required=True,
        max_length=30
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        insta_id = self.insta_id.value.strip()
        url = f"https://ajanss.tr/api/instagram.php?type=id&q={insta_id}"
        data = await api_sorgula(url)
        embed = format_sonuc(data, "📸 Instagram ID")
        await interaction.followup.send(embed=embed, ephemeral=True)

class InstaPhoneModal(discord.ui.Modal, title='📸 Instagram Telefon Sorgu'):
    telefon = discord.ui.TextInput(
        label='Telefon Numarası',
        placeholder='17814729662',
        required=True,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        telefon = self.telefon.value.strip()
        url = f"https://ajanss.tr/api/instagram.php?type=phone&q={telefon}"
        data = await api_sorgula(url)
        embed = format_sonuc(data, "📸 Instagram Telefon")
        await interaction.followup.send(embed=embed, ephemeral=True)

class InstaNameModal(discord.ui.Modal, title='📸 Instagram İsim Sorgu'):
    isim = discord.ui.TextInput(
        label='İsim',
        placeholder='Miller',
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        isim = self.isim.value.strip()
        url = f"https://ajanss.tr/api/instagram.php?type=name&q={isim}"
        data = await api_sorgula(url)
        embed = format_sonuc(data, "📸 Instagram İsim")
        await interaction.followup.send(embed=embed, ephemeral=True)

class InstaAddressModal(discord.ui.Modal, title='📸 Instagram Adres Sorgu'):
    adres = discord.ui.TextInput(
        label='Adres',
        placeholder='Los Angeles',
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        adres = self.adres.value.strip()
        url = f"https://ajanss.tr/api/instagram.php?type=address&q={adres}"
        data = await api_sorgula(url)
        embed = format_sonuc(data, "📸 Instagram Adres")
        await interaction.followup.send(embed=embed, ephemeral=True)

# ============ VIEW'LAR ============
class MainMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="📂 Sorgu Paneli", style=discord.ButtonStyle.primary, custom_id="sorgu_paneli")
    async def sorgu_paneli(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = KomutlarView()
        embed = discord.Embed(
            title="📂 Sorgu Paneli",
            description="Sorgulamak istediğiniz platformu seçin:",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="ℹ️ Bilgi", style=discord.ButtonStyle.secondary, custom_id="bilgi")
    async def bilgi_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="ℹ️ Bot Bilgisi",
            description="Sorgu botu ile Twitter, Discord ve Instagram sorgulamaları yapabilirsiniz.",
            color=discord.Color.green()
        )
        embed.add_field(name="👤 Yapımcı", value="@alves0000", inline=True)
        embed.add_field(name="📌 Sürüm", value="2.0.0", inline=True)
        await interaction.response.edit_message(embed=embed, view=None)

class KomutlarView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🐦 Twitter", style=discord.ButtonStyle.primary, custom_id="twitter")
    async def twitter_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TwitterView()
        embed = discord.Embed(
            title="🐦 Twitter Sorgu Menüsü",
            description="Sorgu türünü seçin:",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="💬 Discord", style=discord.ButtonStyle.primary, custom_id="discord")
    async def discord_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = DiscordView()
        embed = discord.Embed(
            title="💬 Discord Sorgu Menüsü",
            description="Sorgu türünü seçin:",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="📸 Instagram", style=discord.ButtonStyle.primary, custom_id="instagram")
    async def instagram_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = InstagramView()
        embed = discord.Embed(
            title="📸 Instagram Sorgu Menüsü",
            description="Sorgu türünü seçin:",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="🔙 Geri", style=discord.ButtonStyle.secondary, custom_id="geri_ana")
    async def geri_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = MainMenuView()
        embed = discord.Embed(
            title="👋 Hoş Geldiniz!",
            description="Aşağıdaki butonlardan birini seçin:",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)

class TwitterView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="👤 Kullanıcı Adı", style=discord.ButtonStyle.secondary, custom_id="twitter_user")
    async def twitter_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TwitterUserModal())
    
    @discord.ui.button(label="📧 Mail", style=discord.ButtonStyle.secondary, custom_id="twitter_email")
    async def twitter_email(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TwitterEmailModal())
    
    @discord.ui.button(label="🔑 Şifre", style=discord.ButtonStyle.secondary, custom_id="twitter_pass")
    async def twitter_pass(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TwitterPassModal())
    
    @discord.ui.button(label="🔙 Geri", style=discord.ButtonStyle.secondary, custom_id="geri_komutlar")
    async def geri_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = KomutlarView()
        embed = discord.Embed(
            title="📂 Sorgu Paneli",
            description="Sorgulamak istediğiniz platformu seçin:",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)

class DiscordView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🆔 ID Sorgu", style=discord.ButtonStyle.secondary, custom_id="discord_id")
    async def discord_id(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DiscordIDModal())
    
    @discord.ui.button(label="🔙 Geri", style=discord.ButtonStyle.secondary, custom_id="geri_komutlar")
    async def geri_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = KomutlarView()
        embed = discord.Embed(
            title="📂 Sorgu Paneli",
            description="Sorgulamak istediğiniz platformu seçin:",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)

class InstagramView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="👤 Kullanıcı Adı", style=discord.ButtonStyle.secondary, custom_id="insta_user")
    async def insta_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InstaUserModal())
    
    @discord.ui.button(label="📧 Mail", style=discord.ButtonStyle.secondary, custom_id="insta_email")
    async def insta_email(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InstaEmailModal())
    
    @discord.ui.button(label="🆔 ID", style=discord.ButtonStyle.secondary, custom_id="insta_id")
    async def insta_id(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InstaIDModal())
    
    @discord.ui.button(label="📱 Telefon", style=discord.ButtonStyle.secondary, custom_id="insta_phone")
    async def insta_phone(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InstaPhoneModal())
    
    @discord.ui.button(label="📝 İsim", style=discord.ButtonStyle.secondary, custom_id="insta_name")
    async def insta_name(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InstaNameModal())
    
    @discord.ui.button(label="📍 Adres", style=discord.ButtonStyle.secondary, custom_id="insta_address")
    async def insta_address(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InstaAddressModal())
    
    @discord.ui.button(label="🔙 Geri", style=discord.ButtonStyle.secondary, custom_id="geri_komutlar")
    async def geri_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = KomutlarView()
        embed = discord.Embed(
            title="📂 Sorgu Paneli",
            description="Sorgulamak istediğiniz platformu seçin:",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)

# ============ KOMUTLAR ============
@bot.event
async def on_ready():
    logger.info(f'✅ {bot.user} olarak giriş yapıldı!')
    if not keep_alive_ping.is_running():
        keep_alive_ping.start()
    try:
        synced = await bot.tree.sync()
        logger.info(f"✅ {len(synced)} komut senkronize edildi.")
    except Exception as e:
        logger.error(f"Sync hatası: {e}")

@bot.tree.command(name="start", description="Bot'u başlat ve ana menüyü göster")
async def start(interaction: discord.Interaction):
    view = MainMenuView()
    embed = discord.Embed(
        title="👋 Hoş Geldiniz!",
        description="Aşağıdaki butonlardan birini seçin:",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="ping", description="Botun gecikme süresini göster")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Gecikme: {latency}ms",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="stats", description="Bot istatistiklerini göster")
async def stats(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 Bot İstatistikleri",
        color=discord.Color.blue()
    )
    embed.add_field(name="⏱️ Çalışma Süresi", value=f"{int(time.time() - start_time)} saniye", inline=True)
    embed.add_field(name="👤 Yapımcı", value="@alves0000", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ============ START ============
start_time = time.time()

if __name__ == "__main__":
    logger.info("=== BOT BAŞLATILIYOR ===")
    
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if not TOKEN:
        logger.critical("❌ DISCORD_TOKEN bulunamadı!")
        raise SystemExit(1)
    
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
