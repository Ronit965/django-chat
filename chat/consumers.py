import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Message


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"room_{self.room_name}"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"WebSocket connected to room: {self.room_name}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected from room: {self.room_name}")

    async def receive(self, text_data):
        try:
            data_json = json.loads(text_data)
            print(f"Received data: {data_json}")
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_message',
                    'message': data_json
                }
            )
        except json.JSONDecodeError:
            print("Error: Invalid JSON received")
        except Exception as e:
            print(f"Error in receive: {e}")

    async def send_message(self, event):
        data = event['message']
        
        # Save message to database
        await self.create_message(data=data)
        
        # Send message to WebSocket
        response = {
            "sender": data["sender"], 
            "message": data["message"]
        }
        
        await self.send(text_data=json.dumps({"message": response}))

    @database_sync_to_async
    def create_message(self, data):
        try:
            get_room = Room.objects.get(room_name=data["room_name"])
            
            # Create new message (removed duplicate check for better real-time experience)
            new_message = Message.objects.create(
                room=get_room, 
                message=data["message"], 
                sender=data["sender"]
            )
            print(f"Message saved: {new_message}")
            return new_message
        except Room.DoesNotExist:
            print(f"Room not found: {data['room_name']}")
        except Exception as e:
            print(f"Error saving message: {e}")