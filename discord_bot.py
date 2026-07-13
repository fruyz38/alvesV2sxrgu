import discord
from discord.ext import commands
from discord import app_commands
import requests
import asyncio
import os
import logging
import threading
import time
from typing import Optional
from flask import Flask, jsonify
import aiohttp
import urllib.parse

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
REQUIRED_ROLE_ID = int(os.getenv('REQUIRED_ROLE_ID', '0'))
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
    return jsonify({"status": "Bot is running!", "uptime": time.time() - start_time})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/ping')
def ping():
    return jsonify({"status": "pong"})

def run_web_server():
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# ============ API SORGULAMA (DÜZELTİLDİ) ============
def api_sorgula(url):
    """API'ye sorgu gönderir"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        logger.info(f"API sorgusu: {url}")
        response = requests.get(url, headers=headers, timeout=20)
        logger.info(f"API yanıt kodu: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API hata: {response.status_code} - {response.text[:200]}")
            return None
            
    except Exception as e:
        logger.error(f"API hatası: {e}")
        return None

# ============ MODAL'LAR ============
class AdSoyadModal(discord.ui.Modal, title='🧾 Ad Soyad Sorgu'):
    ad = discord.ui.TextInput(
        label='Adınız',
        placeholder='Ahmet',
        required=True,
        max_length=50
    )
    soyad = discord.ui.TextInput(
        label='Soyadınız',
        placeholder='Yılmaz',
        required=True,
        max_length=50
    )
    il = discord.ui.TextInput(
        label='İl (Opsiyonel)',
        placeholder='İstanbul veya boş bırakın',
        required=False,
        max_length=30
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        ad = self.ad.value.strip()
        soyad = self.soyad.value.strip()
        il = self.il.value.strip() if self.il.value else ""
        
        # URL encode yap (Türkçe karakterler için)
        ad_encoded = urllib.parse.quote(ad)
        soyad_encoded = urllib.parse.quote(soyad)
        il_encoded = urllib.parse.quote(il) if il else ""
        
        # DOĞRU URL - sowixapi
        if il:
            url = f"https://api.hexnox.pro/sowixapi/adsoyadilce.php?ad={ad_encoded}&soyad={soyad_encoded}&il={il_encoded}"
        else:
            url = f"https://api.hexnox.pro/sowixapi/adsoyadilce.php?ad={ad_encoded}&soyad={soyad_encoded}"
        
        logger.info(f"Adsoyad sorgu URL: {url}")
        
        data = api_sorgula(url)
        
        if data and data.get("data"):
            data_listesi = data.get("data")
            if data_listesi and isinstance(data_listesi, list) and len(data_listesi) > 0:
                kisi = data_listesi[0]
                sonuc = "\n".join([f"🔹 {k}: {v}" for k, v in kisi.items()])
                embed = discord.Embed(
                    title="✅ Sorgu Sonucu",
                    description=sonuc,
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
        
        # İlk deneme başarısız olursa alternatif URL dene
        alt_url = f"https://api.hexnox.pro/sowixapi/adsoyad.php?ad={ad_encoded}&soyad={soyad_encoded}"
        if il:
            alt_url += f"&il={il_encoded}"
        
        logger.info(f"Alternatif sorgu URL: {alt_url}")
        data = api_sorgula(alt_url)
        
        if data and data.get("data"):
            data_listesi = data.get("data")
            if data_listesi and isinstance(data_listesi, list) and len(data_listesi) > 0:
                kisi = data_listesi[0]
                sonuc = "\n".join([f"🔹 {k}: {v}" for k, v in kisi.items()])
                embed = discord.Embed(
                    title="✅ Sorgu Sonucu",
                    description=sonuc,
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
        
        await interaction.followup.send("❌ Sonuç bulunamadı. Lütfen bilgileri kontrol edin.", ephemeral=True)

class TCProModal(discord.ui.Modal, title='🆔 TC Pro Sorgu'):
    tc = discord.ui.TextInput(
        label='TC Kimlik Numarası',
        placeholder='12345678901',
        required=True,
        max_length=11,
        min_length=11
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        tc = self.tc.value.strip()
        
        if not tc.isdigit() or len(tc) != 11:
            await interaction.followup.send("❌ Geçerli bir 11 haneli TC giriniz.", ephemeral=True)
            return
        
        url = f"https://api.hexnox.pro/sowixapi/tcpro.php?tc={tc}"
        logger.info(f"TC Pro sorgu URL: {url}")
        
        data = api_sorgula(url)
        
        if data and data.get("data"):
            data_content = data.get("data")
            sonuc = "\n".join([f"🔹 {k}: {v}" for k, v in data_content.items()])
            embed = discord.Embed(
                title="✅ TC Pro Sonuç",
                description=sonuc,
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("❌ TC bulunamadı.", ephemeral=True)

class GSMModal(discord.ui.Modal, title='📱 GSM Detay Sorgu'):
    gsm = discord.ui.TextInput(
        label='GSM Numarası',
        placeholder='5365865294 (Başında 0 olmadan)',
        required=True,
        max_length=10,
        min_length=10
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        gsm = self.gsm.value.strip()
        
        if not gsm.isdigit() or len(gsm) != 10:
            await interaction.followup.send("❌ Geçerli bir GSM numarası giriniz.", ephemeral=True)
            return
        
        url = f"https://api.hexnox.pro/sowixapi/gsmdetay.php?gsm={gsm}"
        logger.info(f"GSM detay sorgu URL: {url}")
        
        data = api_sorgula(url)
        
        if data and data.get("success") and data.get("Data"):
            d = data["Data"]
            sonuc = f"""📱 GSM Detay Sorgu Sonucu

