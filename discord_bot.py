import discord
from discord.ext import commands
from discord import app_commands
import requests
import asyncio
import os
import logging
import threading
import time
from flask import Flask, jsonify
import aiohttp
import urllib.parse
import json

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
PORT = int(os.getenv('PORT', 5000))

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set!")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Flask
app = Flask(__name__)
ping_counter = [0]
start_time = time.time()

@app.route('/')
def home():
    return jsonify({"status": "Bot is running!"})

@app.route('/ping')
def ping():
    return jsonify({"status": "pong"})

def run_web_server():
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# ============ API SORGULAMA ============
def api_sorgula(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        logger.info(f"API sorgusu: {url}")
        response = requests.get(url, headers=headers, timeout=20)
        logger.info(f"Yanıt kodu: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"API hatası: {e}")
        return None

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
        url = f"https://ajanss.tr/api/twitter.php?type=user&q={urllib.parse.quote(kullanici)}"
        data = api_sorgula(url)
        
        if data:
            mesaj = "**🐦 Twitter Kullanıcı Sorgu Sonucu**\n\n"
            if isinstance(data, dict):
                for anahtar, deger in data.items():
                    mesaj += f"**{anahtar}:** {deger}\n"
            elif isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, dict):
                        for anahtar, deger in item.items():
                            mesaj += f"**{anahtar}:** {deger}\n"
                        mesaj += "\n"
            await interaction.followup.send(mesaj, ephemeral=True)
        else:
            await interaction.followup.send("❌ Sonuç bulunamadı.", ephemeral=True)

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
        url = f"https://ajanss.tr/api/twitter.php?type=email&q={urllib.parse.quote(email)}"
        data = api_sorgula(url)
        
        if data:
            mesaj = "**🐦 Twitter Mail Sorgu Sonucu**\n\n"
            if isinstance(data, dict):
                for anahtar, deger in data.items():
                    mesaj += f"**{anahtar}:** {deger}\n"
            elif isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, dict):
                        for anahtar, deger in item.items():
                            mesaj += f"**{anahtar}:** {deger}\n"
                        mesaj += "\n"
            await interaction.followup.send(mesaj, ephemeral=True)
        else:
            await interaction.followup.send("❌ Sonuç bulunamadı.", ephemeral=True)

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
        url = f"https://ajanss.tr/api/twitter.php?type=pass&q={urllib.parse.quote(sifre)}"
        data = api_sorgula(url)
        
        if data:
            mesaj = "**🐦 Twitter Şifre Sorgu Sonucu**\n\n"
            if isinstance(data, dict):
                for anahtar, deger in data.items():
                    mesaj += f"**{anahtar}:** {deger}\n"
            elif isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, dict):
                        for anahtar, deger in item.items():
                            mesaj += f"**{anahtar}:** {deger}\n"
                        mesaj += "\n"
            await interaction.followup.send(mesaj, ephemeral=True)
        else:
            await interaction.followup.send("❌ Sonuç bulunamadı.", ephemeral=True)

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
        data = api_sorgula(url)
        
        if data:
            mesaj = "**💬 Discord ID Sorgu Sonucu**\n\n"
            if isinstance(data, dict):
                for anahtar, deger in data.items():
                    mesaj += f"**{anahtar}:** {deger}\n"
            elif isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, dict):
                        for anahtar, deger in item.items():
                            mesaj += f"**{anahtar}:** {deger}\n"
                        mesaj += "\n"
            await interaction.followup.send(mesaj, ephemeral=True)
        else:
            await interaction.followup.send("❌ Sonuç bulunamadı.", ephemeral=True)

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
        url = f"https://ajanss.tr/api/instagram.php?type=user&q={urllib.parse.quote(kullanici)}"
        data = api_sorgula(url)
        
        if data:
            mesaj = "**📸 Instagram Kullanıcı Sorgu Sonucu**\n\n"
            if isinstance(data, dict):
                for anahtar, deger in data.items():
                    mesaj += f"**{anahtar}:** {deger}\n"
            elif isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, dict):
                        for anahtar, deger in item.items():
                            mesaj += f"**{anahtar}:** {deger}\n"
                        mesaj += "\n"
            await interaction.followup.send(mesaj, ephemeral=True)
        else:
            await interaction.followup.send("❌ Sonuç bulunamadı.", ephemeral=True)

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
        url = f"https://ajanss.tr/api/instagram.php?type=email&q={urllib.parse.quote(email)}"
        data = api_sorgula(url)
        
        if data:
            mesaj = "**📸 Instagram Mail Sorgu Sonucu**\n\n"
            if isinstance(data, dict):
                for anahtar, deger in data.items():
                    mesaj += f"**{anahtar}:** {deger}\n"
            elif isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, dict):
                        for anahtar, deger in item.items():
                            mesaj += f"**{anahtar}:** {deger}\n"
                        mesaj += "\n"
            await interaction.followup.send(mesaj, ephemeral=True)
        else:
            await interaction.followup.send("❌ Sonuç bulunamadı.", ephemeral=True)

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
        data = api_sorgula(url)
        
        if data:
            mesaj = "**📸 Instagram ID Sorgu Sonucu**\n\n"
            if isinstance(data, dict):
                for anahtar, deger in data.items():
                    mesaj += f"**{anahtar}:** {deger}\n"
            elif isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, dict):
                        for anahtar, deger in item.items():
                            mesaj += f"**{anahtar}:** {deger}\n"
                        mesaj += "\n"
            await interaction.followup.send(mesaj, ephemeral=True)
        else:
            await interaction.followup.send("❌ Sonuç bulunamadı.", ephemeral=True)

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
        data = api_sorgula(url)
        
        if data:
            mesaj = "**📸 Instagram Telefon Sorgu Sonucu**\n\n"
            if isinstance(data, dict):
                for anahtar, deger in data.items():
                    mesaj += f"**{anahtar}:** {deger}\n"
            elif isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, dict):
                        for anahtar, deger in item.items():
                            mesaj += f"**{anahtar}:** {deger}\n"
                        mesaj += "\n"
            await interaction.followup.send(mesaj, ephemeral=True)
        else:
            await interaction.followup.send("❌ Sonuç bulunamadı.", ephemeral=True)

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
        url = f"https://ajanss.tr/api/instagram.php?type=name&q={urllib.parse.quote(isim)}"
        data = api_sorgula(url)
        
        if data:
            mesaj = "**📸 Instagram İsim Sorgu Sonucu**\n\n"
            if isinstance(data, dict):
                for anahtar, deger in data.items():
                    mesaj += f"**{anahtar}:** {deger}\n"
            elif isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, dict):
                        for anahtar, deger in item.items():
                            mesaj += f"**{anahtar}:** {deger}\n"
                        mesaj += "\n"
            await interaction.followup.send(mesaj, ephemeral=True)
        else:
            await interaction.followup.send("❌ Sonuç bulunamadı.", ephemeral=True)

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
        url = f"https://ajanss.tr/api/instagram.php?type=address&q={urllib.parse.quote(adres)}"
        data = api_sorgula(url)
        
        if data:
            mesaj = "**📸 Instagram Adres Sorgu Sonucu**\n\n"
            if isinstance(data, dict):
                for anahtar, deger in data.items():
                    mesaj += f"**{anahtar}:** {deger}\n"
            elif isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, dict):
                        for anahtar, deger in item.items():
                            mesaj += f"**{anahtar}:** {deger}\n"
                        mesaj += "\n"
            await interaction.followup.send(mesaj, ephemeral=True)
        else:
            await interaction.followup.send("❌ Sonuç bulunamadı.", ephemeral=True)

