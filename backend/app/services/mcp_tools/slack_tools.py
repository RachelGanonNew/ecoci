"""
Slack Tools for MCP Server

This module provides tools for interacting with the Slack API through the MCP server.
"""
import json
import logging
import hmac
import hashlib
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

import httpx
from fastapi import HTTPException, status
from pydantic import BaseModel, HttpUrl

from app.core.config import settings
from app.services.mcp_server import ToolDefinition

logger = logging.getLogger(__name__)

# Tool Definitions
SEND_MESSAGE_TOOL = {
    "name": "slack.send_message",
    "description": "Send a message to a Slack channel or user",
    "parameters": {
        "channel": {"type": "string", "description": "Channel or user ID to send the message to (e.g., 'C1234567890' or '@username')"},
        "text": {"type": "string", "description": "The message text"},
        "blocks": {"type": "array", "items": {"type": "object"}, "description": "Message blocks for rich formatting"},
        "attachments": {"type": "array", "items": {"type": "object"}, "description": "Message attachments"},
        "thread_ts": {"type": "string", "description": "Thread timestamp to reply to a thread"},
        "as_user": {"type": "boolean", "description": "Pass true to post the message as the authed user", "default": False}
    },
    "required": ["channel", "text"]
}

OPEN_MODAL_TOOL = {
    "name": "slack.open_modal",
    "description": "Open a Slack modal dialog",
    "parameters": {
        "trigger_id": {"type": "string", "description": "Trigger ID from a Slack interaction"},
        "view": {"type": "object", "description": "View payload for the modal"}
    },
    "required": ["trigger_id", "view"]
}

UPDATE_MESSAGE_TOOL = {
    "name": "slack.update_message",
    "description": "Update an existing Slack message",
    "parameters": {
        "channel": {"type": "string", "description": "Channel containing the message"},
        "ts": {"type": "string", "description": "Timestamp of the message to update"},
        "text": {"type": "string", "description": "New text for the message"},
        "blocks": {"type": "array", "items": {"type": "object"}, "description": "New blocks for the message"},
        "attachments": {"type": "array", "items": {"type": "object"}, "description": "New attachments for the message"}
    },
    "required": ["channel", "ts"]
}

class SlackTools:
    """Slack tools for the MCP server."""
    
    def __init__(self):
        self.token = settings.SLACK_BOT_TOKEN
        self.signing_secret = settings.SLACK_SIGNING_SECRET
        self.api_base_url = "https://slack.com/api"
        self.client = httpx.AsyncClient(
            base_url=self.api_base_url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json; charset=utf-8"
            },
            timeout=30.0
        )
    
    async def verify_slack_request(self, request_body: bytes, headers: Dict[str, str]) -> bool:
        """Verify that a request is coming from Slack."""
        try:
            # Get the signature and timestamp from headers
            signature = headers.get("x-slack-signature", "")
            timestamp = headers.get("x-slack-request-timestamp", "")
            
            # Check if the timestamp is too old (replay attack protection)
            if abs(time.time() - float(timestamp)) > 60 * 5:
                return False
            
            # Create the signature base string
            sig_basestring = f"v0:{timestamp}:{request_body.decode('utf-8')}"
            
            # Create a new HMAC "signature"
            my_signature = 'v0=' + hmac.new(
                self.signing_secret.encode('utf-8'),
                sig_basestring.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare the signatures
            return hmac.compare_digest(my_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying Slack request: {str(e)}")
            return False
    
    async def send_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
        as_user: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a message to a Slack channel or user.
        
        Args:
            channel: Channel or user ID to send the message to
            text: The message text
            blocks: Message blocks for rich formatting
            attachments: Message attachments
            thread_ts: Thread timestamp to reply to a thread
            as_user: Pass true to post the message as the authed user
            
        Returns:
            Dictionary containing the message response
        """
        try:
            payload = {
                "channel": channel,
                "text": text,
                "as_user": as_user
            }
            
            if blocks:
                payload["blocks"] = blocks
            if attachments:
                payload["attachments"] = attachments
            if thread_ts:
                payload["thread_ts"] = thread_ts
            
            response = await self.client.post(
                "/chat.postMessage",
                json=payload
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok", False):
                error = data.get("error", "unknown_error")
                raise Exception(f"Slack API error: {error}")
            
            return {
                "channel": data.get("channel"),
                "ts": data.get("ts"),
                "message": {
                    "text": data.get("message", {}).get("text"),
                    "user": data.get("message", {}).get("user"),
                    "bot_id": data.get("message", {}).get("bot_id"),
                    "type": data.get("message", {}).get("type")
                },
                "response_metadata": data.get("response_metadata", {})
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending Slack message: {str(e)}")
            raise Exception(f"Failed to send message: {str(e)}")
        except Exception as e:
            logger.error(f"Error sending Slack message: {str(e)}", exc_info=True)
            raise Exception(f"Failed to send message: {str(e)}")
    
    async def open_modal(
        self,
        trigger_id: str,
        view: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Open a Slack modal dialog.
        
        Args:
            trigger_id: Trigger ID from a Slack interaction
            view: View payload for the modal
            
        Returns:
            Dictionary containing the modal response
        """
        try:
            payload = {
                "trigger_id": trigger_id,
                "view": view
            }
            
            response = await self.client.post(
                "/views.open",
                json=payload
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok", False):
                error = data.get("error", "unknown_error")
                raise Exception(f"Slack API error: {error}")
            
            return {
                "view_id": data.get("view", {}).get("id"),
                "response_metadata": data.get("response_metadata", {})
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error opening Slack modal: {str(e)}")
            raise Exception(f"Failed to open modal: {str(e)}")
        except Exception as e:
            logger.error(f"Error opening Slack modal: {str(e)}", exc_info=True)
            raise Exception(f"Failed to open modal: {str(e)}")
    
    async def update_message(
        self,
        channel: str,
        ts: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update an existing Slack message.
        
        Args:
            channel: Channel containing the message
            ts: Timestamp of the message to update
            text: New text for the message
            blocks: New blocks for the message
            attachments: New attachments for the message
            
        Returns:
            Dictionary containing the update response
        """
        try:
            payload = {
                "channel": channel,
                "ts": ts
            }
            
            if text is not None:
                payload["text"] = text
            if blocks is not None:
                payload["blocks"] = blocks
            if attachments is not None:
                payload["attachments"] = attachments
            
            response = await self.client.post(
                "/chat.update",
                json=payload
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok", False):
                error = data.get("error", "unknown_error")
                raise Exception(f"Slack API error: {error}")
            
            return {
                "channel": data.get("channel"),
                "ts": data.get("ts"),
                "text": data.get("text"),
                "message": data.get("message", {})
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error updating Slack message: {str(e)}")
            raise Exception(f"Failed to update message: {str(e)}")
        except Exception as e:
            logger.error(f"Error updating Slack message: {str(e)}", exc_info=True)
            raise Exception(f"Failed to update message: {str(e)}")

# Create a singleton instance
slack_tools = SlackTools()

# Tool registration functions
def register_slack_tools(mcp_server):
    """Register Slack tools with the MCP server."""
    # Register send message tool
    mcp_server.register_tool(
        SEND_MESSAGE_TOOL,
        slack_tools.send_message
    )
    
    # Register open modal tool
    mcp_server.register_tool(
        OPEN_MODAL_TOOL,
        slack_tools.open_modal
    )
    
    # Register update message tool
    mcp_server.register_tool(
        UPDATE_MESSAGE_TOOL,
        slack_tools.update_message
    )
    
    logger.info("Registered Slack tools with MCP server")
