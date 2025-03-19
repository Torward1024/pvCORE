# super/manipulator.py
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from base.observation import Observation
from super.configurator import Configurator
from super.calculator import Calculator
from super.vizualizator import Vizualizator
from super.optimizator import Optimizator
from utils.validation import check_type, check_non_empty_string
from utils.logging_setup import logger


class Project:
    """Container for managing multiple observations."""
    def __init__(self, name: str, observations: List[Observation] = None):
        self._name = name
        self._observations = observations if observations else []
        logger.info(f"Initialized Project '{name}' with {len(self._observations)} observations")

    def add_observation(self, observation: Observation) -> None:
        self._observations.append(observation)
        logger.info(f"Added observation '{observation.get_observation_code()}' to Project '{self._name}'")
    
    def insert_observation(self, observation: Observation, index: int) -> None:
        """Insert an observation at the specified index."""
        check_type(observation, Observation, "Observation")
        if not (0 <= index <= len(self._observations)):
            logger.error(f"Invalid index {index} for insertion in Project '{self._name}'")
            raise IndexError(f"Index {index} out of range for Project with {len(self._observations)} observations")
        self._observations.insert(index, observation)
        logger.info(f"Inserted observation '{observation.get_observation_code()}' at index {index} in Project '{self._name}'")

    def remove_observation(self, index: int) -> None:
        try:
            obs = self._observations.pop(index)
            logger.info(f"Removed observation '{obs.get_observation_code()}' from Project '{self._name}'")
        except IndexError:
            logger.error(f"Invalid observation index: {index}")
            raise IndexError("Invalid observation index!")

    def get_observations(self) -> List[Observation]:
        return self._observations

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self._name, "observations": [obs.to_dict() for obs in self._observations]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        return cls(name=data["name"], observations=[Observation.from_dict(obs) for obs in data["observations"]])

    def get_name(self) -> str:
        return self._name

    def set_name(self, name: str) -> None:
        check_non_empty_string(name, "Project name")
        self._name = name
        logger.info(f"Set project name to '{name}'")


class Manipulator(ABC):
    """Abstract base class for managing projects and coordinating super-classes."""
    def __init__(self, project: Optional[Project] = None):
        self._project = project if project else Project(name="DefaultProject")
        self._configurator = None
        self._calculator = None
        self._vizualizator = None
        self._optimizator = None
        logger.info(f"Initialized Manipulator with project '{self._project.get_name()}'")

    def set_project(self, project: Project) -> None:
        check_type(project, Project, "Project")
        self._project = project
        logger.info(f"Set project '{project.get_name()}' for Manipulator")

    def add_observation(self, observation: Observation) -> None:
        check_type(observation, Observation, "Observation")
        self._project.add_observation(observation)
    
    def insert_observation(self, observation: Observation, index: int) -> None:
        """Insert an observation at the specified index in the project."""
        check_type(observation, Observation, "Observation")
        self._project.insert_observation(observation, index)

    def remove_observation(self, index: int) -> None:
        self._project.remove_observation(index)

    def set_configurator(self, configurator: 'Configurator') -> None:
        check_type(configurator, Configurator, "Configurator")
        self._configurator = configurator
        logger.info("Configurator set in Manipulator")

    def set_calculator(self, calculator: 'Calculator') -> None:
        check_type(calculator, Calculator, "Calculator")
        self._calculator = calculator
        logger.info("Calculator set in Manipulator")

    def set_vizualizator(self, vizualizator: 'Vizualizator') -> None:
        check_type(vizualizator, Vizualizator, "Vizualizator")
        self._vizualizator = vizualizator
        logger.info("Vizualizator set in Manipulator")

    def set_optimizator(self, optimizator: 'Optimizator') -> None:
        check_type(optimizator, Optimizator, "Optimizator")
        self._optimizator = optimizator
        logger.info("Optimizator set in Manipulator")

    @abstractmethod
    def execute(self) -> None:
        """Execute the task."""
        pass

    def save_project(self, filepath: str) -> None:
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self._project.to_dict(), f, indent=4)
        logger.info(f"Project saved to '{filepath}'")

    def load_project(self, filepath: str) -> None:
        import json
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._project = Project.from_dict(data)
            logger.info(f"Project loaded from '{filepath}'")
        except FileNotFoundError:
            logger.error(f"Project file '{filepath}' not found")
            raise FileNotFoundError(f"Project file '{filepath}' not found!")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from '{filepath}': {e}")
            raise ValueError(f"Invalid JSON in '{filepath}': {e}")

    def get_project_name(self) -> str:
        """Get the project name."""
        return self._project.get_name()
    
    def get_observations(self) -> List[Observation]:
        """Get the list of observations in the project."""
        return self._project.get_observations()


class DefaultManipulator(Manipulator):
    """Default implementation of Manipulator."""
    def execute(self) -> None:
        """Execute the default task: configure, calculate, and visualize all observations."""
        if not self._project.get_observations():
            logger.warning("No observations to execute")
            return
        for obs in self._project.get_observations():
            if self._configurator:
                self._configurator.configure_observation(obs)
            if self._calculator:
                self._calculator.calculate_all(obs)
            if self._vizualizator:
                self._vizualizator.visualize_observation(obs)
        logger.info(f"Executed all tasks for project '{self._project.get_name()}'")