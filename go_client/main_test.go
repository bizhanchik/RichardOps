package main

import (
	"math"
	"testing"
	"time"
)

// TestCPUBaselineCalculation tests the CPU baseline and z-score calculation
func TestCPUBaselineCalculation(t *testing.T) {
	config := Config{
		BaselineSamples: 5,
		CPUSpikePct:     85.0,
	}
	
	agent, err := NewAgent(config)
	if err != nil {
		t.Fatalf("Failed to create agent: %v", err)
	}
	
	// Add baseline samples with low variance
	baselineSamples := []float64{20.0, 22.0, 21.0, 23.0, 19.0}
	for _, sample := range baselineSamples {
		agent.cpuSamples = append(agent.cpuSamples, CPUSample{
			Value:     sample,
			Timestamp: time.Now(),
		})
	}
	
	// Calculate expected mean and standard deviation
	var sum, sumSquares float64
	for _, sample := range baselineSamples {
		sum += sample
		sumSquares += sample * sample
	}
	
	n := float64(len(baselineSamples))
	expectedMean := sum / n
	expectedVariance := (sumSquares / n) - (expectedMean * expectedMean)
	expectedStdDev := math.Sqrt(expectedVariance)
	
	// Test with a high CPU value that should trigger an alert
	highCPU := 90.0
	expectedZScore := (highCPU - expectedMean) / expectedStdDev
	
	// Clear any existing alerts
	agent.localAlerts = agent.localAlerts[:0]
	
	// Update baseline with high CPU value
	agent.updateCPUBaseline(highCPU)
	
	// Check if CPU spike alert was generated
	found := false
	for _, alert := range agent.localAlerts {
		if alert == "CPU_SPIKE" {
			found = true
			break
		}
	}
	
	if !found {
		t.Errorf("Expected CPU_SPIKE alert to be generated for CPU %.2f%% (z-score: %.2f)", highCPU, expectedZScore)
	}
	
	t.Logf("CPU baseline test passed: mean=%.2f, stddev=%.2f, z-score=%.2f", expectedMean, expectedStdDev, expectedZScore)
}

// TestSimulateAttackBehavior tests the simulate attack functionality
func TestSimulateAttackBehavior(t *testing.T) {
	config := Config{
		SimulateAttack:       true,
		FailedAuthThreshold:  20,
		CPUSpikePct:         85.0,
		BaselineSamples:     5,
	}
	
	agent, err := NewAgent(config)
	if err != nil {
		t.Fatalf("Failed to create agent: %v", err)
	}
	
	// Clear any existing data
	agent.authFailures = agent.authFailures[:0]
	agent.localAlerts = agent.localAlerts[:0]
	agent.cpuSamples = agent.cpuSamples[:0]
	agent.eventBuffer = agent.eventBuffer[:0]
	
	// Run simulate attack
	agent.simulateAttack()
	
	// Check that brute force failures were added
	if len(agent.authFailures) < config.FailedAuthThreshold {
		t.Errorf("Expected at least %d auth failures, got %d", config.FailedAuthThreshold, len(agent.authFailures))
	}
	
	// Check that CPU spike samples were added
	if len(agent.cpuSamples) == 0 {
		t.Error("Expected CPU spike samples to be added")
	}
	
	// Check that Docker event was added
	if len(agent.eventBuffer) == 0 {
		t.Error("Expected Docker event to be added")
	}
	
	// Check that shell in container alert was added
	foundShellAlert := false
	for _, alert := range agent.localAlerts {
		if alert == "SHELL_IN_CONTAINER" {
			foundShellAlert = true
			break
		}
	}
	
	if !foundShellAlert {
		t.Error("Expected SHELL_IN_CONTAINER alert to be generated")
	}
	
	// Verify the simulated IP address
	foundSimulatedIP := false
	for _, failure := range agent.authFailures {
		if failure.IP == "192.0.2.1" {
			foundSimulatedIP = true
			break
		}
	}
	
	if !foundSimulatedIP {
		t.Error("Expected simulated IP 192.0.2.1 in auth failures")
	}
	
	t.Logf("Simulate attack test passed: %d auth failures, %d CPU samples, %d events, %d alerts",
		len(agent.authFailures), len(agent.cpuSamples), len(agent.eventBuffer), len(agent.localAlerts))
}

