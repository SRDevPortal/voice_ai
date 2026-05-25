import asyncio
import os
from dotenv import load_dotenv
from livekit.api import LiveKitAPI
from livekit.protocol.sip import CreateSIPOutboundTrunkRequest, SIPOutboundTrunkInfo

load_dotenv("/home/vishal/livekit_vienna/main gemini live/.env.local")

async def main():
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    http_url = url.replace("wss://", "https://").replace("ws://", "http://")
    print(f"Connecting to LiveKit: {http_url}")
    
    api = LiveKitAPI(http_url, api_key, api_secret)
    try:
        # Create SIP Outbound Trunk Request
        # In Python SDK, api.sip.create_outbound_trunk expects CreateSIPOutboundTrunkRequest
        print("Creating Outbound SIP Trunk on LiveKit Cloud...")
        req = CreateSIPOutboundTrunkRequest(
            trunk=SIPOutboundTrunkInfo(
                name="vobiz-outbound",
                address="c9d96078.sip.vobiz.ai",
                numbers=["+917971543240"]
            )
        )
        res = await api.sip.create_outbound_trunk(req)
        print("Success! Created Outbound Trunk:")
        print(f"Trunk ID: {res.sip_trunk_id}")
        print(f"Name: {res.name}")
        print(f"Address: {res.address}")
        print(f"Numbers: {res.numbers}")
    except Exception as e:
        print(f"Error creating trunk: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await api.aclose()

if __name__ == "__main__":
    asyncio.run(main())
