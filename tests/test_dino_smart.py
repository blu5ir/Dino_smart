import os
import sys
import json
import pytest

# Add Dino_smart to sys.path to allow imports of local packages
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Dino_smart"))

def test_version_json_exists_and_valid():
    """Verify that version.json exists, is valid JSON, and has the correct keys."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    version_path = os.path.join(root_dir, "Dino_smart", "version.json")
    
    assert os.path.exists(version_path), "version.json does not exist in Dino_smart folder"
    
    with open(version_path, "r") as f:
        data = json.load(f)
        
    assert "version" in data, "version key missing"
    assert "build" in data, "build key missing"
    assert "timestamp" in data, "timestamp key missing"
    assert isinstance(data["version"], str), "version should be a string"
    assert isinstance(data["build"], str), "build should be a string"

def test_llm_factory_import_and_basic():
    """Test that LLMFactory can be imported and resolves get_provider correctly."""
    from providers.llm_factory import LLMFactory
    
    # Should return None if provider_name is not specified or None
    assert LLMFactory.get_provider() is None
    assert LLMFactory.get_provider(None) is None

def test_base_provider_abstract():
    """Test that BaseLLMProvider cannot be instantiated directly."""
    from providers.base_provider import BaseLLMProvider
    
    with pytest.raises(TypeError):
        BaseLLMProvider()
