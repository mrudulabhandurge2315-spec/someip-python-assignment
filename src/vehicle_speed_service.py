
import asyncio

from someipy import (
    Method,
    MethodResult,
    MessageType,
    ReturnCode,
    ServerServiceInstance,
    ServiceBuilder,
    TransportLayerProtocol,
    connect_to_someipy_daemon,
)

from src.vehicle_speed_interface import (
    SERVICE_ID,
    INSTANCE_ID,
    MAJOR_VERSION,
    GET_SPEED_METHOD_ID,
    SPEED_CHANGED_EVENT_ID,
    SPEED_EVENTGROUP_ID,
    INTERFACE_IP,
    PROVIDER_PORT,
    SpeedPayload,
    speed_eventgroup,
)

# Initial simulated vehicle speed
current_speed = 40


# SOME/IP method handler for GetSpeed
def get_speed_handler(request_payload: bytes, client_address: tuple) -> MethodResult:
    global current_speed

    print("\n[VEHICLE ECU] GetSpeed request received")
    print(f"[VEHICLE ECU] Client address: {client_address}")

    result = MethodResult()

    if len(request_payload) != 0:
        result.message_type = MessageType.ERROR
        result.return_code = ReturnCode.E_MALFORMED_MESSAGE
        result.payload = b""
        return result

    speed_response = SpeedPayload(current_speed)

    result.message_type = MessageType.RESPONSE
    result.return_code = ReturnCode.E_OK
    result.payload = speed_response.serialize()

    print(f"[VEHICLE ECU] Sending speed: {current_speed} km/h")

    return result


# Create the service with the GetSpeed handler
get_speed_method = Method(
    id=GET_SPEED_METHOD_ID,
    protocol=TransportLayerProtocol.UDP,
    method_handler=get_speed_handler,
)

vehicle_speed_service = (
    ServiceBuilder()
    .with_service_id(SERVICE_ID)
    .with_major_version(MAJOR_VERSION)
    .with_method(get_speed_method)
    .with_eventgroup(speed_eventgroup)
    .build()
)


async def main():

    global current_speed

    daemon = None
    service_instance = None

    try:
        print("\n========================================")
        print("       VEHICLE ECU PROVIDER")
        print("========================================")

        print("[VEHICLE ECU] Connecting to someipy daemon...")

        daemon = await connect_to_someipy_daemon()

        print("[VEHICLE ECU] Connected to daemon successfully")

        # Create the SOME/IP server instance
        service_instance = ServerServiceInstance(
            daemon=daemon,
            service=vehicle_speed_service,
            instance_id=INSTANCE_ID,
            endpoint_ip=INTERFACE_IP,
            endpoint_port=PROVIDER_PORT,
            ttl=5,
            cyclic_offer_delay_ms=2000,
        )

        # Announce the service through SOME/IP Service Discovery
        await service_instance.start_offer()

        print("\n[VEHICLE ECU] Service offered successfully")
        print(f"[VEHICLE ECU] Service ID: 0x{SERVICE_ID:04X}")
        print(f"[VEHICLE ECU] Instance ID: 0x{INSTANCE_ID:04X}")
        print(f"[VEHICLE ECU] Endpoint: {INTERFACE_IP}:{PROVIDER_PORT}")
        print("[VEHICLE ECU] Waiting for GetSpeed requests...")
        print("[VEHICLE ECU] Publishing SpeedChanged every 2 seconds")
        print("\nPress CTRL+C to stop the provider.")
        print("----------------------------------------")

        # Publish speed notifications every 2 seconds
        while True:

            await asyncio.sleep(2)

            # Simulate a changing vehicle speed
            current_speed += 5

            if current_speed > 80:
                current_speed = 40

            speed_event = SpeedPayload(current_speed)

            service_instance.send_event(
                SPEED_EVENTGROUP_ID,
                SPEED_CHANGED_EVENT_ID,
                speed_event.serialize(),
            )

            print(
                f"[VEHICLE ECU] SpeedChanged event published: "
                f"{current_speed} km/h"
            )

    except asyncio.CancelledError:
        print("\n[VEHICLE ECU] Application cancelled")

    except Exception as error:
        print(f"\n[VEHICLE ECU] Error: {error}")
        raise

    finally:
        if service_instance is not None:
            print("[VEHICLE ECU] Stopping service offer...")
            await service_instance.stop_offer()

        if daemon is not None:
            print("[VEHICLE ECU] Disconnecting from daemon...")


            for attempt in range(3):
                try:
                    await daemon.disconnect_from_daemon()
                    print("[VEHICLE ECU] Disconnected successfully")
                    break

                except asyncio.TimeoutError:
                    if attempt < 2:
                        print(
                            f"[VEHICLE ECU] Disconnect timed out. "
                            f"Retrying ({attempt + 2}/3)..."
                        )
                        await asyncio.sleep(0.2)
                    else:
                        print(
                            "[VEHICLE ECU] Warning: daemon shutdown "
                            "timed out after 3 attempts."
                        )

        print("[VEHICLE ECU] Provider stopped")


if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\n[VEHICLE ECU] Stopped by user")
