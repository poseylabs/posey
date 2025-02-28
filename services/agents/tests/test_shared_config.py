import unittest
import json
import os
from app.config.prompts import PromptLoader

class TestSharedConfigurations(unittest.TestCase):
    def setUp(self):
        # Ensure we're starting with a clean cache
        PromptLoader._prompts = {}
    
    def test_shared_config_loading(self):
        """Test that shared configurations are loaded and merged correctly"""
        # Get the posey prompt with shared configuration
        posey_config = PromptLoader.get_prompt_with_shared_config("posey")
        
        # Verify that the posey configuration has the shared_config reference
        self.assertIn("shared_config", posey_config)
        self.assertEqual(posey_config["shared_config"]["response_principles"], "response_styles")
        self.assertEqual(posey_config["shared_config"]["response_examples"], "response_styles")
        
        # Get the response styles directly to check common_examples
        response_styles = PromptLoader.get_shared_prompt("response_styles")
        self.assertIn("common_examples", response_styles)
        
        # Verify that specific examples exist in common_examples
        self.assertIn("time_query", response_styles["common_examples"])
        self.assertIn("joke_request", response_styles["common_examples"])
        self.assertIn("successful_image", response_styles["common_examples"])
        self.assertIn("failed_image", response_styles["common_examples"])
        
        # Verify that response_examples are mapped correctly from common_examples
        self.assertIn("response_examples", posey_config)
        self.assertEqual(
            posey_config["response_examples"]["successful_image"]["answer"],
            response_styles["common_examples"]["successful_image"]["answer"]
        )
        self.assertEqual(
            posey_config["response_examples"]["joke_request"]["answer"],
            response_styles["common_examples"]["joke_request"]["answer"]
        )
        
        # Check other merged sections from shared config
        self.assertIn("response_principles", posey_config)
        self.assertEqual(
            posey_config["response_principles"],
            response_styles["response_principles"]
        )
        
        # Check synthesis prompt similarly
        synthesis_config = PromptLoader.get_prompt_with_shared_config("synthesis")
        self.assertIn("shared_config", synthesis_config)
        self.assertEqual(synthesis_config["shared_config"]["response_examples"], "response_styles")
        
        # Verify response_examples are mapped from common_examples in synthesis
        self.assertIn("response_examples", synthesis_config)
        self.assertEqual(
            synthesis_config["response_examples"]["successful_image"]["answer"],
            response_styles["common_examples"]["successful_image"]["answer"]
        )
        
        # Print a confirmation message if all tests pass
        print("All shared configuration tests passed!")

if __name__ == "__main__":
    unittest.main() 
