from __future__ import annotations
from .call_api import InsnrgPool
from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import aiohttp_client
from . import InsnrgPoolEntity
from .const import DOMAIN
import logging
_LOGGER = logging.getLogger(__name__)
KEYS_TO_CHECK = ["PH", "ORP"]

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Defer number setup to the shared number module."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    number_descriptions = []
    for key in KEYS_TO_CHECK:
        if key in coordinator.data:
            name = coordinator.data[key]['name']
            if coordinator.data[key]["thermostatStatus"]["valueMax"] > 0:
                name =  f"InsnrgPool Set {key} Point"
            number_descriptions.append(NumberEntityDescription(
                key=key,
                name=name,
            ))
    entities = [
        InsnrgPoolNumber(coordinator, hass, config_entry, description)
        for description in number_descriptions
    ]
    async_add_entities(entities, False)

class InsnrgPoolNumber(InsnrgPoolEntity, NumberEntity):
    """Number entity representing Insnrg Pool data."""
    def __init__(self, coordinator, hass, entry, description):
        super().__init__(coordinator, entry, description)
        self.insnrg_pool = InsnrgPool(
            aiohttp_client.async_get_clientsession(hass),
            entry.data[CONF_EMAIL],
            entry.data[CONF_PASSWORD],
        )
    
    @property
    def mode(self) -> str | None:
        """Return the mode."""
        return "slider"

    @property
    def native_max_value(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data[self.entity_description.key]["thermostatStatus"]["valueMax"]
    
    @property
    def native_min_value(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data[self.entity_description.key]["thermostatStatus"]["valueMin"]

    @property
    def native_step(self) -> float:
        """Return the unit of measurement."""
        if self.entity_description.key == "ORP":
            return 10
        else:
            return 0.1

    @property
    def native_value(self) -> float:
        """Return the current temperature."""
        return self.coordinator.data[self.entity_description.key]["thermostatStatus"]["setPoint"]
    
    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        deviceId = self.coordinator.data[self.entity_description.key]["deviceId"]
        success = await self.insnrg_pool.set_chemistry(value, deviceId)
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Set temp failed.")
