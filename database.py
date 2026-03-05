"""
MongoDB Database operations for the verification system.
Uses MongoDB Atlas for free online storage.
"""
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# MongoDB connection
MONGODB_URI = os.environ.get("MONGODB_URI", "")

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.verifications = None
    
    async def connect(self):
        """Connect to MongoDB Atlas."""
        if not MONGODB_URI:
            print("WARNING: MONGODB_URI not set. Verification system will not work!")
            return False
        
        try:
            self.client = AsyncIOMotorClient(MONGODB_URI)
            self.db = self.client["ilsrp_verification"]
            self.verifications = self.db["verifications"]
            
            # Create indexes for faster queries
            await self.verifications.create_index("discord_id", unique=True)
            await self.verifications.create_index("roblox_id")
            await self.verifications.create_index("guild_id")
            
            print("Connected to MongoDB Atlas successfully!")
            return True
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
    
    async def add_verification(self, discord_id: int, roblox_id: int, roblox_username: str, 
                                discord_username: str, guild_id: int, member_guid: str = None,
                                discord_join_date: datetime = None, guild_join_date: datetime = None):
        """Add or update a verification record."""
        verification_data = {
            "discord_id": discord_id,
            "roblox_id": roblox_id,
            "roblox_username": roblox_username,
            "discord_username": discord_username,
            "guild_id": guild_id,
            "member_guid": member_guid,
            "discord_join_date": discord_join_date,
            "guild_join_date": guild_join_date,
            "verified_at": datetime.utcnow()
        }
        
        try:
            await self.verifications.update_one(
                {"discord_id": discord_id},
                {"$set": verification_data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error adding verification: {e}")
            return False
    
    async def get_verification(self, discord_id: int = None, roblox_id: int = None):
        """Get verification record by Discord ID or Roblox ID."""
        query = {}
        if discord_id:
            query["discord_id"] = discord_id
        elif roblox_id:
            query["roblox_id"] = roblox_id
        else:
            return None
        
        try:
            return await self.verifications.find_one(query)
        except Exception as e:
            print(f"Error getting verification: {e}")
            return None
    
    async def delete_verification(self, discord_id: int):
        """Delete a verification record."""
        try:
            result = await self.verifications.delete_one({"discord_id": discord_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting verification: {e}")
            return False
    
    async def get_all_verifications(self, guild_id: int = None):
        """Get all verification records, optionally filtered by guild."""
        query = {"guild_id": guild_id} if guild_id else {}
        try:
            cursor = self.verifications.find(query)
            return await cursor.to_list(length=None)
        except Exception as e:
            print(f"Error getting verifications: {e}")
            return []

# Global database instance
db = Database()
</parameter>
