
"""
Common interface definition for VehicleSpeedService.

Shared by:
1. Vehicle ECU - Service Provider
2. Instrument Cluster ECU - Service Consumer
"""

from dataclasses import dataclass

from someipy import (
    Event,
    EventGroup,
    Method,
    ServiceBuilder,
    TransportLayerProtocol,
)

from someipy.serialization import SomeIpPayload, Uint16


# ============================================================
# 1. SERVICE IDENTIFICATION
# ============================================================

SERVICE_ID = 0x1234
INSTANCE_ID = 0x5678
MAJOR_VERSION = 1


# ============================================================
# 2. METHOD IDENTIFICATION
# ============================================================

GET_SPEED_METHOD_ID = 0x0001


# ============================================================
# 3. EVENT IDENTIFICATION
# ============================================================

SPEED_CHANGED_EVENT_ID = 0x8001
SPEED_EVENTGROUP_ID = 0x0001


# ============================================================
# 4. NETWORK CONFIGURATION
# ============================================================

INTERFACE_IP = "127.0.0.1"

PROVIDER_PORT = 3000
CONSUMER_PORT = 3002


# ============================================================
# 5. SPEED PAYLOAD DEFINITION
# ============================================================

@dataclass
class SpeedPayload(SomeIpPayload):

    speed_kmph: Uint16

    def __init__(self, speed_kmph: int = 0):

        self.speed_kmph = Uint16(speed_kmph)


# ============================================================
# 6. GET SPEED METHOD
# ============================================================

get_speed_method = Method(
    id=GET_SPEED_METHOD_ID,
    protocol=TransportLayerProtocol.UDP,
)


# ============================================================
# 7. SPEED CHANGED EVENT
# ============================================================

speed_changed_event = Event(
    id=SPEED_CHANGED_EVENT_ID,
    protocol=TransportLayerProtocol.UDP,
)


# ============================================================
# 8. EVENT GROUP
# ============================================================

speed_eventgroup = EventGroup(
    id=SPEED_EVENTGROUP_ID,
    events=[speed_changed_event],
)


# ============================================================
# 9. VEHICLE SPEED SERVICE
# ============================================================

vehicle_speed_service = (
    ServiceBuilder()
    .with_service_id(SERVICE_ID)
    .with_major_version(MAJOR_VERSION)
    .with_method(get_speed_method)
    .with_eventgroup(speed_eventgroup)
    .build()
)


print("VehicleSpeedService interface loaded successfully.")
