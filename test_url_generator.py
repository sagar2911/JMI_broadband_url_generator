"""
Tests for URL Generator Tool
"""

import pytest
from url_generator import (
    BroadbandParams,
    generate_broadband_url,
    VALID_SPEEDS,
    VALID_CONTRACT_LENGTHS,
    VALID_PHONE_CALLS,
)


class TestBroadbandParams:
    """Test BroadbandParams class."""
    
    def test_valid_postcode(self):
        """Test valid UK postcode formats."""
        params = BroadbandParams(postcode="E14 9WB")
        assert params.validate()
        assert params.normalize_postcode() == "E14+9WB"
        
        params = BroadbandParams(postcode="SW10 9PA")
        assert params.validate()
        assert params.normalize_postcode() == "SW10+9PA"
        
        params = BroadbandParams(postcode="M1 1AA")
        assert params.validate()
    
    def test_invalid_postcode(self):
        """Test invalid postcode formats."""
        params = BroadbandParams(postcode="")
        assert not params.validate()
        assert "Postcode is required" in params.errors
        
        params = BroadbandParams(postcode="INVALID")
        assert not params.validate()
        assert "Invalid UK postcode format" in params.errors[0]
    
    def test_valid_speed(self):
        """Test valid speed values."""
        for speed in VALID_SPEEDS:
            params = BroadbandParams(postcode="E14 9WB", speedInMb=speed)
            assert params.validate()
    
    def test_invalid_speed(self):
        """Test invalid speed values."""
        params = BroadbandParams(postcode="E14 9WB", speedInMb="200Mb")
        assert not params.validate()
        assert "Invalid speed" in params.errors[0]
    
    def test_valid_contract_length(self):
        """Test valid contract length values."""
        for contract in VALID_CONTRACT_LENGTHS:
            if contract:  # Skip empty string
                params = BroadbandParams(postcode="E14 9WB", contractLength=contract)
                assert params.validate()
    
    def test_valid_phone_calls(self):
        """Test valid phone calls options."""
        for phone_call in VALID_PHONE_CALLS:
            params = BroadbandParams(postcode="E14 9WB", phoneCalls=phone_call)
            assert params.validate()
    
    def test_multiple_providers(self):
        """Test multiple providers."""
        params = BroadbandParams(
            postcode="E14 9WB",
            providers="Hyperoptic,BT,Sky"
        )
        assert params.validate()


class TestGenerateURL:
    """Test URL generation function."""
    
    def test_basic_url(self):
        """Test basic URL generation with just postcode."""
        params = BroadbandParams(postcode="E14 9WB")
        url, error = generate_broadband_url(params)
        
        assert error is None
        assert "broadband.justmovein.co" in url
        assert "E14%2B9WB" in url or "E14+9WB" in url
        assert "location=" in url
    
    def test_full_url(self):
        """Test URL generation with all parameters."""
        params = BroadbandParams(
            postcode="E14 9WB",
            speedInMb="100Mb",
            contractLength="12 months",
            phoneCalls="Evening and Weekend",
            productType="broadband,phone",
            providers="Hyperoptic",
            sortBy="Avg. Monthly Cost"
        )
        url, error = generate_broadband_url(params)
        
        assert error is None
        assert "speedInMb=100Mb" in url or "100Mb" in url
        assert "12%20months" in url or "12 months" in url
        assert "Hyperoptic" in url
    
    def test_invalid_params(self):
        """Test URL generation with invalid parameters."""
        params = BroadbandParams(postcode="", speedInMb="200Mb")
        url, error = generate_broadband_url(params)
        
        assert url == ""
        assert error is not None
        assert "Validation errors" in error
    
    def test_provider_filtering(self):
        """Test URL with provider filtering."""
        params = BroadbandParams(
            postcode="SW10 9PA",
            providers="BT,Sky,Vodafone"
        )
        url, error = generate_broadband_url(params)
        
        assert error is None
        assert "providers=" in url
        assert "BT" in url or "Sky" in url or "Vodafone" in url
    
    def test_current_provider(self):
        """Test URL with current provider."""
        params = BroadbandParams(
            postcode="E14 9WB",
            currentProvider="Virgin Media"
        )
        url, error = generate_broadband_url(params)
        
        assert error is None
        assert "Virgin%20Media" in url or "Virgin+Media" in url or "Virgin Media" in url


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

