# base/frequencies.py
from base.base_entity import BaseEntity
from utils.validation import check_type, check_non_negative, check_positive, check_list_type
from utils.logging_setup import logger

# Speed of light constant in MHz * cm
C_MHZ_CM = 29979.2458

class IF(BaseEntity):
    def __init__(self, freq: float, bandwidth: float, isactive: bool = True):
        """Initialize an IF object with frequency and bandwidth.

        Args:
            freq (float): Frequency in MHz.
            bandwidth (float): Bandwidth in MHz.
            isactive (bool): Whether the frequency is active (default: True).
        """
        super().__init__(isactive)
        check_non_negative(freq, "Frequency")
        check_non_negative(bandwidth, "Bandwidth")
        self._frequency = freq
        self._bandwidth = bandwidth
        logger.info(f"Initialized IF with frequency={freq} MHz, bandwidth={bandwidth} MHz")

    def activate(self) -> None:
        """Activate IF frequency."""
        super().activate()

    def deactivate(self) -> None:
        """Deactivate IF frequency."""
        super().deactivate()

    def set_if(self, freq: float, bandwidth: float, isactive: bool = True) -> None:
        """Set IF values."""
        check_non_negative(freq, "Frequency")
        check_non_negative(bandwidth, "Bandwidth")
        self._frequency = freq
        self._bandwidth = bandwidth
        self.isactive = isactive
        logger.info(f"Set IF to frequency={freq} MHz, bandwidth={bandwidth} MHz")

    def set_frequency(self, freq: float, isactive: bool = True) -> None:
        """Set IF frequency value in MHz."""
        check_non_negative(freq, "Frequency")
        self._frequency = freq
        self.isactive = isactive
        logger.info(f"Set frequency to {freq} MHz for IF")

    def set_bandwidth(self, bandwidth: float) -> None:
        """Set IF bandwidth value in MHz."""
        check_non_negative(bandwidth, "Bandwidth")
        self._bandwidth = bandwidth
        logger.info(f"Set bandwidth to {bandwidth} MHz for IF")

    def set_frequency_wavelength(self, wavelength_cm: float) -> None:
        """Set IF frequency value in MHz through wavelength value in cm."""
        check_positive(wavelength_cm, "Wavelength")
        self._frequency = C_MHZ_CM / wavelength_cm
        logger.info(f"Set frequency to {self._frequency} MHz from wavelength={wavelength_cm} cm for IF")

    def get_frequency(self) -> float:
        """Return the IF frequency value in MHz."""
        logger.debug(f"Retrieved frequency={self._frequency} MHz for IF")
        return self._frequency

    def get_bandwidth(self) -> float:
        """Return the IF bandwidth value in MHz."""
        logger.debug(f"Retrieved bandwidth={self._bandwidth} MHz for IF")
        return self._bandwidth

    def get_freq_wavelength(self) -> float:
        """Get wavelength in cm for the frequency."""
        if self._frequency == 0:
            logger.error("Frequency cannot be zero for wavelength calculation")
            raise ValueError("Frequency cannot be zero for wavelength calculation!")
        wavelength = C_MHZ_CM / self._frequency
        logger.debug(f"Calculated wavelength={wavelength} cm for frequency={self._frequency} MHz")
        return wavelength

    def to_dict(self) -> dict:
        """Convert IF object to a dictionary for serialization."""
        logger.info(f"Converted IF (frequency={self._frequency} MHz) to dictionary")
        return {
            "frequency": self._frequency,
            "bandwidth": self._bandwidth,
            "isactive": self.isactive
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'IF':
        """Create an IF object from a dictionary."""
        logger.info(f"Created IF from dictionary with frequency={data['frequency']} MHz")
        return cls(
            freq=data["frequency"],
            bandwidth=data["bandwidth"],
            isactive=data["isactive"]
        )

    def __repr__(self) -> str:
        """Return a string representation of IF."""
        logger.debug(f"Generated string representation for IF with frequency={self._frequency} MHz")
        return f"IF(frequency={self._frequency} MHz, bandwidth={self._bandwidth} MHz, isactive={self.isactive})"

class Frequencies(BaseEntity):
    def __init__(self, ifs: list[IF] = None):
        """Initialize Frequencies with a list of IF objects."""
        super().__init__()
        if ifs is not None:
            check_list_type(ifs, IF, "IFs")
        self._data = ifs if ifs is not None else []
        logger.info(f"Initialized Frequencies with {len(self._data)} IFs")

    def add_frequency(self, if_obj: IF) -> None:
        """Add a new IF object."""
        check_type(if_obj, IF, "IF")
        if any(f.get_frequency() == if_obj.get_frequency() for f in self._data):
            logger.error(f"IF with frequency={if_obj.get_frequency()} MHz already exists")
            raise ValueError(f"IF with frequency={if_obj.get_frequency()} MHz already exists!")
        self._data.append(if_obj)
        logger.info(f"Added IF with frequency={if_obj.get_frequency()} MHz to Frequencies")

    def remove_frequency(self, index: int) -> None:
        """Remove frequency by index."""
        try:
            self._data.pop(index)
            logger.info(f"Removed IF at index {index} from Frequencies")
        except IndexError:
            logger.error(f"Invalid frequencies index: {index}")
            raise IndexError("Invalid frequencies index!")

    def get_frequencies(self) -> list[float]:
        """Get list of frequencies in MHz."""
        logger.debug(f"Retrieved frequencies with {len(self._data)} items")
        return [if_obj.get_frequency() for if_obj in self._data]

    def get_bandwidths(self) -> list[float]:
        """Get list of bandwidths in MHz."""
        logger.debug(f"Retrieved bandwidths with {len(self._data)} items")
        return [if_obj.get_bandwidth() for if_obj in self._data]

    def get_all_wavelengths(self) -> list[float]:
        """Get list of wavelengths in cm."""
        logger.debug(f"Retrieved wavelengths with {len(self._data)} items")
        return [if_obj.get_freq_wavelength() for if_obj in self._data]

    def get_data(self) -> list[IF]:
        """Get IFs frequencies and bandwidths."""
        logger.debug(f"Retrieved frequencies and bandwidths with {len(self._data)} items")
        return self._data

    def get_active_frequencies(self) -> list[IF]:
        """Get active IF frequencies."""
        active = [if_obj for if_obj in self._data if if_obj.isactive]
        logger.debug(f"Retrieved {len(active)} active frequencies")
        return active

    def get_inactive_frequencies(self) -> list[IF]:
        """Get inactive IF frequencies."""
        inactive = [if_obj for if_obj in self._data if not if_obj.isactive]
        logger.debug(f"Retrieved {len(inactive)} inactive frequencies")
        return inactive

    def clear(self) -> None:
        """Clear frequencies data."""
        logger.info(f"Cleared {len(self._data)} IFs from Frequencies")
        self._data.clear()

    def activate_all(self) -> None:
        """Activate all frequencies."""
        if not self._data:
            logger.error("No frequencies to activate")
            raise ValueError("No frequencies to activate!")
        for if_obj in self._data:
            if_obj.activate()
        logger.info("Activated all frequencies")

    def deactivate_all(self) -> None:
        """Deactivate all frequencies."""
        if not self._data:
            logger.error("No frequencies to deactivate")
            raise ValueError("No frequencies to deactivate!")
        for if_obj in self._data:
            if_obj.deactivate()
        logger.info("Deactivated all frequencies")

    def to_dict(self) -> dict:
        """Convert Frequencies object to a dictionary for serialization."""
        logger.info(f"Converted Frequencies with {len(self._data)} IFs to dictionary")
        return {"data": [if_obj.to_dict() for if_obj in self._data]}

    @classmethod
    def from_dict(cls, data: dict) -> 'Frequencies':
        """Create a Frequencies object from a dictionary."""
        ifs = [IF.from_dict(if_data) for if_data in data["data"]]
        logger.info(f"Created Frequencies with {len(ifs)} IFs from dictionary")
        return cls(ifs=ifs)

    def __len__(self) -> int:
        """Return the number of IFs in Frequencies."""
        return len(self._data)

    def __repr__(self) -> str:
        """String representation of Frequencies."""
        active_count = len(self.get_active_frequencies())
        logger.debug(f"Generated string representation for Frequencies")
        return f"Frequencies(count={len(self._data)}, active={active_count}, inactive={len(self._data) - active_count})"