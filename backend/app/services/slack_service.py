import logging
from typing import Dict, List, Optional, Any, Union
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.web.slack_response import SlackResponse

from ..config import settings

logger = logging.getLogger(__name__)

class SlackService:
    """Service for interacting with the Slack API."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize the Slack service.
        
        Args:
            token: Slack bot token. If not provided, uses SLACK_BOT_TOKEN from settings.
        """
        self.token = token or settings.SLACK_BOT_TOKEN
        self.client = WebClient(token=self.token) if self.token else None
    
    def send_message(
        self, 
        channel: str, 
        text: str, 
        blocks: Optional[List[Dict]] = None,
        thread_ts: Optional[str] = None,
        **kwargs
    ) -> Optional[SlackResponse]:
        """Send a message to a Slack channel.
        
        Args:
            channel: Channel ID or name (e.g., '#general' or 'C1234567890')
            text: Message text (fallback for notifications)
            blocks: List of block kit blocks for rich formatting
            thread_ts: Timestamp of the thread to reply to
            **kwargs: Additional arguments to pass to chat_postMessage
            
        Returns:
            Slack API response or None if sending failed
        """
        if not self.client:
            logger.warning("Slack client not initialized. Message not sent.")
            return None
            
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks,
                thread_ts=thread_ts,
                **kwargs
            )
            logger.info(f"Message sent to {channel}: {text[:100]}...")
            return response
        except SlackApiError as e:
            logger.error(f"Error sending message to Slack: {e.response['error']}")
            return None
    
    def send_scan_results(
        self, 
        channel: str, 
        scan_results: Dict[str, Any],
        repository_name: str,
        repository_url: str,
        pr_url: Optional[str] = None
    ) -> Optional[SlackResponse]:
        """Send CI/CD scan results to a Slack channel with interactive buttons.
        
        Args:
            channel: Channel ID or name
            scan_results: Dictionary containing scan results
            repository_name: Name of the repository
            repository_url: URL of the repository
            pr_url: Optional URL to the pull request with fixes
            
        Returns:
            Slack API response or None if sending failed
        """
        total_emissions = scan_results.get("total_emissions_kg", 0)
        total_cost = scan_results.get("total_cost_usd", 0)
        potential_savings = scan_results.get("potential_savings", {})
        
        # Format the message
        title = f"🚀 CI/CD Scan Results for {repository_name}"
        
        # Create blocks for the message
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Repository:* <{repository_url}|{repository_name}>\n"
                            f"*Total Emissions:* {total_emissions:.4f} kg CO₂e\n"
                            f"*Estimated Cost:* ${total_cost:.4f} USD"
                }
            },
            {
                "type": "divider"
            }
        ]
        
        # Add potential savings section if available
        if potential_savings:
            emissions_savings = potential_savings.get("total_emissions_savings_kg", 0)
            cost_savings = potential_savings.get("total_cost_savings_usd", 0)
            
            savings_text = (
                f"*Potential Emissions Savings:* {emissions_savings:.4f} kg CO₂e\n"
                f"*Potential Cost Savings:* ${cost_savings:.4f} USD\n"
            )
            
            # Add opportunities
            for opp in potential_savings.get("opportunities", [])[:3]:  # Limit to top 3
                savings_text += f"• *{opp['type'].title()}*: {opp['description']}\n"
            
            blocks.extend([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*💡 Potential Optimizations*\n" + savings_text
                    }
                },
                {
                    "type": "divider"
                }
            ])
        
        # Add actions (buttons)
        actions = []
        
        if pr_url:
            actions.append({
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "View Pull Request",
                    "emoji": True
                },
                "url": pr_url,
                "style": "primary"
            })
        
        actions.extend([
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "View Full Report",
                    "emoji": True
                },
                "url": f"{repository_url}/actions",
                "style": "primary"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Dismiss",
                    "emoji": True
                },
                "value": "dismiss",
                "style": "danger"
            }
        ])
        
        blocks.append({
            "type": "actions",
            "elements": actions
        })
        
        # Send the message
        return self.send_message(
            channel=channel,
            text=title,
            blocks=blocks
        )
    
    def send_approval_request(
        self,
        channel: str,
        pr_title: str,
        pr_url: str,
        repository_name: str,
        changes: List[Dict[str, str]],
        approvers: List[str] = None
    ) -> Optional[SlackResponse]:
        """Send a pull request approval request to a Slack channel.
        
        Args:
            channel: Channel ID or name
            pr_title: Title of the pull request
            pr_url: URL to the pull request
            repository_name: Name of the repository
            changes: List of changes in the PR
            approvers: List of user IDs or usernames to mention as approvers
            
        Returns:
            Slack API response or None if sending failed
        """
        # Format approvers
        approvers_text = ""
        if approvers:
            mentions = [f"<@{user}>" for user in approvers]
            approvers_text = f"*Approvers:* {' '.join(mentions)}\n\n"
        
        # Format changes
        changes_text = "*Changes in this PR:*\n"
        for i, change in enumerate(changes[:5], 1):  # Limit to 5 changes
            changes_text += f"{i}. {change.get('description', 'No description')} "
            changes_text += f"(*{change.get('type', 'change')}*)\n"
        
        if len(changes) > 5:
            changes_text += f"\n...and {len(changes) - 5} more changes"
        
        # Create blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "✅ Pull Request Approval Requested",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{pr_title}*\n"
                            f"*Repository:* {repository_name}\n"
                            f"{approvers_text}\n"
                            f"{changes_text}"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View PR",
                        "emoji": True
                    },
                    "url": pr_url,
                    "style": "primary"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Approve & Merge",
                            "emoji": True
                        },
                        "value": f"approve_pr:{repository_name}:{pr_url.split('/')[-1]}",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Request Changes",
                            "emoji": True
                        },
                        "value": "request_changes",
                        "style": "danger"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Details",
                            "emoji": True
                        },
                        "url": pr_url
                    }
                ]
            }
        ]
        
        return self.send_message(
            channel=channel,
            text=f"Approval requested for PR: {pr_title}",
            blocks=blocks
        )
    
    def update_message(
        self, 
        channel: str, 
        ts: str, 
        text: str, 
        blocks: Optional[List[Dict]] = None,
        **kwargs
    ) -> Optional[SlackResponse]:
        """Update an existing Slack message.
        
        Args:
            channel: Channel ID
            ts: Timestamp of the message to update
            text: New message text
            blocks: New blocks for the message
            **kwargs: Additional arguments to pass to chat_update
            
        Returns:
            Slack API response or None if update failed
        """
        if not self.client:
            logger.warning("Slack client not initialized. Message not updated.")
            return None
            
        try:
            response = self.client.chat_update(
                channel=channel,
                ts=ts,
                text=text,
                blocks=blocks,
                **kwargs
            )
            logger.info(f"Message {ts} in {channel} updated")
            return response
        except SlackApiError as e:
            logger.error(f"Error updating Slack message: {e.response['error']}")
            return None
    
    def handle_interaction(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle Slack interactive component interactions.
        
        Args:
            payload: The interaction payload from Slack
            
        Returns:
            Response to send back to Slack or None
        """
        if not payload:
            return None
            
        action_type = payload.get("type")
        
        if action_type == "block_actions":
            # Handle button clicks, select menus, etc.
            actions = payload.get("actions", [])
            if not actions:
                return None
                
            action = actions[0]
            action_id = action.get("action_id")
            value = action.get("value")
            
            # Handle different action types
            if action_id == "approve_pr" and value:
                # Handle PR approval
                _, repo, pr_number = value.split(":")
                return self._handle_pr_approval(payload, repo, pr_number)
                
            elif action_id == "request_changes":
                # Handle request changes
                return self._handle_request_changes(payload)
                
        return None
    
    def _handle_pr_approval(
        self, 
        payload: Dict[str, Any],
        repository: str,
        pr_number: str
    ) -> Dict[str, Any]:
        """Handle PR approval from Slack."""
        user = payload.get("user", {})
        user_id = user.get("id")
        user_name = user.get("username")
        
        # In a real implementation, you would:
        # 1. Verify the user has permission to approve
        # 2. Call the GitHub API to approve the PR
        # 3. Optionally merge the PR
        
        # For now, just return a confirmation message
        return {
            "response_type": "in_channel",
            "replace_original": True,
            "text": f"✅ PR #{pr_number} in {repository} approved by <@{user_id}>"
        }
    
    def _handle_request_changes(
        self, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle request changes from Slack."""
        user = payload.get("user", {})
        user_id = user.get("id")
        
        # In a real implementation, you would:
        # 1. Post a comment on the PR requesting changes
        # 2. Possibly update the PR status
        
        return {
            "response_type": "ephemeral",
            "replace_original": False,
            "text": f"<@{user_id}> has requested changes to this PR. "
                    "Please update the PR and request another review when ready."
        }