👤 Ad Soyad: {d.get('AD', 'Yok')} {d.get('SOYAD', 'Yok')}
🆔 TC: {d.get('TC', 'Yok')}
🎂 Doğum Tarihi: {d.get('DOGUMTARIHI', 'Yok')}
📍 Adres: {d.get('Ikametgah', 'Yok')}
👩 Anne Adı: {d.get('ANNEADI', 'Yok')}
👨 Baba Adı: {d.get('BABAADI', 'Yok')}"""
            embed = discord.Embed(
                title="📱 GSM Detay Sonucu",
                description=sonuc,
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("❌ Sonuç bulunamadı.", ephemeral=True)

class PlakaModal(discord.ui.Modal, title='🚗 Plaka Sorgu'):
    plaka = discord.ui.TextInput(
        label='Plaka Numarası',
        placeholder='34KG4978',
        required=True,
        max_length=8
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        plaka = self.plaka.value.strip().upper()
        
        if not plaka.isalnum() or len(plaka) > 8:
            await interaction.followup.send("❌ Geçerli bir plaka giriniz.", ephemeral=True)
            return
        
        url = f"https://quantrexsystems.alwaysdata.net/diger/plaka.php?plaka={plaka}"
        logger.info(f"Plaka sorgu URL: {url}")
        
        data = api_sorgula(url)
        
        if data and data.get("success") and data.get("Data"):
            d = data["Data"]
            sonuc = f"""🚗 Plaka Sorgu Sonucu

Plaka: {d.get('plaka', 'N/A')}
Borç Türü: {d.get('borcTuru', 'N/A')}
İsim Soyisim: {d.get('Isimsoyisim', 'N/A')}
T.C.: {d.get('Tc', 'N/A')}
Yazılan Ceza: {d.get('YazilanCeza', 'N/A')}
Toplam Ceza: {d.get('ToplamCeza', 'N/A')}"""
            embed = discord.Embed(
                title="🚗 Plaka Sorgu Sonucu",
                description=sonuc,
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("❌ Veri bulunamadı.", ephemeral=True)

# ============ VIEW'LAR ============
class MainMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="📂 Komutlar", style=discord.ButtonStyle.primary, custom_id="komutlar")
    async def komutlar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = KomutlarView()
        embed = discord.Embed(
            title="⚙️ Komut Türü Seçin",
            description="Hangi tür komutları kullanmak istersiniz?",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="ℹ️ Bilgi", style=discord.ButtonStyle.secondary, custom_id="bilgi")
    async def bilgi_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="ℹ️ Bot Bilgisi",
            description="Bu bot çeşitli sorgulama işlemleri yapmanızı sağlar.",
            color=discord.Color.green()
        )
        embed.add_field(name="📌 Sürüm", value="1.1.0", inline=True)
        embed.add_field(name="👤 Yapımcı", value="@alves0000", inline=True)
        embed.add_field(name="⏱️ Çalışma Süresi", value=f"{int(time.time() - start_time)} saniye", inline=True)
        await interaction.response.edit_message(embed=embed, view=None)

class KomutlarView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🆓 Free Komutlar", style=discord.ButtonStyle.success, custom_id="free")
    async def free_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = FreeKomutlarView()
        embed = discord.Embed(
            title="🆓 Free Komutlar Menüsü",
            description="Aşağıdaki sorgulama işlemlerinden birini seçin:",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="💎 Premium Komutlar", style=discord.ButtonStyle.danger, custom_id="premium")
    async def premium_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="💎 Premium Komutlar",
            description="Premium panel satın alımları için yetkiliyle iletişime geçin.",
            color=discord.Color.gold()
        )
        embed.add_field(name="📞 İletişim", value="@alves0000", inline=False)
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="🔙 Geri", style=discord.ButtonStyle.secondary, custom_id="geri_ana")
    async def geri_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👋 Hoş Geldiniz!",
            description="Aşağıdaki butonlardan birini seçin:",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=MainMenuView())

class FreeKomutlarView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🧾 Ad Soyad Sorgu", style=discord.ButtonStyle.secondary, custom_id="adsoyad")
    async def adsoyad_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdSoyadModal())
    
    @discord.ui.button(label="🆔 TC Pro Sorgu", style=discord.ButtonStyle.secondary, custom_id="tcpro")
    async def tcpro_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TCProModal())
    
    @discord.ui.button(label="📱 GSM Detay", style=discord.ButtonStyle.secondary, custom_id="gsmdetay")
    async def gsmdetay_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GSMModal())
    
    @discord.ui.button(label="🚗 Plaka Sorgu", style=discord.ButtonStyle.secondary, custom_id="plaka")
    async def plaka_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PlakaModal())
    
    @discord.ui.button(label="📞 İletişim", style=discord.ButtonStyle.secondary, custom_id="iletisim")
    async def iletisim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📞 İletişim Bilgileri",
            description="Bot yapımcısı ile iletişime geçin:",
            color=discord.Color.blue()
        )
        embed.add_field(name="👤 Yapımcı", value="@alves0000", inline=False)
        embed.add_field(name="📱 Telegram", value="https://t.me/alves0000", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🔙 Geri", style=discord.ButtonStyle.secondary, custom_id="geri_komutlar")
    async def geri_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚙️ Komut Türü Seçin",
            description="Hangi tür komutları kullanmak istersiniz?",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=KomutlarView())

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
        title="👋 Hoş Geldiniz!",
        description="Aşağıdaki butonlardan birini seçin:",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

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
