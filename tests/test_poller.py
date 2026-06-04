"""
Unit tests for the poller components (adapter detection, speed tester)
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from poller.adapter_detector import AdapterDetector
from poller.speed_tester import SpeedTester, MockSpeedTester

# ------------------- Adapter Detection Tests -------------------

def test_adapter_detector_vpn_keywords():
    detector = AdapterDetector()
    assert detector._is_vpn_adapter("TAP-Windows Adapter") is True
    assert detector._is_vpn_adapter("Cisco AnyConnect Secure") is True
    assert detector._is_vpn_adapter("Realtek PCIe GbE") is False
    assert detector._is_vpn_adapter("Intel Wi-Fi 6 AX200") is False

def test_adapter_detector_mac_filter():
    detector = AdapterDetector()
    assert detector._has_physical_mac("00:05:69:12:34:56") is False  # VMware
    assert detector._has_physical_mac("00:0C:29:AB:CD:EF") is False  # VMware
    assert detector._has_physical_mac("08:00:27:AA:BB:CC") is False   # VirtualBox
    assert detector._has_physical_mac("00:1A:2B:3C:4D:5E") is True    # Real

@patch("poller.adapter_detector.wmi.WMI")
def test_wmi_query(mock_wmi):
    # Mock a WMI adapter
    mock_nic = Mock()
    mock_nic.Name = "Intel Ethernet"
    mock_nic.Description = "Intel(R) Ethernet Connection"
    mock_nic.PhysicalAdapter = True
    mock_nic.NetEnabled = True
    mock_nic.MACAddress = "00:1A:2B:3C:4D:5E"
    mock_nic.Index = 1
    mock_nic.Speed = 1000000000
    mock_nic.Manufacturer = "Intel"
    mock_nic.InterfaceIndex = 5
    
    mock_wmi.return_value.Win32_NetworkAdapter.return_value = [mock_nic]
    
    detector = AdapterDetector()
    adapters = detector.get_physical_adapters_wmi()
    assert len(adapters) == 1
    assert adapters[0]["name"] == "Intel Ethernet"

# ------------------- Speed Tester Tests -------------------

def test_speed_tester_structure():
    adapter_info = {"id": 1, "name": "Test Adapter"}
    tester = SpeedTester(adapter_info)
    # Just test that the object exists
    assert tester.adapter_name == "Test Adapter"

def test_mock_speed_tester():
    adapter = {"id": 1, "name": "Mock"}
    tester = MockSpeedTester(adapter)
    result = tester.run_test()
    assert "timestamp" in result
    assert "download_mbps" in result
    assert "upload_mbps" in result
    assert "latency_ms" in result
    assert "packet_loss" in result
    assert result["download_mbps"] > 0

@patch("poller.speed_tester.subprocess.run")
def test_ping_analysis_fallback(mock_run):
    # Simulate ping output
    mock_run.return_value.stdout = """
    Pinging 8.8.8.8 with 32 bytes of data:
    Reply from 8.8.8.8: bytes=32 time=12ms TTL=117
    Reply from 8.8.8.8: bytes=32 time=11ms TTL=117
    Reply from 8.8.8.8: bytes=32 time=13ms TTL=117
    Reply from 8.8.8.8: bytes=32 time=12ms TTL=117
    
    Ping statistics for 8.8.8.8:
        Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),
    """
    adapter = {"id": 1}
    tester = SpeedTester(adapter)
    # We only test the ping method directly
    result = tester.run_test_ping_analysis()
    assert 10 <= result["latency_ms"] <= 20
    assert result["packet_loss"] == 0.0

# ------------------- Integration with DB (mock) -------------------

def test_poller_cycle_integration():
    """Test that a poller cycle can run without crashing (using mock tester)"""
    from db.db_manager import DatabaseManager
    from poller.main import NetworkSpeedPoller
    from poller.adapter_detector import AdapterDetector
    
    # Use in-memory DB
    db = DatabaseManager(":memory:")
    
    # Patch the poller to use mock tester and our DB
    with patch("poller.main.DatabaseManager", return_value=db), \
         patch("poller.main.SpeedTester", MockSpeedTester), \
         patch.object(AdapterDetector, "get_active_physical_adapter") as mock_adapter:
        
        mock_adapter.return_value = {"id": 1, "name": "Mock Adapter"}
        poller = NetworkSpeedPoller()
        poller.db = db
        poller.current_adapter = mock_adapter.return_value
        
        # Run a single poll
        poller.poll_once()
        
        # Verify data was inserted
        stats = db.get_stats()
        assert stats["total_samples"] == 1