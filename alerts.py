"""
OSRS Alerts Module
Discord alerting and notification system
"""

import requests
import datetime
import streamlit as st

# Global state
LAST_ALERTS = {}


def send_discord_alert(item, buy, sell, margin):
    """Send Discord alert with rate limiting"""
    global LAST_ALERTS

    discord_webhook_url = st.secrets["discord"]["webhook_url"]
    now = datetime.datetime.now(datetime.timezone.utc)
    last = LAST_ALERTS.get(item)

    # 3 minute cooldown
    cooldown_seconds = 180
    if last and (now - last).total_seconds() < cooldown_seconds:
        remaining_time = cooldown_seconds - (now - last).total_seconds()
        print(f"⏳ Discord alert for {item} on cooldown for {remaining_time:.0f} more seconds")
        return False

    LAST_ALERTS[item] = now

    try:
        payload = f"🚨 **OSRS Flip Alert** 🚨\n**{item}**\n💰 Buy: {buy:,} gp\n💸 Sell: {sell:,} gp\n📈 Net Margin: {margin:,} gp\n⏰ {now.strftime('%H:%M UTC')}"
        response = requests.post(
            discord_webhook_url,
            json={"content": payload},
            headers={"Content-Type": "application/json"},
            timeout=5
        )

        if response.status_code == 200:
            print(f"✅ Discord alert sent for {item}")
            return True
        else:
            print(f"❌ Discord alert failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Discord alert failed: {e}")
        return False


def get_alert_history():
    """Get current alert history"""
    return LAST_ALERTS


def clear_alert_history():
    """Clear all alert history"""
    global LAST_ALERTS
    LAST_ALERTS = {}