import asyncio
import os
from dotenv import load_dotenv
from livekit.api import LiveKitAPI
from livekit.protocol.sip import ListSIPOutboundTrunkRequest, ListSIPInboundTrunkRequest

load_dotenv("/home/vishal/livekit_vienna/Vienna-main/.env.local")

async def main():
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    print(f"URL: {url}")
    print(f"Key: {api_key}")
    
    http_url = url.replace("wss://", "https://").replace("ws://", "http://")
    api = LiveKitAPI(http_url, api_key, api_secret)
    try:
        outbound_trunks_res = await api.sip.list_outbound_trunk(ListSIPOutboundTrunkRequest())
        print("=== OUTBOUND TRUNKS ===")
        for t in outbound_trunks_res.items:
            print(f"- ID: {t.sip_trunk_id}, Name: {t.name}, Address: {t.address}, Numbers: {t.numbers}")
            
        inbound_trunks_res = await api.sip.list_inbound_trunk(ListSIPInboundTrunkRequest())
        print("=== INBOUND TRUNKS ===")
        for t in inbound_trunks_res.items:
            print(f"- ID: {t.sip_trunk_id}, Name: {t.name}, Numbers: {t.numbers}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await api.aclose()

if __name__ == "__main__":
    asyncio.run(main())
