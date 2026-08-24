from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


ALLOWED_STATES = {"prepared", "approved", "sent", "paused", "closed"}


@dataclass(frozen=True)
class EntryPacket:
    packet_id: str
    company: str
    priority: int
    state: str
    channel: str
    recipient: str
    recipient_confidence: str
    objective: str
    message: str
    questions: tuple[str, ...]
    attachments: tuple[str, ...]
    stop_conditions: tuple[str, ...]

    def ready_to_send(self, human_approved: bool = False) -> bool:
        return (
            human_approved
            and self.state == "approved"
            and self.recipient_confidence == "verified"
            and bool(self.message.strip())
        )


def load_entry_packets(path: str | Path) -> tuple[EntryPacket, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    packets = []
    for item in payload["packets"]:
        if item["state"] not in ALLOWED_STATES:
            raise ValueError(f"Invalid state: {item['state']}")
        packet = EntryPacket(
            packet_id=item["packet_id"],
            company=item["company"],
            priority=int(item["priority"]),
            state=item["state"],
            channel=item["channel"],
            recipient=item["recipient"],
            recipient_confidence=item["recipient_confidence"],
            objective=item["objective"],
            message=item["message"],
            questions=tuple(item["questions"]),
            attachments=tuple(item["attachments"]),
            stop_conditions=tuple(item["stop_conditions"]),
        )
        if packet.priority < 1 or packet.priority > 5:
            raise ValueError(f"Priority outside 1..5: {packet.packet_id}")
        if not packet.stop_conditions:
            raise ValueError(f"Missing stop condition: {packet.packet_id}")
        packets.append(packet)
    return tuple(sorted(packets, key=lambda packet: packet.priority))
