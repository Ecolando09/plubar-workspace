#!/usr/bin/env python3
"""
Telegram Channel Listener using Telethon
Forward messages from Telegram channels to Discord or other platforms
"""
import os
import asyncio
from datetime import datetime
from typing import Callable, Optional
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import Message, Channel

load_dotenv()

class TelegramListener:
    """Listen to Telegram channels and handle messages"""
    
    def __init__(self, session_name: str = 'telethon_listener'):
        self.api_id = os.environ.get('API_ID')
        self.api_hash = os.environ.get('API_HASH')
        self.phone = os.environ.get('PHONE')
        self.session_name = session_name
        self.client: Optional[TelegramClient] = None
        self.running = False
        self.handlers = {}
    
    async def connect(self):
        """Connect to Telegram"""
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone)
            code = input('Enter Telegram code: ')
            try:
                await self.client.sign_in(self.phone, code)
            except SessionPasswordNeededError:
                pw = input('Enter 2FA password: ')
                await self.client.sign_in(password=pw)
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()
    
    async def get_channel_entity(self, channel_id: str):
        """Get channel entity from ID, username, or invite link"""
        if channel_id.startswith('https://t.me/'):
            channel_id = channel_id.replace('https://t.me/', '')
        
        if channel_id.startswith('+'):
            # Username or invite link
            entity = await self.client.get_entity(channel_id)
        else:
            # Could be username, ID, or invite link
            try:
                entity = await self.client.get_entity(int(channel_id))
            except ValueError:
                entity = await self.client.get_entity(channel_id)
        
        return entity
    
    async def listen_to_channel(self, channel_id: str, handler: Callable[[Message], None]):
        """
        Listen to a channel and call handler for each new message
        
        Args:
            channel_id: Channel ID, username, or invite link
            handler: Async function to call for each message
        """
        entity = await self.get_channel_entity(channel_id)
        self.handlers[entity.id] = handler
        
        @self.client.on(Message(chats=[entity]))
        async def new_message(event):
            message = event.message
            if message.text:
                await handler(message)
    
    async def start_listening(self):
        """Start listening to all registered channels"""
        self.running = True
        while self.running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """Stop listening"""
        self.running = False


class DiscordForwarder:
    """Forward Telegram messages to Discord"""
    
    def __init__(self, bot_token: str, channel_id: str):
        self.bot_token = bot_token
        self.channel_id = channel_id
        import requests
        self.http = requests.Session()
        self.http.headers.update({'Authorization': f'Bot {bot_token}'})
    
    async def forward(self, message: Message):
        """Forward a message to Discord"""
        text = message.text[:1900]  # Discord limit
        
        # Get sender info if available
        sender = ""
        if message.sender:
            if hasattr(message.sender, 'username') and message.sender.username:
                sender = f"@{message.sender.username}"
            elif hasattr(message.sender, 'first_name'):
                sender = message.sender.first_name
        
        payload = {
            'content': f"📱 **{sender}**\n{text}"
        }
        
        self.http.post(
            f'https://discord.com/api/v10/channels/{self.channel_id}/messages',
            json=payload
        )
    
    def send(self, text: str):
        """Send a simple text message"""
        payload = {'content': text}
        self.http.post(
            f'https://discord.com/api/v10/channels/{self.channel_id}/messages',
            json=payload
        )


# CLI Interface
if __name__ == '__main__':
    import sys
    
    async def print_message(message: Message):
        print(f"[{message.date}] {message.text[:100]}")
    
    async def main():
        if not os.environ.get('API_ID'):
            print("Error: Set API_ID and API_HASH in .env file")
            print("See SKILL.md for setup instructions")
            sys.exit(1)
        
        listener = TelegramListener()
        await listener.connect()
        
        if len(sys.argv) < 2:
            print("Usage: python telethon_listener.py <channel_id>")
            sys.exit(1)
        
        channel_id = sys.argv[1]
        print(f"Listening to {channel_id}...")
        
        await listener.listen_to_channel(channel_id, print_message)
        await listener.start_listening()
    
    asyncio.run(main())
