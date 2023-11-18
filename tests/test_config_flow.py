"""Test the Network serial port config flow."""
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from custom_components.network_serial_port.config_flow import CannotConnect, InvalidAuth
from custom_components.network_serial_port.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

pytestmark = pytest.mark.usefixtures("mock_setup_entry")


async def test_form(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert not result["errors"]

    with patch(
        "custom_components.network_serial_port.config_flow.validate_input",
        return_value={"title": "Title"},
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "serial_url": "Serial URL handler",
                "baudrate": 12345,
                "tcp_port": 54321,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Title"
    assert result2["data"] == {
        "serial_url": "Serial URL handler",
        "baudrate": 12345,
        "tcp_port": 54321,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.network_serial_port.config_flow.validate_input",
        side_effect=CannotConnect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "serial_url": "Serial URL handler",
                "baudrate": 12345,
                "tcp_port": 54321,
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}
