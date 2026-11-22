import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from organizations.models import ProjectMembership

from .models import ProjectMessage, ProjectRoom

MAX_MESSAGE_LENGTH = 2000


class ProjectChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_id = int(self.scope["url_route"]["kwargs"]["project_id"])
        user = self.scope["user"]
        if not user.is_authenticated or not await self._is_member(user.id):
            await self.close()
            return
        self.group_name = f"project_{self.project_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            return
        body = str(payload.get("body") or "").strip()
        if not body:
            return
        body = body[:MAX_MESSAGE_LENGTH]
        saved = await self._save_message(self.scope["user"].id, body)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "body": saved["body"],
                "author": saved["author"],
                "created_at": saved["created_at"],
            },
        )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "body": event["body"],
                    "author": event["author"],
                    "created_at": event["created_at"],
                }
            )
        )

    @database_sync_to_async
    def _is_member(self, user_id):
        return ProjectMembership.objects.filter(
            project_id=self.project_id,
            user_id=user_id,
            user__is_active=True,
        ).exists()

    @database_sync_to_async
    def _save_message(self, user_id, body):
        room, _created = ProjectRoom.objects.get_or_create(project_id=self.project_id)
        message = ProjectMessage.objects.create(
            room=room,
            author_id=user_id,
            body=body,
        )
        return {
            "body": message.body,
            "author": message.author.username,
            "created_at": message.created_at.isoformat(),
        }
