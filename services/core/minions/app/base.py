    def create_agent(self, result_type=None, model_key=DEFAULT_MODEL_KEY):
        """Create a new agent with the specified result type and model configuration"""
        logger.info(f"[{self.__class__.__name__}] Creating agent with model_key: {model_key}")
        
        model_config = LLM_CONFIG[model_key]
        provider = model_config["provider"]
        model = model_config["model"]
        
        logger.info(f"[{self.__class__.__name__}] Using provider: {provider}, model: {model}")
        
        # Set up the custom result type based on the provided type or the default
        real_result_type = result_type if result_type else self.result_type
        
        # Log the abilities we're registering
        abilities_to_register = self.fetch_available_abilities()
        logger.info(f"[{self.__class__.__name__}] Registering abilities: {', '.join([a.__name__ for a in abilities_to_register])}")
        
        # Create the agent with the configured model
        agent = agent_utils.create_agent(
            model_key=model_key,
            system_prompt=self.system_prompt,
            result_type=real_result_type,
            abilities=abilities_to_register
        )
        
        logger.info(f"[{self.__class__.__name__}] Successfully created agent with model_key: {model_key}")
        return agent 