// TestAlertScoring tests the alert scoring system
func TestAlertScoring(t *testing.T) {
	config := Config{}
	agent, err := NewAgent(config)
	if err != nil {
		t.Fatalf("Failed to create agent: %v", err)
	}
	
	// Test individual alert scores
	testCases := []struct {
		alerts        []string
		expectedScore float64
	}{
		{[]string{"CPU_SPIKE"}, 0.4},
		{[]string{"BRUTE_FORCE:192.168.1.1"}, 0.5},
		{[]string{"SHELL_IN_CONTAINER"}, 0.6},
		{[]string{"HTTP_5XX_SPIKE"}, 0.25},
		{[]string{"CPU_SPIKE", "BRUTE_FORCE:10.0.0.1"}, 0.9},
		{[]string{"CPU_SPIKE", "SHELL_IN_CONTAINER", "BRUTE_FORCE:1.2.3.4"}, 1.5},
	}
	
	for _, tc := range testCases {
		score := agent.calculateScore(tc.alerts)
		if math.Abs(score-tc.expectedScore) > 0.001 {
			t.Errorf("Expected score %.3f for alerts %v, got %.3f", tc.expectedScore, tc.alerts, score)
		}
	}
	
	t.Log("Alert scoring test passed")
}

// TestSensitiveDataMasking tests the sensitive data masking functionality
func TestSensitiveDataMasking(t *testing.T) {
	config := Config{}
	agent, err := NewAgent(config)
	if err != nil {
		t.Fatalf("Failed to create agent: %v", err)
	}
	
	testCases := []struct {
		input    string
		expected string
	}{
		{"password=secret123", "password=[REDACTED]"},
		{"token=abc123def", "token=[REDACTED]"},
		{"API_KEY=xyz789", "API_KEY=[REDACTED]"},
		{`"password": "secret123"`, `"password": "[REDACTED]"`},
		{`"token": "bearer abc123"`, `"token": "[REDACTED]"`},
		{"normal log message", "normal log message"},
		{"user=john password=secret", "user=john password=[REDACTED]"},
	}
	
	for _, tc := range testCases {
		result := agent.maskSensitiveData(tc.input)
		if result != tc.expected {
			t.Errorf("Expected '%s' for input '%s', got '%s'", tc.expected, tc.input, result)
		}
	}
	
	t.Log("Sensitive data masking test passed")
}

// TestBruteForceDetection tests the brute force detection logic
func TestBruteForceDetection(t *testing.T) {
	config := Config{
		AuthWindowSeconds:   300,
		FailedAuthThreshold: 5, // Lower threshold for testing
	}
	
	agent, err := NewAgent(config)
	if err != nil {
		t.Fatalf("Failed to create agent: %v", err)
	}
	
	// Add auth failures for the same IP
	testIP := "192.168.1.100"
	now := time.Now()
	
	// Add failures within the window
	for i := 0; i < 6; i++ {
		agent.authFailures = append(agent.authFailures, AuthFailure{
			IP:        testIP,
			Timestamp: now.Add(-time.Duration(i*30) * time.Second), // Spread over 150 seconds
		})
	}
	
	// Add some failures outside the window (should be ignored)
	agent.authFailures = append(agent.authFailures, AuthFailure{
		IP:        testIP,
		Timestamp: now.Add(-400 * time.Second), // Outside 300s window
	})
	
	// Clear existing alerts
	agent.localAlerts = agent.localAlerts[:0]
	
	// Check for brute force attacks
	agent.checkBruteForceAttacks()
	
	// Verify that brute force alert was generated
	expectedAlert := "BRUTE_FORCE:" + testIP
	found := false
	for _, alert := range agent.localAlerts {
		if alert == expectedAlert {
			found = true
			break
		}
	}
	
	if !found {
		t.Errorf("Expected brute force alert '%s' to be generated", expectedAlert)
	}
	
	t.Logf("Brute force detection test passed: detected attack from %s", testIP)
}