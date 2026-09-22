from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset







T = TypeVar("T", bound="PeerStats")



@_attrs_define
class PeerStats:
    """ Statistics for a single AmneziaWireGuard peer (key).

        Attributes:
            name (str): Key/peer name.
            ip (str): Peer IP address inside the tunnel.
            received (str): Amount of data received, human-readable.
            sent (str): Amount of data sent, human-readable.
            last_handshake (str): Date/time of the last handshake or 'never'.
            status (str): Peer activity status, e.g. Active/Inactive.
     """

    name: str
    ip: str
    received: str
    sent: str
    last_handshake: str
    status: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        name = self.name

        ip = self.ip

        received = self.received

        sent = self.sent

        last_handshake = self.last_handshake

        status = self.status


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "ip": ip,
            "received": received,
            "sent": sent,
            "last_handshake": last_handshake,
            "status": status,
        })

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        ip = d.pop("ip")

        received = d.pop("received")

        sent = d.pop("sent")

        last_handshake = d.pop("last_handshake")

        status = d.pop("status")

        peer_stats = cls(
            name=name,
            ip=ip,
            received=received,
            sent=sent,
            last_handshake=last_handshake,
            status=status,
        )


        peer_stats.additional_properties = d
        return peer_stats

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
