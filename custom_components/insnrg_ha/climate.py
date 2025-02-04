from __future__ import annotations
from .call_api import InsnrgPool
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import aiohttp_client
from . import InsnrgPoolEntity
from .const import DOMAIN
import logging
_LOGGER = logging.getLogger(__name__)
KEYS_TO_CHECK = ["SPA_CONTROL", "POOL_CONTROL"]

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Defer climate setup to the shared climate module."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    climate_descriptions = []
    for key in KEYS_TO_CHECK:
        if key in coordinator.data:
            climate_descriptions.append(ClimateEntityDescription(
                key=key,
                name=coordinator.data[key]['name'],
            ))
    entities = [
        InsnrgPoolClimate(coordinator, hass, config_entry, description)
        for description in climate_descriptions
    ]
    async_add_entities(entities, False)

class InsnrgPoolClimate(InsnrgPoolEntity, ClimateEntity):
    """Climate entity representing Insnrg Pool data."""
    _attr_hvac_modes = [None]
    _attr_hvac_mode = None
    def __init__(self, coordinator, hass, entry, description):
        super().__init__(coordinator, entry, description)
        self.insnrg_pool = InsnrgPool(
            aiohttp_client.async_get_clientsession(hass),
            entry.data[CONF_EMAIL],
            entry.data[CONF_PASSWORD],
        )
    
    @property
    def supported_features(self) -> str | None:
        """Return the current temperature."""
        return ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def max_temp(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data[self.entity_description.key]["thermostatStatus"]["valueMax"]
    
    @property
    def min_temp(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data[self.entity_description.key]["thermostatStatus"]["valueMin"]

    @property
    def target_temperature_step(self) -> str:
        """Return the unit of measurement."""
        if self.entity_description.key == "PH":
            return 0.1
        elif self.entity_description.key == "ORP":
            return 10
        else:
            return 0.5

    @property
    def temperature_unit(self) -> float:
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data[self.entity_description.key]["temperatureSensorStatus"]["value"]

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        if 'ggPoolSetTemperature' in self.coordinator.data[self.entity_description.key]["thermostatStatus"]:
            return self.coordinator.data[self.entity_description.key]["thermostatStatus"]["ggPoolSetTemperature"]
        else:
            return self.coordinator.data[self.entity_description.key]["thermostatStatus"]["value"]
    
    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temp_value = kwargs.get("temperature")
        deviceId = self.coordinator.data[self.entity_description.key]["deviceId"]
        success = await self.insnrg_pool.set_thermostat_temp(temp_value, deviceId)
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Set temp failed.")
