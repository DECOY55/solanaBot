# app.py (Main File) - Modified for Vercel with FastAPI Startup Event and Test Message
import os
import asyncio
from fastapi import FastAPI
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import connect
from telegram import Bot

# ===== CONFIG ===== (Replace these values via Vercel Environment Variables)
PRIVATE_KEY = os.getenv("PRIVATE_KEY")  # Base58 encoded private key
RPC_URL = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
BUY_AMOUNT_SOL = float(os.getenv("BUY_AMOUNT_SOL", "0.05"))
PROFIT_TARGET = float(os.getenv("PROFIT_TARGET", "1.5"))

# ===== INIT FASTAPI =====
app = FastAPI()

class SolanaLaunchBot:
    def __init__(self):
        self.keypair = Keypair.from_base58_string(PRIVATE_KEY)
        self.client = AsyncClient(RPC_URL)
        self.bot = Bot(TELEGRAM_TOKEN)
        self.seen_tokens = set()
        self.portfolio = {}

    async def start(self):
        """Start all bot services concurrently."""
        await asyncio.gather(
            self.listen_new_mints(),
            self.monitor_profits()
        )

    async def listen_new_mints(self):
        """Watch for new token launches."""
        # For testing purposes: simulate a token event after a delay.
        await asyncio.sleep(10)  # Wait 10 seconds after startup.
        test_token = "TEST123456"
        await self.process_new_token(test_token)
        
        # When ready for real data, comment out the simulation above and uncomment below:
        """
        async with connect(RPC_URL) as websocket:
            await websocket.account_subscribe(
                program_id="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                commitment="confirmed"
            )
            while True:
                msg = await websocket.recv()
                new_token = str(msg[0].result.value.pubkey)
                if new_token not in self.seen_tokens:
                    self.seen_tokens.add(new_token)
                    asyncio.create_task(self.process_new_token(new_token))
        """

    async def process_new_token(self, token_address: str):
        """Handle new token detection."""
        if await self.is_safe_token(token_address):
            await self.execute_trade(token_address, is_buy=True)
            self.portfolio[token_address] = {
                'amount': BUY_AMOUNT_SOL,
                'buy_price': await self.get_price(token_address)
            }
            await self.bot.send_message(
                CHAT_ID,
                f"🚀 New token detected!\n"
                f"Address: {token_address[:6]}...\n"
                f"Buying {BUY_AMOUNT_SOL} SOL worth"
            )

    async def monitor_profits(self):
        """Automatic profit taking."""
        while True:
            for token, data in list(self.portfolio.items()):
                current_price = await self.get_price(token)
                if (current_price / data['buy_price']) >= PROFIT_TARGET:
                    await self.execute_trade(token, is_buy=False)
                    del self.portfolio[token]
                    await self.bot.send_message(
                        CHAT_ID,
                        f"✅ Sold {token[:6]}...\n"
                        f"Profit: {(current_price/data['buy_price'] - 1)*100:.1f}%"
                    )
            await asyncio.sleep(60)

    async def is_safe_token(self, token_address: str) -> bool:
        """Implement your safety checks here."""
        return True  # Replace with actual checks

    async def get_price(self, token_address: str) -> float:
        """Get token price from DEX."""
        return 0.0  # Replace with actual price-checking logic

    async def execute_trade(self, token_address: str, is_buy: bool):
        """Execute buy/sell trade."""
        print(f"{'Buying' if is_buy else 'Selling'} {token_address[:6]}...")

# Create a single bot instance.
bot = SolanaLaunchBot()

# Use FastAPI's startup event to launch the bot in the background.
@app.on_event("startup")
async def startup_event():
    # Ensure there's an event loop; create one if needed.
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Send a test message to Telegram to verify integration.
    try:
        await bot.bot.send_message(
            CHAT_ID,
            "Bot has started successfully on Vercel!"
        )
    except Exception as e:
        print(f"Error sending startup message: {e}")
    
    # Start the bot in the background.
    loop.create_task(bot.start())

# A simple HTTP route to verify that FastAPI is running.
@app.get("/")
async def home():
    return {"message": "Bot is running!"}
