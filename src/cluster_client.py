import asyncio

from someipy import (
    ClientServiceInstance,
    MessageType,
    ReturnCode,
    connect_to_someipy_daemon,
)

from src.vehicle_speed_interface import (
    INSTANCE_ID,
    INTERFACE_IP,
    CONSUMER_PORT,
    GET_SPEED_METHOD_ID,
    SPEED_CHANGED_EVENT_ID,
    SPEED_EVENTGROUP_ID,
    SpeedPayload,
    vehicle_speed_service,
    speed_eventgroup,
)


def decode_speed(payload: bytes) -> int:
    decoded = SpeedPayload()
    decoded.deserialize(payload)
    return decoded.speed_kmph.value

def on_speed_changed(event_id: int, payload: bytes) -> None:
    """Handle SpeedChanged notifications from the Vehicle ECU."""
    if event_id != SPEED_CHANGED_EVENT_ID:
        return

    try:
        speed = decode_speed(payload)
        print(f"[CLUSTER] SpeedChanged event received: {speed} km/h")
    except Exception as error:
        print(f"[CLUSTER] Could not decode event: {error}")


async def main():
    daemon = None
    client_instance = None

    try:
        print("========================================")
        print("     INSTRUMENT CLUSTER CLIENT")
        print("========================================")

        # Connect the client application to the someipy daemon.
        daemon = await connect_to_someipy_daemon()
        print("[CLUSTER] Connected to someipy daemon")

        # Create the client service instance.
        client_instance = ClientServiceInstance(
            daemon=daemon,
            service=vehicle_speed_service,
            instance_id=INSTANCE_ID,
            endpoint_ip=INTERFACE_IP,
            endpoint_port=CONSUMER_PORT,
        )

        # Register the callback for incoming event notifications.
        client_instance.register_callback(on_speed_changed)

        print("[CLUSTER] Waiting for VehicleSpeedService...")

        available = False

        for attempt in range(10):
            available = await client_instance.is_available()

            if available:
                break

            await asyncio.sleep(1)

        if not available:
            print("[CLUSTER] VehicleSpeedService was not found.")
            print("[CLUSTER] Check that the daemon and provider are running.")
            return

        print("[CLUSTER] VehicleSpeedService is available!")

        # Subscribe to the SpeedChanged event group.
        client_instance.subscribe_eventgroup(
            speed_eventgroup,
            ttl_subscription_seconds=30,
        )

        print("[CLUSTER] Subscribed to SpeedChanged event group")

        # Send GetSpeed request.
        print("[CLUSTER] Sending GetSpeed request...")

        result = await client_instance.call_method(
            GET_SPEED_METHOD_ID,
            b"",
        )
        if (
            result.message_type == MessageType.RESPONSE
            and result.return_code == ReturnCode.E_OK
        ):
            speed = decode_speed(result.payload)
            print(f"[CLUSTER] GetSpeed response: {speed} km/h")
        else:
            print("[CLUSTER] GetSpeed request failed.")
            print(f"[CLUSTER] Message type: {result.message_type}")
            print(f"[CLUSTER] Return code: {result.return_code}")

        print("----------------------------------------")
        print("[CLUSTER] Listening for SpeedChanged events")
        print("[CLUSTER] Press Ctrl+C to stop")
        print("----------------------------------------")

        # Keep the client running to receive event notifications.
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n[CLUSTER] Stopped by user")

    except Exception as error:
        print(f"[CLUSTER] Error: {error}")

    finally:
        if client_instance is not None:
            try:
                client_instance.unsubscribe_eventgroup(speed_eventgroup)
                print("[CLUSTER] Unsubscribed from event group")
            except Exception as error:
                print(f"[CLUSTER] Unsubscribe warning: {error}")

        if daemon is not None:
            for attempt in range(3):
                try:
                    await daemon.disconnect_from_daemon()
                    print("[CLUSTER] Disconnected from daemon")
                    break

                except asyncio.TimeoutError:
                    if attempt < 2:
                        print(
                            f"[CLUSTER] Disconnect timed out. "
                            f"Retrying ({attempt + 2}/3)..."
                        )
                        await asyncio.sleep(0.2)
                    else:
                        print(
                            "[CLUSTER] Warning: daemon shutdown "
                            "timed out after 3 attempts."
                        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n[CLUSTER] Stopped by user")
