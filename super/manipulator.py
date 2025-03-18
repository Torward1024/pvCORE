# super/manipulator.py
from abc import ABC
from typing import List, Optional
from base.observation import Observation, Project
from super.configurator import Configurator
from super.calculator import Calculator
from super.visualizator import Visualizator
from super.optimizator import Optimizator
import json
from utils.logging_setup import logger

class Manipulator(ABC):
    def __init__(self, project: Optional[Project] = None):
        self.project = project if project else Project(project_name="Default Project")
        self._cache = {}
        logger.info(f"Initialized Manipulator with project '{self.project.project_name}'")

    def add_observation(self, observation: Observation) -> None:
        if not isinstance(observation, Observation):
            logger.error("Attempted to add invalid observation type")
            raise TypeError("Observation must be an Observation instance!")
        self.project.observations.append(observation)
        self._invalidate_cache()
        logger.info(f"Added observation '{observation.observation_code}' to project '{self.project.project_name}'")

    def remove_observation(self, index: int) -> None:
        try:
            obs = self.project.observations.pop(index)
            self._invalidate_cache()
            logger.info(f"Removed observation at index {index} from project '{self.project.project_name}'")
        except IndexError:
            logger.error(f"Invalid observation index: {index}")
            raise IndexError("Invalid observation index!")

    def get_observation(self, index: int) -> Observation:
        try:
            obs = self.project.observations[index]
            logger.info(f"Retrieved observation at index {index} from project '{self.project.project_name}'")
            return obs
        except IndexError:
            logger.error(f"Invalid observation index: {index}")
            raise IndexError("Invalid observation index!")

    def get_all_observations(self) -> List[Observation]:
        logger.info(f"Retrieved all observations from project '{self.project.project_name}'")
        return self.project.get_observations()

    def configure(self, configurator: Configurator, obs_code: Optional[str] = None) -> None:
        if not isinstance(configurator, Configurator):
            logger.error("Invalid configurator type provided")
            raise TypeError("Configurator must be a Configurator instance!")
        if obs_code:
            obs = self.project.get_observation(obs_code=obs_code)
            configurator.configure_observation(obs)
            logger.info(f"Configured observation '{obs_code}' in project '{self.project.project_name}'")
        else:
            for obs in self.project.get_observations():
                configurator.configure_observation(obs)
            logger.info(f"Configured all observations in project '{self.project.project_name}'")
        self._invalidate_cache()

    def calculate(self, calculator: Calculator, obs_code: Optional[str] = None) -> dict:
        if not isinstance(calculator, Calculator):
            logger.error("Invalid calculator type provided")
            raise TypeError("Calculator must be a Calculator instance!")
        cache_key = f"calc_{obs_code if obs_code else 'all'}"
        if cache_key in self._cache:
            logger.info(f"Retrieved cached calculation for '{cache_key}'")
            return self._cache[cache_key]
        
        result = {}
        if obs_code:
            obs = self.project.get_observation(obs_code=obs_code)
            result = calculator.calculate(obs)
            logger.info(f"Calculated parameters for observation '{obs_code}'")
        else:
            result = {obs.get_observation_code(): calculator.calculate(obs) 
                      for obs in self.project.get_observations()}
            logger.info(f"Calculated parameters for all observations in project '{self.project.project_name}'")
        self._cache[cache_key] = result
        return result

    def visualize(self, visualizator: Visualizator, obs_code: Optional[str] = None) -> None:
        if not isinstance(visualizator, Visualizator):
            logger.error("Invalid visualizator type provided")
            raise TypeError("Visualizator must be a Visualizator instance!")
        if obs_code:
            obs = self.project.get_observation(obs_code=obs_code)
            visualizator.visualize(obs)
            logger.info(f"Visualized observation '{obs_code}'")
        else:
            for obs in self.project.get_observations():
                visualizator.visualize(obs)
            logger.info(f"Visualized all observations in project '{self.project.project_name}'")

    def optimize(self, optimizator: Optimizator, obs_code: Optional[str] = None) -> None:
        if not isinstance(optimizator, Optimizator):
            logger.error("Invalid optimizator type provided")
            raise TypeError("Optimizator must be an Optimizator instance!")
        if obs_code:
            obs = self.project.get_observation(obs_code=obs_code)
            optimizator.optimize(obs)
            logger.info(f"Optimized observation '{obs_code}'")
        else:
            for obs in self.project.get_observations():
                optimizator.optimize(obs)
            logger.info(f"Optimized all observations in project '{self.project.project_name}'")
        self._invalidate_cache()

    def save_project(self, filename: str) -> None:
        try:
            data = self.project.to_dict()
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            logger.info(f"Saved project '{self.project.project_name}' to '{filename}'")
        except Exception as e:
            logger.error(f"Failed to save project to '{filename}': {str(e)}")
            raise

    def load_project(self, filename: str) -> None:
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.project = Project.from_dict(data)
            self._invalidate_cache()
            logger.info(f"Loaded project '{self.project.project_name}' from '{filename}'")
        except Exception as e:
            logger.error(f"Failed to load project from '{filename}': {str(e)}")
            raise

    def _invalidate_cache(self) -> None:
        self._cache.clear()
        logger.info(f"Cleared cache for project '{self.project.project_name}'")

    def __repr__(self) -> str:
        return f"Manipulator(project='{self.project.project_name}', observations={len(self.project)})"