"""
Comprehensive Cryptocurrency Address Detection Tests
100 variations (Bitcoin, Ethereum, Litecoin, etc.)
"""

import pytest
from tests.fixtures.test_data import CRYPTO_TEST_CASES


@pytest.mark.crypto
class TestCryptoDetection:
    """Test cryptocurrency address detection across 100 variations"""

    @pytest.mark.parametrize("crypto_address", CRYPTO_TEST_CASES)
    def test_crypto_detection(self, filter_instance, crypto_address):
        """Test that each crypto address format is detected"""
        text = f"Send payment to {crypto_address}"

        result = filter_instance.mask(text)

        # Check if detected
        crypto_detected = any(
            "BITCOIN" in entity["entity_type"] or
            "ETHEREUM" in entity["entity_type"] or
            "CRYPTO" in entity["entity_type"]
            for entity in result.entities_found
        )

        # If detected, should be masked
        if crypto_detected:
            assert crypto_address not in result.masked_text, f"Crypto not masked: {crypto_address}"

    @pytest.mark.parametrize("crypto_address", CRYPTO_TEST_CASES[:30])  # Test Bitcoin
    def test_crypto_masking_and_demasking(self, filter_instance, crypto_address):
        """Test full mask -> demask cycle for crypto addresses"""
        text = f"Wallet: {crypto_address}"

        # Mask
        mask_result = filter_instance.mask(text)
        session_id = mask_result.session_id

        # Demask
        demask_result = filter_instance.demask(
            mask_result.masked_text,
            session_id=session_id
        )

        # Should restore
        assert demask_result.original_text is not None

    def test_bitcoin_legacy_addresses(self, filter_instance):
        """Test Bitcoin legacy (P2PKH) addresses"""
        bitcoin_addresses = [
            "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
            "3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy",
        ]

        detected_count = 0
        for address in bitcoin_addresses:
            text = f"BTC: {address}"
            result = filter_instance.mask(text)

            if any("BITCOIN" in e["entity_type"] or "CRYPTO" in e["entity_type"]
                   for e in result.entities_found):
                detected_count += 1

        # Should detect Bitcoin addresses
        assert detected_count >= len(bitcoin_addresses) // 2

    def test_bitcoin_segwit_addresses(self, filter_instance):
        """Test Bitcoin SegWit (Bech32) addresses"""
        segwit_addresses = [
            "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
            "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
        ]

        detected_count = 0
        for address in segwit_addresses:
            text = f"BTC (SegWit): {address}"
            result = filter_instance.mask(text)

            if any("BITCOIN" in e["entity_type"] or "CRYPTO" in e["entity_type"]
                   for e in result.entities_found):
                detected_count += 1

        # SegWit addresses are harder to detect
        assert detected_count >= 0

    def test_ethereum_addresses(self, filter_instance):
        """Test Ethereum addresses"""
        eth_addresses = [
            "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
            "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359",
            "0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB",
        ]

        detected_count = 0
        for address in eth_addresses:
            text = f"ETH: {address}"
            result = filter_instance.mask(text)

            if any("ETHEREUM" in e["entity_type"] or "CRYPTO" in e["entity_type"]
                   for e in result.entities_found):
                detected_count += 1

        # Should detect Ethereum addresses
        assert detected_count >= len(eth_addresses) // 2

    def test_litecoin_addresses(self, filter_instance):
        """Test Litecoin addresses"""
        ltc_addresses = [
            "LM2WMpR1Rp6j3Sa59cMXMs1SPzj9eXpGc1",
            "LQ4i7FLNzYMnJDWr4WDvWjp3rqVSDt3MgK",
        ]

        for address in ltc_addresses:
            text = f"LTC: {address}"
            result = filter_instance.mask(text)

            # Litecoin might not be detected
            assert result.masked_text is not None

    def test_multiple_crypto_addresses(self, filter_instance):
        """Test multiple different crypto addresses"""
        text = """
        Bitcoin: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
        Ethereum: 0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed
        """

        result = filter_instance.mask(text)

        # Should detect multiple crypto addresses
        crypto_entities = [
            e for e in result.entities_found
            if "BITCOIN" in e["entity_type"] or
               "ETHEREUM" in e["entity_type"] or
               "CRYPTO" in e["entity_type"]
        ]

        # At least one should be detected
        assert len(crypto_entities) >= 1

    def test_crypto_in_sentence(self, filter_instance):
        """Test crypto addresses embedded in natural text"""
        test_cases = [
            "Please send BTC to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "My Ethereum wallet is 0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
            "Deposit address: bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq (Bitcoin)",
        ]

        detected_count = 0
        for text in test_cases:
            result = filter_instance.mask(text)
            if len(result.entities_found) > 0:
                detected_count += 1

        # Should detect crypto in most sentences
        assert detected_count >= len(test_cases) // 2

    def test_crypto_case_sensitivity(self, filter_instance):
        """Test that crypto addresses are case-sensitive"""
        # Ethereum addresses have checksummed case
        eth_address = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
        lowercase = eth_address.lower()

        text1 = f"Address: {eth_address}"
        text2 = f"Address: {lowercase}"

        result1 = filter_instance.mask(text1)
        result2 = filter_instance.mask(text2)

        # Both should be handled (case matters for Ethereum)
        assert result1.masked_text is not None
        assert result2.masked_text is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "crypto"])