# ============ VIEW'LAR ============
class MainMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="📂 Sorgu Paneli", style=discord.ButtonStyle.primary, custom_id="sorgu_paneli")
    async def sorgu_paneli(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = KomutlarView()
        embed = discord.Embed(
            title="📂 Alves Sorgu Paneli",
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
            title="Alves Sorgu Paneli",
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
            title="📂Alves Sorgu Paneli",
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
            title="📂Alves Sorgu Paneli",
            description="Sorgulamak istediğiniz platformu seçin:",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)

# ============ KOMUTLAR ============
@bot.event
async def on_ready():
    logger.info(f'{bot.user} olarak giriş yapıldı!')
    try:
        synced = await bot.tree.sync()
        logger.info(f"{len(synced)} komut senkronize edildi.")
        
        if ADMIN_ID != 0:
            try:
                admin = await bot.fetch_user(ADMIN_ID)
                await admin.send(f"✅ Bot başarıyla başlatıldı!")
            except:
                pass
    except Exception as e:
        logger.error(f"Senkronizasyon hatası: {e}")

@bot.tree.command(name="start", description="Bot'u başlat ve ana menüyü göster")
async def start(interaction: discord.Interaction):
    view = MainMenuView()
    embed = discord.Embed(
        title="👋Alves Sorgu Paneline Hoş Geldiniz!",
        description="Aşağıdaki butonlardan birini seçin:",
        color=discord.Color.blue()
    )
    # HERKESE GÖRÜNÜR - ephemeral yok
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

# ============ PING ============
async def keep_alive():
    bot_url = f"http://localhost:{PORT}/ping"
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(bot_url, timeout=5) as response:
                    if response.status == 200:
                        ping_counter[0] += 1
        except:
            pass
        await asyncio.sleep(480)

def run_bot():
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Bot hatası: {e}")

# ============ ANA ============
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(keep_alive())
    
    run_bot()
