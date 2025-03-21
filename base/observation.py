# base/observation.py
from base.base_entity import BaseEntity
from base.sources import Source, Sources
from base.telescopes import Telescope, SpaceTelescope, Telescopes
from base.frequencies import Frequencies, IF
from base.scans import Scans
from utils.validation import check_type, check_non_empty_string
from utils.logging_setup import logger
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
import astropy.units as u
import numpy as np
import re

class Observation(BaseEntity):
    def __init__(self, observation_code: str = "OBS_DEFAULT", sources: Sources = None,
                 telescopes: Telescopes = None, frequencies: Frequencies = None,
                 scans: Scans = None, observation_type: str = "VLBI", isactive: bool = True):
        """Initialize an Observation object."""
        super().__init__(isactive)
        check_type(observation_code, str, "Observation code")
        if observation_type not in ("VLBI", "SINGLE_DISH"):
            logger.error(f"Observation type must be 'VLBI' or 'SINGLE_DISH', got {observation_type}")
            raise ValueError(f"Observation type must be 'VLBI' or 'SINGLE_DISH', got {observation_type}")
        if sources is not None:
            check_type(sources, Sources, "Sources")
        if telescopes is not None:
            check_type(telescopes, Telescopes, "Telescopes")
        if frequencies is not None:
            check_type(frequencies, Frequencies, "Frequencies")
        if scans is not None:
            check_type(scans, Scans, "Scans")
        self._observation_code = observation_code
        self._observation_type = observation_type
        self._sources = sources if sources is not None else Sources()
        self._telescopes = telescopes if telescopes is not None else Telescopes()
        self._frequencies = frequencies if frequencies is not None else Frequencies()
        self._scans = scans if scans is not None else Scans()
        self._sources._parent = self
        self._telescopes._parent = self
        self._frequencies._parent = self
        self._scans._parent = self
        self._calculated_data: Dict[str, Any] = {} # Хранилище для результатов Calculator
        logger.info(f"Initialized Observation '{observation_code}' with type '{observation_type}'")

    def set_observation(self, observation_code: str, sources: Sources = None,
                        telescopes: Telescopes = None, frequencies: Frequencies = None,
                        scans: Scans = None, observation_type: str = "VLBI", isactive: bool = True) -> None:
        """Set observation parameters."""
        check_type(observation_code, str, "Observation code")
        if observation_type not in ("VLBI", "SINGLE_DISH"):
            logger.error(f"Observation type must be 'VLBI' or 'SINGLE_DISH', got {observation_type}")
            raise ValueError(f"Observation type must be 'VLBI' or 'SINGLE_DISH', got {observation_type}")
        if sources is not None:
            check_type(sources, Sources, "Sources")
        if telescopes is not None:
            check_type(telescopes, Telescopes, "Telescopes")
        if frequencies is not None:
            check_type(frequencies, Frequencies, "Frequencies")
        if scans is not None:
            check_type(scans, Scans, "Scans")
        self._observation_code = observation_code
        self._observation_type = observation_type
        self._sources = sources if sources is not None else Sources()
        self._telescopes = telescopes if telescopes is not None else Telescopes()
        self._frequencies = frequencies if frequencies is not None else Frequencies()
        self._scans = scans if scans is not None else Scans()
        self.isactive = isactive
        self._calculated_data.clear()  # Очищаем результаты при полной переустановке параметров
        logger.info(f"Set observation '{observation_code}' with type '{observation_type}'")

    def set_observation_code(self, observation_code: str) -> None:
        """Set observation code."""
        check_type(observation_code, str, "Observation code")
        self._observation_code = observation_code
        logger.info(f"Set observation code to '{observation_code}'")

    def set_sources(self, sources: Sources) -> None:
        """Set observation sources."""
        check_type(sources, Sources, "Sources")
        self._sources = sources
        self._calculated_data.clear()  # Очищаем результаты, так как данные изменились
        logger.info(f"Set sources for observation '{self._observation_code}'")

    def set_telescopes(self, telescopes: Telescopes) -> None:
        """Set observation telescopes."""
        check_type(telescopes, Telescopes, "Telescopes")
        self._telescopes = telescopes
        self._calculated_data.clear()  # Очищаем результаты, так как данные изменились
        logger.info(f"Set telescopes for observation '{self._observation_code}'")

    def set_frequencies(self, frequencies: Frequencies) -> None:
        """Set observation frequencies with polarizations."""
        check_type(frequencies, Frequencies, "Frequencies")
        self._frequencies = frequencies
        self._calculated_data.clear()  # Очищаем результаты, так как данные изменились
        logger.info(f"Set frequencies with polarizations for observation '{self._observation_code}'")

    def set_scans(self, scans: Scans) -> None:
        """Set observation scans."""
        check_type(scans, Scans, "Scans")
        self._scans = scans
        self._calculated_data.clear()  # Очищаем результаты, так как данные изменились
        logger.info(f"Set scans for observation '{self._observation_code}'")

    def set_calculated_data(self, key: str, data: Any) -> None:
        """Save calculated data for this observation."""
        check_non_empty_string(key, "Key")
        self._calculated_data[key] = data
        logger.info(f"Stored calculated data '{key}' for observation '{self._observation_code}'")

    def get_calculated_data(self, key: str) -> Any:
        """Retrieve calculated data by key."""
        check_non_empty_string(key, "Key")
        return self._calculated_data.get(key)

    def get_observation_code(self) -> str:
        """Get observation code."""
        return self._observation_code
    
    def get_observation_type(self) -> str:
        """Get observation type."""
        return self._observation_type

    def get_sources(self) -> Sources:
        """Get observation sources."""
        return self._sources

    def get_telescopes(self) -> Telescopes:
        """Get observation telescopes."""
        return self._telescopes

    def get_frequencies(self) -> Frequencies:
        """Get observation frequencies."""
        return self._frequencies

    def get_scans(self) -> Scans:
        """Get observation scans."""
        return self._scans

    def get_start_datetime(self) -> Optional[datetime]:
        """Get observation start time as a datetime object (UTC), based on earliest scan."""
        active_scans = self._scans.get_active_scans(self)  # Передаем self
        if not active_scans:
            return None
        return min(scan.get_start_datetime() for scan in active_scans)
    
    def _update_scan_indices(self, entity_type: str, removed_index: Optional[int] = None, inserted_index: Optional[int] = None) -> None:
        """Update scan indices after adding/removing sources, telescopes, or frequencies."""
        entity_map = {"sources": "_source_index", "telescopes": "_telescope_indices", "frequencies": "_frequency_indices"}
        if entity_type not in entity_map:
            raise ValueError(f"Invalid entity type: {entity_type}")
        attr = entity_map[entity_type]
        
        for scan in self._scans.get_all_scans():
            if entity_type == "sources":
                current_idx = getattr(scan, attr)
                if removed_index is not None and current_idx is not None:
                    if current_idx == removed_index:
                        scan.set_source_index(None)  # Источник удалён, сбрасываем
                        scan.is_off_source = True
                    elif current_idx > removed_index:
                        scan.set_source_index(current_idx - 1)
                elif inserted_index is not None and current_idx is not None and current_idx >= inserted_index:
                    scan.set_source_index(current_idx + 1)
            else:  # telescopes or frequencies
                current_indices = getattr(scan, attr)
                updated_indices = []
                for idx in current_indices:
                    if removed_index is not None:
                        if idx == removed_index:
                            continue  # Пропускаем удалённый индекс
                        elif idx > removed_index:
                            updated_indices.append(idx - 1)
                        else:
                            updated_indices.append(idx)
                    elif inserted_index is not None:
                        if idx >= inserted_index:
                            updated_indices.append(idx + 1)
                        else:
                            updated_indices.append(idx)
                if removed_index is not None or inserted_index is not None:
                    if entity_type == "telescopes":
                        scan.set_telescope_indices(updated_indices)
                    else:
                        scan.set_frequency_indices(updated_indices)
        logger.debug(f"Updated scan indices for {entity_type} in observation '{self._observation_code}'")
    
    def remove_source(self, index: int) -> None:
        """Remove a source and update scan indices."""
        check_type(index, int, "Index")
        self._sources.remove_source(index)
        self._update_scan_indices("sources", removed_index=index)
        logger.info(f"Removed source at index {index} and updated scan indices")

    def insert_source(self, source: Source, index: int) -> None:
        """Insert a source and update scan indices."""
        check_type(source, Source, "Source")
        check_type(index, int, "Index")
        self._sources._data.insert(index, source)
        self._update_scan_indices("sources", inserted_index=index)
        logger.info(f"Inserted source '{source.get_name()}' at index {index} and updated scan indices")

    def remove_telescope(self, index: int) -> None:
        """Remove a telescope and update scan indices."""
        check_type(index, int, "Index")
        self._telescopes.remove_telescope(index)
        self._update_scan_indices("telescopes", removed_index=index)
        logger.info(f"Removed telescope at index {index} and updated scan indices")

    def insert_telescope(self, telescope: Union[Telescope, SpaceTelescope], index: int) -> None:
        """Insert a telescope and update scan indices."""
        check_type(telescope, (Telescope, SpaceTelescope), "Telescope")
        check_type(index, int, "Index")
        self._telescopes._data.insert(index, telescope)
        self._update_scan_indices("telescopes", inserted_index=index)
        logger.info(f"Inserted telescope '{telescope.get_telescope_code()}' at index {index} and updated scan indices")

    def remove_frequency(self, index: int) -> None:
        """Remove a frequency and update scan indices."""
        check_type(index, int, "Index")
        self._frequencies.remove_frequency(index)
        self._update_scan_indices("frequencies", removed_index=index)
        logger.info(f"Removed frequency at index {index} and updated scan indices")

    def insert_frequency(self, if_obj: IF, index: int) -> None:
        """Insert a frequency and update scan indices."""
        check_type(if_obj, IF, "IF")
        check_type(index, int, "Index")
        self._frequencies._data.insert(index, if_obj)
        self._update_scan_indices("frequencies", inserted_index=index)
        logger.info(f"Inserted frequency {if_obj.get_frequency()} MHz at index {index} and updated scan indices")

    def validate(self) -> bool:
        """Validate the observation parameters."""
        from utils.validation import check_type, check_positive_float, check_list_not_empty

        # Check observation code
        if not self._observation_code or not isinstance(self._observation_code, str):
            logger.error("Observation code must be a non-empty string")
            return False

        # Check observation type
        if self._observation_type not in ["VLBI", "SINGLE_DISH"]:
            logger.error(f"Invalid observation type: {self._observation_type}. Must be 'VLBI' or 'SINGLE_DISH'")
            return False

        # Validate SEFD
        check_positive_float(self._sefd, "SEFD")

        # Validate sources
        if not self._sources.get_active_sources():
            logger.error("No active sources defined in observation")
            return False
        for source in self._sources.get_active_sources():
            if not source.validate():
                logger.error(f"Source validation failed for {source.get_name()}")
                return False

        # Validate telescopes
        if not self._telescopes.get_active_telescopes():
            logger.error("No active telescopes defined in observation")
            return False
        for telescope in self._telescopes.get_active_telescopes():
            if not telescope.validate():
                logger.error(f"Telescope validation failed for {telescope.get_telescope_code()}")
                return False

        # Validate frequencies
        if not self._frequencies.get_active_frequencies():
            logger.error("No active frequencies defined in observation")
            return False
        for freq in self._frequencies.get_active_frequencies():
            if not freq.validate():
                logger.error(f"Frequency validation failed for {freq}")
                return False

        # Validate scans
        if not self._scans.get_active_scans(self):  # Передаем self
            logger.error("No active scans defined in observation")
            return False
        for scan in self._scans.get_active_scans(self):  # Передаем self
            if not scan.validate():
                logger.error(f"Scan validation failed for start time {scan.get_start()}")
                return False

        # Check temporal consistency of scans
        active_scans = sorted(self._scans.get_active_scans(), key=lambda x: x.get_start())
        telescope_scans = {}  # Словарь для отслеживания занятости телескопов
        for scan in active_scans:
            scan_start = scan.get_start()
            scan_end = scan_start + scan.get_duration()
            
            # Проверка доступности телескопов для скана
            if not scan.check_telescope_availability():
                logger.error(f"Telescope availability check failed for scan starting at {scan_start}")
                return False

            # Проверка пересечений по времени для телескопов
            for telescope in scan.get_telescopes().get_active_telescopes():
                tel_code = telescope.get_telescope_code()
                if tel_code not in telescope_scans:
                    telescope_scans[tel_code] = []
                for prev_start, prev_end in telescope_scans[tel_code]:
                    if not (scan_end <= prev_start or scan_start >= prev_end):
                        logger.error(f"Scan overlap detected for telescope {tel_code}: "
                                    f"[{prev_start}, {prev_end}] vs [{scan_start}, {scan_end}]")
                        return False
                telescope_scans[tel_code].append((scan_start, scan_end))

        logger.info(f"Observation '{self._observation_code}' validated successfully")
        return True

    def activate(self) -> None:
        """Activate observation."""
        super().activate()

    def deactivate(self) -> None:
        """Deactivate observation."""
        super().deactivate()

    def _sync_scans_with_activation(self, entity_type: str, index: int, is_active: bool) -> None:
        """Sync scans when an entity (source, telescope, frequency) is activated/deactivated."""
        entity_map = {"sources": "_source_index", "telescopes": "_telescope_indices", "frequencies": "_frequency_indices"}
        if entity_type not in entity_map:
            raise ValueError(f"Invalid entity type: {entity_type}")
        attr = entity_map[entity_type]
        
        for scan in self._scans.get_all_scans():
            if entity_type == "sources":
                current_idx = getattr(scan, attr)
                if current_idx == index:
                    if not is_active:
                        scan.set_source_index(None)
                        scan.is_off_source = True
                        logger.debug(f"Scan source index reset to None due to deactivation in '{self._observation_code}'")
                    elif is_active and scan.is_off_source and current_idx is not None:
                        # Восстанавливаем источник, если он был изначально привязан
                        scan.set_source_index(index)
                        scan.is_off_source = False
                        logger.debug(f"Scan source index restored to {index} due to activation in '{self._observation_code}'")
            else:  # telescopes or frequencies
                current_indices = getattr(scan, attr)
                if index in current_indices and not is_active:
                    # Деактивация: удаляем индекс
                    updated_indices = [i for i in current_indices if i != index]
                    if entity_type == "telescopes":
                        scan.set_telescope_indices(updated_indices)
                    else:
                        scan.set_frequency_indices(updated_indices)
                    logger.debug(f"Removed {entity_type} index {index} from scan in '{self._observation_code}'")
                elif index not in current_indices and is_active:
                    # Активация: добавляем индекс, только если он изначально мог быть в скане
                    # Предполагаем, что индекс добавляется, если он валиден и не нарушает логику
                    all_entities = (self._telescopes.get_all_telescopes() if entity_type == "telescopes" 
                                    else self._frequencies.get_all_frequencies())
                    if index < len(all_entities) and all_entities[index].isactive:
                        updated_indices = current_indices + [index]
                        if entity_type == "telescopes":
                            scan.set_telescope_indices(updated_indices)
                        else:
                            scan.set_frequency_indices(updated_indices)
                        logger.debug(f"Added {entity_type} index {index} to scan in '{self._observation_code}'")    

    def to_dict(self) -> dict:
        """Convert Observation object to a dictionary for serialization."""
        def convert_quantity(obj):
            """Преобразует Quantity или вложенные структуры в сериализуемые данные."""
            if isinstance(obj, u.Quantity):
                return obj.value.tolist() if obj.isscalar else obj.value.tolist()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, bool):  # Добавляем обработку bool
                return bool(obj)  # Оставляем как есть, json сам разберётся
            elif isinstance(obj, dict):
                return {k: convert_quantity(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_quantity(item) for item in obj]
            return obj

        data = {
            "observation_code": self._observation_code,
            "observation_type": self._observation_type,
            "sources": self._sources.to_dict(),
            "telescopes": self._telescopes.to_dict(),
            "frequencies": self._frequencies.to_dict(),
            "scans": self._scans.to_dict(),
            "isactive": self.isactive,
            "calculated_data": convert_quantity(self._calculated_data) if hasattr(self, '_calculated_data') else {}
        }
        logger.info(f"Converted observation '{self._observation_code}' to dictionary")
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Observation':
        """Create an Observation object from a dictionary."""
        obs = cls(
            observation_code=data["observation_code"],
            observation_type=data["observation_type"],
            sources=Sources.from_dict(data["sources"]),
            telescopes=Telescopes.from_dict(data["telescopes"]),
            frequencies=Frequencies.from_dict(data["frequencies"]),
            scans=Scans.from_dict(data["scans"]),
            isactive=data.get("isactive", True)
        )
        if "calculated_data" in data:
            # При десериализации единицы измерения не восстанавливаем, оставляем как числа
            obs._calculated_data = data["calculated_data"]
        logger.info(f"Created observation '{data['observation_code']}' from dictionary")
        return obs

    def __repr__(self) -> str:
        """Return a string representation of Observation."""
        return (f"Observation(code='{self._observation_code}', sources={self._sources}, "
                f"telescopes={self._telescopes}, frequencies={self._frequencies}, "
                f"scans={self._scans}, isactive={self.isactive}, "
                f"calculated_data={len(self._calculated_data)} items)")

class CatalogManager:
    """Класс для управления каталогами источников и телескопов в текстовом формате."""
    
    def __init__(self, source_file: Optional[str] = None, telescope_file: Optional[str] = None):
        """Инициализация менеджера каталогов.
        
        Args:
            source_file (str, optional): Путь к файлу каталога источников.
            telescope_file (str, optional): Путь к файлу каталога телескопов.
        """
        if source_file is not None and not isinstance(source_file, str):
            logger.error("source_file must be a string or None")
            raise TypeError("source_file must be a string or None!")
        if telescope_file is not None and not isinstance(telescope_file, str):
            logger.error("telescope_file must be a string or None")
            raise TypeError("telescope_file must be a string or None!")
        self.source_catalog = Sources()
        self.telescope_catalog = Telescopes()
        
        if source_file:
            self.load_source_catalog(source_file)
        if telescope_file:
            self.load_telescope_catalog(telescope_file)

    # --- Методы для работы с каталогом источников ---

    def load_source_catalog(self, source_file: str) -> None:
        """Загрузка каталога источников из текстового файла.
        
        Формат: b1950_name j2000_name alt_name ra_hh:mm:ss.ssss dec_dd:mm:ss.ssss
        
        Args:
            source_file (str): Путь к файлу каталога источников.
        
        Raises:
            FileNotFoundError: Если файл не найден.
            ValueError: Если данные в файле некорректны.
        """
        sources = []
        failed_count = 0
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = re.split(r'\s+', line)
                    if len(parts) < 5:
                        logger.warning(f"Skipping invalid source format: {line}")
                        failed_count += 1
                        continue

                    b1950_name = parts[0]
                    j2000_name = parts[1] if parts[1] != "ALT_NAME" else None
                    alt_name = parts[2] if parts[2] != "ALT_NAME" else None
                    ra_str, dec_str = parts[-2], parts[-1]

                    try:
                        ra_match = re.match(r'(\d{2}):(\d{2}):(\d{2}\.\d+)', ra_str)
                        if not ra_match:
                            raise ValueError(f"Invalid RA format: {ra_str}")
                        ra_h, ra_m, ra_s = map(float, ra_match.groups())

                        dec_match = re.match(r'([-+])?(\d{2}):(\d{2}):(\d{2}\.\d+)', dec_str)
                        if not dec_match:
                            raise ValueError(f"Invalid DEC format: {dec_str}")
                        sign, de_d, de_m, de_s = dec_match.groups()
                        de_d = float(de_d) if sign != '-' else -float(de_d)
                        de_m, de_s = float(de_m), float(de_s)

                        source = Source(
                            name=b1950_name,
                            ra_h=ra_h, ra_m=ra_m, ra_s=ra_s,
                            de_d=de_d, de_m=de_m, de_s=de_s,
                            name_J2000=j2000_name,
                            alt_name=alt_name
                        )
                        sources.append(source)
                    except ValueError as e:
                        logger.warning(f"Failed to parse source '{line}': {e}")
                        failed_count += 1
                        continue
            self.source_catalog = Sources(sources)
            if failed_count > 0:
                logger.warning(f"Loaded {len(sources)} sources from '{source_file}', {failed_count} failed")
            else:
                logger.info(f"Successfully loaded {len(sources)} sources from '{source_file}'")
        except FileNotFoundError:
            raise FileNotFoundError(f"Source catalog file '{source_file}' not found!")
        except ValueError as e:
            raise ValueError(f"Error parsing source catalog: {e}")

    def get_source(self, name: str) -> Optional[Source]:
        """Получить источник по имени (B1950 или J2000)."""
        return next((s for s in self.source_catalog.get_all_sources() 
                     if s.name == name or (s.name_J2000 and s.name_J2000 == name)), None)

    def get_sources_by_ra_range(self, ra_min: float, ra_max: float) -> List[Source]:
        """Получить список источников в заданном диапазоне прямого восхождения (RA) в градусах."""
        return [s for s in self.source_catalog.get_all_sources() 
                if ra_min <= s.get_ra_degrees() <= ra_max]

    def get_sources_by_dec_range(self, dec_min: float, dec_max: float) -> List[Source]:
        """Получить список источников в заданном диапазоне склонения (DEC) в градусах."""
        return [s for s in self.source_catalog.get_all_sources() 
                if dec_min <= s.get_dec_degrees() <= dec_max]

    # --- Методы для работы с каталогом телескопов ---

    def load_telescope_catalog(self, telescope_file: str) -> None:
        """Загрузка каталога телескопов из текстового файла.
        
        Формат: number short_name full_name x y z
        
        Args:
            telescope_file (str): Путь к файлу каталога телескопов.
        
        Raises:
            FileNotFoundError: Если файл не найден.
            ValueError: Если данные в файле некорректны.
        """
        telescopes = []
        failed_count = 0
        try:
            with open(telescope_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = re.split(r'\s+', line)
                    if len(parts) < 6:
                        logger.warning(f"Skipping invalid telescope format: {line}")
                        failed_count += 1
                        continue

                    try:
                        number, short_name, full_name = parts[0], parts[1], parts[2]
                        x, y, z = map(float, parts[3:6])
                        diameter = float(parts[6])
                        vx, vy, vz = 0.0, 0.0, 0.0  # Скорости не указаны в каталоге

                        telescope = Telescope(
                            code=short_name,
                            name=full_name,
                            x=x, y=y, z=z,
                            vx=vx, vy=vy, vz=vz,
                            diameter=diameter,
                            isactive=True
                        )
                        telescopes.append(telescope)
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse telescope '{line}': {e}")
                        failed_count += 1
                        continue
            self.telescope_catalog = Telescopes(telescopes)
            if failed_count > 0:
                logger.warning(f"Loaded {len(telescopes)} telescopes from '{telescope_file}', {failed_count} failed")
            else:
                logger.info(f"Successfully loaded {len(telescopes)} telescopes from '{telescope_file}'")
        except FileNotFoundError:
            raise FileNotFoundError(f"Telescope catalog file '{telescope_file}' not found!")
        except ValueError as e:
            raise ValueError(f"Error parsing telescope catalog: {e}")

    def get_telescope(self, code: str) -> Optional[Telescope]:
        """Получить телескоп по коду."""
        return next((t for t in self.telescope_catalog.get_all_telescopes() if t.code == code), None)

    def get_telescopes_by_type(self, telescope_type: str = "Telescope") -> List[Telescope]:
        """Получить список телескопов заданного типа."""
        return [t for t in self.telescope_catalog.get_all_telescopes() 
                if (telescope_type == "Telescope" and isinstance(t, Telescope))]

    # --- Общие методы ---

    def clear_catalogs(self) -> None:
        """Очистить оба каталога."""
        self.source_catalog.clear()
        self.telescope_catalog.clear()

    def __repr__(self) -> str:
        """Строковое представление CatalogManager."""
        return (f"CatalogManager(sources={len(self.source_catalog)}, "
                f"telescopes={len(self.telescope_catalog)})")