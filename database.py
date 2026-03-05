"""
MongoDB Database operations for ILSRP Verification System.
Uses MongoDB Atlas for free online storage.

Database Schema:
- users: User accounts with Discord/Roblox linking
- staff: Staff team profiles
- tickets: Ticket system data
- blacklist: Blacklisted members
- config: Bot configuration
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
        self.users = None
        self.staff = None
        self.tickets = None
        self.blacklist = None
        self.config = None
    
    async def connect(self):
        """Connect to MongoDB Atlas."""
        if not MONGODB_URI:
            print("WARNING: MONGODB_URI not set. Verification system will not work!")
            return False
        
        try:
            self.client = AsyncIOMotorClient(MONGODB_URI)
            self.db = self.client["ilsrp_database"]
            
            # Initialize collections
            self.users = self.db["users"]
            self.staff = self.db["staff"]
            self.tickets = self.db["tickets"]
            self.blacklist = self.db["blacklist"]
            self.config = self.db["config"]
            
            # Create indexes for faster queries
            await self.users.create_index("discord_id", unique=True)
            await self.users.create_index("roblox_id")
            await self.users.create_index("guild_id")
            await self.users.create_index("username")
            
            await self.staff.create_index("discord_id", unique=True)
            await self.staff.create_index("guild_id")
            
            await self.tickets.create_index("ticket_id", unique=True)
            await self.tickets.create_index("user_id")
            await self.tickets.create_index("guild_id")
            await self.tickets.create_index("status")
            
            await self.blacklist.create_index("discord_id", unique=True)
            await self.blacklist.create_index("roblox_id")
            await self.blacklist.create_index("guild_id")
            
            await self.config.create_index("key", unique=True)
            
            print("Connected to MongoDB Atlas successfully!")
            return True
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
    
    # ==================== USER OPERATIONS ====================
    
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
            "verified_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        try:
            await self.users.update_one(
                {"discord_id": discord_id},
                {"$set": verification_data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error adding verification: {e}")
            return False
    
    async def get_user(self, discord_id: int = None, roblox_id: int = None):
        """Get user record by Discord ID or Roblox ID."""
        query = {}
        if discord_id:
            query["discord_id"] = discord_id
        elif roblox_id:
            query["roblox_id"] = roblox_id
        else:
            return None
        
        try:
            return await self.users.find_one(query)
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    async def get_user_by_username(self, username: str):
        """Get user by Discord or Roblox username (case-insensitive search)."""
        try:
            return await self.users.find_one({
                "$or": [
                    {"discord_username": {"$regex": f"^{username}$", "$options": "i"}},
                    {"roblox_username": {"$regex": f"^{username}$", "$options": "i"}}
                ]
            })
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None
    
    async def update_user(self, discord_id: int, update_data: dict):
        """Update user data."""
        update_data["updated_at"] = datetime.utcnow()
        try:
            result = await self.users.update_one(
                {"discord_id": discord_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    async def delete_user(self, discord_id: int):
        """Delete a user record."""
        try:
            result = await self.users.delete_one({"discord_id": discord_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    async def get_all_users(self, guild_id: int = None):
        """Get all user records, optionally filtered by guild."""
        query = {"guild_id": guild_id} if guild_id else {}
        try:
            cursor = self.users.find(query)
            return await cursor.to_list(length=None)
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
    
    async def get_verified_count(self, guild_id: int = None):
        """Get count of verified users."""
        query = {"guild_id": guild_id} if guild_id else {}
        try:
            return await self.users.count_documents(query)
        except Exception as e:
            print(f"Error getting verified count: {e}")
            return 0
    
    # ==================== STAFF OPERATIONS ====================
    
    async def add_staff(self, discord_id: int, discord_username: str, guild_id: int,
                        role: str, team: str, joined_at: datetime = None):
        """Add or update a staff member record."""
        staff_data = {
            "discord_id": discord_id,
            "discord_username": discord_username,
            "guild_id": guild_id,
            "role": role,
            "team": team,
            "joined_at": joined_at or datetime.utcnow(),
            "promotions": [],
            "infractions": [],
            "verified": True,
            "updated_at": datetime.utcnow()
        }
        
        try:
            await self.staff.update_one(
                {"discord_id": discord_id, "guild_id": guild_id},
                {"$set": staff_data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error adding staff: {e}")
            return False
    
    async def get_staff(self, discord_id: int, guild_id: int = None):
        """Get staff member record."""
        query = {"discord_id": discord_id}
        if guild_id:
            query["guild_id"] = guild_id
        
        try:
            return await self.staff.find_one(query)
        except Exception as e:
            print(f"Error getting staff: {e}")
            return None
    
    async def update_staff(self, discord_id: int, guild_id: int, update_data: dict):
        """Update staff member data."""
        update_data["updated_at"] = datetime.utcnow()
        try:
            result = await self.staff.update_one(
                {"discord_id": discord_id, "guild_id": guild_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating staff: {e}")
            return False
    
    async def add_promotion(self, discord_id: int, guild_id: int, old_role: str, 
                           new_role: str, promoter: str, reason: str):
        """Add a promotion record to staff member."""
        promotion = {
            "old_role": old_role,
            "new_role": new_role,
            "promoted_by": promoter,
            "reason": reason,
            "date": datetime.utcnow()
        }
        
        try:
            result = await self.staff.update_one(
                {"discord_id": discord_id, "guild_id": guild_id},
                {"$push": {"promotions": promotion}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error adding promotion: {e}")
            return False
    
    async def add_infraction(self, discord_id: int, guild_id: int, infraction_type: str,
                            reason: str, infractor: str):
        """Add an infraction to staff member."""
        infraction = {
            "type": infraction_type,
            "reason": reason,
            "infracted_by": infractor,
            "date": datetime.utcnow()
        }
        
        try:
            result = await self.staff.update_one(
                {"discord_id": discord_id, "guild_id": guild_id},
                {"$push": {"infractions": infraction}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error adding infraction: {e}")
            return False
    
    async def get_all_staff(self, guild_id: int = None):
        """Get all staff members."""
        query = {"guild_id": guild_id} if guild_id else {}
        try:
            cursor = self.staff.find(query)
            return await cursor.to_list(length=None)
        except Exception as e:
            print(f"Error getting staff: {e}")
            return []
    
    # ==================== TICKET OPERATIONS ====================
    
    async def create_ticket(self, ticket_id: int, guild_id: int, user_id: int, 
                           category: str, channel_id: int):
        """Create a new ticket."""
        ticket_data = {
            "ticket_id": ticket_id,
            "guild_id": guild_id,
            "user_id": user_id,
            "category": category,
            "channel_id": channel_id,
            "status": "open",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "claimed_by": None,
            "claimed_at": None,
            "transcript": [],
            "messages": 0
        }
        
        try:
            await self.tickets.insert_one(ticket_data)
            return True
        except Exception as e:
            print(f"Error creating ticket: {e}")
            return False
    
    async def get_ticket(self, ticket_id: int = None, channel_id: int = None):
        """Get ticket by ID or channel ID."""
        query = {}
        if ticket_id:
            query["ticket_id"] = ticket_id
        elif channel_id:
            query["channel_id"] = channel_id
        else:
            return None
        
        try:
            return await self.tickets.find_one(query)
        except Exception as e:
            print(f"Error getting ticket: {e}")
            return None
    
    async def update_ticket(self, ticket_id: int, update_data: dict):
        """Update ticket data."""
        update_data["updated_at"] = datetime.utcnow()
        try:
            result = await self.tickets.update_one(
                {"ticket_id": ticket_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating ticket: {e}")
            return False
    
    async def close_ticket(self, ticket_id: int, closer: str = None):
        """Close a ticket."""
        update_data = {
            "status": "closed",
            "closed_by": closer,
            "closed_at": datetime.utcnow()
        }
        return await self.update_ticket(ticket_id, update_data)
    
    async def claim_ticket(self, ticket_id: int, claimed_by: int):
        """Claim a ticket."""
        update_data = {
            "claimed_by": claimed_by,
            "claimed_at": datetime.utcnow()
        }
        return await self.update_ticket(ticket_id, update_data)
    
    async def add_ticket_message(self, ticket_id: int, message_data: dict):
        """Add a message to ticket transcript."""
        try:
            result = await self.tickets.update_one(
                {"ticket_id": ticket_id},
                {
                    "$push": {"transcript": message_data},
                    "$inc": {"messages": 1}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error adding ticket message: {e}")
            return False
    
    async def get_user_tickets(self, user_id: int, guild_id: int = None):
        """Get all tickets for a user."""
        query = {"user_id": user_id}
        if guild_id:
            query["guild_id"] = guild_id
        
        try:
            cursor = self.tickets.find(query).sort("created_at", -1)
            return await cursor.to_list(length=None)
        except Exception as e:
            print(f"Error getting user tickets: {e}")
            return []
    
    async def get_open_tickets(self, guild_id: int = None, category: str = None):
        """Get all open tickets."""
        query = {"status": "open"}
        if guild_id:
            query["guild_id"] = guild_id
        if category:
            query["category"] = category
        
        try:
            cursor = self.tickets.find(query).sort("created_at", 1)
            return await cursor.to_list(length=None)
        except Exception as e:
            print(f"Error getting open tickets: {e}")
            return []
    
    async def get_ticket_count(self, guild_id: int = None):
        """Get total ticket count."""
        query = {}
        if guild_id:
            query["guild_id"] = guild_id
        
        try:
            return await self.tickets.count_documents(query)
        except Exception as e:
            print(f"Error getting ticket count: {e}")
            return 0
    
    async def get_category_stats(self, guild_id: int = None):
        """Get ticket statistics by category."""
        query = {}
        if guild_id:
            query["guild_id"] = guild_id
        
        try:
            pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": "$category",
                    "total": {"$sum": 1},
                    "open": {"$sum": {"$cond": [{"$eq": ["$status", "open"]}, 1, 0]}},
                    "closed": {"$sum": {"$cond": [{"$eq": ["$status", "closed"]}, 1, 0]}}
                }}
            ]
            cursor = self.tickets.aggregate(pipeline)
            return await cursor.to_list(length=None)
        except Exception as e:
            print(f"Error getting category stats: {e}")
            return []
    
    # ==================== BLACKLIST OPERATIONS ====================
    
    async def add_blacklist(self, discord_id: int = None, roblox_id: int = None, 
                           guild_id: int = None, reason: str = "No reason", added_by: str = "System"):
        """Add a user to blacklist."""
        blacklist_data = {
            "discord_id": discord_id,
            "roblox_id": roblox_id,
            "guild_id": guild_id,
            "reason": reason,
            "added_by": added_by,
            "added_at": datetime.utcnow()
        }
        
        query = {}
        if discord_id:
            query["discord_id"] = discord_id
        elif roblox_id:
            query["roblox_id"] = roblox_id
        else:
            return False
        
        try:
            await self.blacklist.update_one(
                query,
                {"$set": blacklist_data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error adding blacklist: {e}")
            return False
    
    async def remove_blacklist(self, discord_id: int = None, roblox_id: int = None):
        """Remove a user from blacklist."""
        query = {}
        if discord_id:
            query["discord_id"] = discord_id
        elif roblox_id:
            query["roblox_id"] = roblox_id
        else:
            return False
        
        try:
            result = await self.blacklist.delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error removing blacklist: {e}")
            return False
    
    async def is_blacklisted(self, discord_id: int = None, roblox_id: int = None, guild_id: int = None):
        """Check if user is blacklisted."""
        query = {}
        if discord_id:
            query["discord_id"] = discord_id
        elif roblox_id:
            query["roblox_id"] = roblox_id
        else:
            return False
        
        if guild_id:
            query["guild_id"] = guild_id
        
        try:
            result = await self.blacklist.find_one(query)
            return result is not None
        except Exception as e:
            print(f"Error checking blacklist: {e}")
            return False
    
    async def get_blacklist(self, guild_id: int = None):
        """Get all blacklisted users."""
        query = {"guild_id": guild_id} if guild_id else {}
        try:
            cursor = self.blacklist.find(query).sort("added_at", -1)
            return await cursor.to_list(length=None)
        except Exception as e:
            print(f"Error getting blacklist: {e}")
            return []
    
    # ==================== CONFIG OPERATIONS ====================
    
    async def set_config(self, key: str, value):
        """Set configuration value."""
        try:
            await self.config.update_one(
                {"key": key},
                {"$set": {"value": value, "updated_at": datetime.utcnow()}},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error setting config: {e}")
            return False
    
    async def get_config(self, key: str, default=None):
        """Get configuration value."""
        try:
            result = await self.config.find_one({"key": key})
            return result["value"] if result else default
        except Exception as e:
            print(f"Error getting config: {e}")
            return default
    
    async def delete_config(self, key: str):
        """Delete configuration."""
        try:
            result = await self.config.delete_one({"key": key})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting config: {e}")
            return False

# Global database instance
db = Database()

