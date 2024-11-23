from aws_cdk import App
from aws_ddk_core import Configurator

class Configs:
    def __init__(self, app: App):
        self.branch_to_env_mappings = {
            "cicd": "cicd",
            "develop": "dev",
            "test": "test",
            "main": "prod",
        }
        
        # format: {env_name: Configurator()}
        self.configs = dict()
        
        for branch in self.branch_to_env_mappings.keys():
            config = Configurator(app, "./ddk.json", branch)
            env_name = config.get_config_attribute("name")
            if env_name:
                self.configs[env_name] = config

    def get_env_by_branch(self, branch: str) -> str:
        return self.branch_to_env_mappings[branch]
    
    def get_branch_by_env(self, env: str) -> str:
        for branch in self.branch_to_env_mappings.keys():
            if self.branch_to_env_mappings[branch] == env:
                return branch
        return None

    def get_config_by_branch(self, branch: str) -> Configurator:
        return self.configs[self.branch_to_env_mappings[branch]]
    
    def get_config_by_env(self, env: str) -> Configurator:
        return self.configs[env]
    
    def get_tags(self) -> dict:
        return self.get_config_by_env('cicd').get_config_attribute('tags')