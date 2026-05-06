# Voice AI Platform: User Manual

Welcome to your production-grade Voice AI orchestration platform. This manual explains how to configure, scale, and integrate your AI agents with your physical telephony lines using the **SIP Account Model**.

---

## 1. The Core Concept: Brains vs. Pipes
The platform separates your logic into two simple parts:
*   **The Brain (Call Queue)**: Defines *who* is talking (The ElevenLabs Agent) and *what* the business rules are (Retries, Priority).
*   **The Pipe (Telephony Account)**: Defines *how* the call reaches the world (The Vobiz/Twilio line) and *how many* calls can happen at once.

---

## 2. Step 1: Setting up Telephony Accounts
A **Telephony Account** represents a physical resource, like a Vobiz SIP Trunk or a Twilio account.

1.  Navigate to **Voice AI Telephony Account**.
2.  Click **New**.
3.  **Account Name**: Give it a recognizable name (e.g., "Vobiz Line 1").
4.  **Phone Number ID**: Enter the unique ID provided by your provider (e.g., your Vobiz phone ID).
5.  **Max Concurrent Calls**: Set the hard limit for this line (e.g., `3`). The system will never exceed this, even if multiple queues share this account.
6.  **Telephony Provider**: Select your provider (Vobiz/Twilio).

---

## 3. Step 2: Setting up Call Queues
A **Call Queue** is where you define your AI campaign.

1.  Navigate to **Call Queue**.
2.  **AI Provider**: Select "ElevenLabs."
3.  **Default Agent ID**: Enter the ElevenLabs Agent ID for this campaign.
4.  **Telephony Account**: Link this queue to one of your created Accounts. 
    *   *Note: This queue will now automatically inherit the Phone Number ID from that account.*
5.  **Retry Policy**: (Optional) Link a policy to handle busy signals or no-answers.

---

## 4. Step 3: Hardware Isolation & Scaling
For high-volume traffic, you can isolate specific telephony lines to their own physical CPU resources.

### Configuration
On the **Telephony Account** record, look for the **Background Queue Name** field (under Advanced).
*   Default: `default`.
*   Custom: Enter a name like `vobiz_heavy`.

### Execution
To give this account its own dedicated hardware, your server administrator should run the following command on a separate server or process:
```bash
bench worker --queue vobiz_heavy
```
The platform will now automatically route every call from this account to that specific worker, ensuring that heavy traffic on one line never slows down your other agents.

---

## 5. Step 4: Integration (The n8n Webhook)
Triggering a call is designed to be "Zero-Friction." You only need to send a simple JSON payload to the `create_encounter_queue` API.

**Endpoint**: `POST /api/method/voice_ai.voice_ai.processor.create_encounter_queue`

**Payload Example**:
```json
{
    "customer_phone": "9876543210",
    "call_queue": "CQ-00001",
    "submit_now": 1,
    "payload_json": {
        "customer_name": "Vishal",
        "order_amount": "$50.00",
        "custom_variable": "any_value"
    }
}
```
*   **Inheritance**: You don't need to pass Agent IDs or Phone IDs in the API. The system fetches them automatically from your Frappe settings.
*   **Dynamic Data**: Everything inside `payload_json` is passed directly to the ElevenLabs Agent as dynamic variables.

---

## 6. Monitoring & Logs
*   **Encounter Queue**: This is your live dashboard. You can see the `Queue Status`, `Telephony Status` (ringing, busy, completed), and the `Business Outcome` of every call.
*   **Call Summary**: Once a call is finished, the AI-generated **Transcript** and **Summary** are automatically synced back to the Encounter record.
*   **Technical Data**: Check the bottom section of any record for `Session IDs` and `ElevenLabs Conversation IDs` if you need to troubleshoot with support.
