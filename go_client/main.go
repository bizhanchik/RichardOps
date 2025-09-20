/*
CHANGELOG:
- Added local security signals with auth log parsing and brute force detection
- Implemented CPU baseline and z-score anomaly detection with sliding window
- Added simulate attack mode for testing security alerts
- Implemented disk persistence for queued payloads with rotation
- Added graceful shutdown with signal handling and context cancellation
- Added health HTTP endpoint with uptime and metrics
- Improved Docker log streaming with proper stdcopy handling
- Enhanced HMAC security with timestamp verification
- Added metadata configuration fields (env, owner-team, server-id)
- Implemented log truncation and sensitive data masking
- Added simple scoring system for alerts
- Included unit test examples
*/

package main

import (
	"bufio"
	"bytes"
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"math"
	"net"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/events"
	"github.com/docker/docker/client"
	"github.com/docker/docker/pkg/stdcopy"
	"github.com/fsnotify/fsnotify"
	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/mem"
	psnet "github.com/shirou/gopsutil/v3/net"
)

// Configuration holds all configuration options
type Config struct {
	ServerURL            string
	Secret               string
	Interval             int
	TailLines            int
	AuthWindowSeconds    int
	CPUSpikePct          float64
	FailedAuthThreshold  int
	BaselineSamples      int
	SimulateAttack       bool
	Env                  string
	OwnerTeam            string
	ServerID             string
	MaxLogEntries        int
}

// SystemMetrics represents system performance metrics
type SystemMetrics struct {
	CPUUsage     float64 `json:"cpu_usage"`
	MemoryUsage  float64 `json:"memory_usage"`
	DiskUsage    float64 `json:"disk_usage"`
	NetworkRX    uint64  `json:"network_rx_bytes_per_sec"`
	NetworkTX    uint64  `json:"network_tx_bytes_per_sec"`
	TCPConns     int     `json:"tcp_connections"`
}

// DockerEvent represents a Docker event
type DockerEvent struct {
	Type      string    `json:"type"`
	Action    string    `json:"action"`
	Container string    `json:"container"`
	Image     string    `json:"image"`
	Timestamp time.Time `json:"timestamp"`
}

// LogEntry represents a container log entry
type LogEntry struct {
	Container string    `json:"container"`
	Message   string    `json:"message"`
	Timestamp time.Time `json:"timestamp"`
}

// Payload represents the complete monitoring payload
type Payload struct {
	Host         string         `json:"host"`
	ServerID     string         `json:"server_id,omitempty"`
	Env          string         `json:"env,omitempty"`
	OwnerTeam    string         `json:"owner_team,omitempty"`
	Timestamp    time.Time      `json:"timestamp"`
	Metrics      SystemMetrics  `json:"metrics"`
	DockerEvents []DockerEvent  `json:"docker_events"`
	Logs         []LogEntry     `json:"logs"`
	LocalAlerts  []string       `json:"local_alerts"`
	Score        float64        `json:"score"`
}

// HealthStatus represents health endpoint response
type HealthStatus struct {
	UptimeSeconds int       `json:"uptime_seconds"`
	LastSendOK    time.Time `json:"last_send_ok"`
	QueueLength   int       `json:"queue_length"`
}

// MetricsStatus represents metrics endpoint response
type MetricsStatus struct {
	CPU         float64  `json:"cpu_usage"`
	Memory      float64  `json:"memory_usage"`
	LocalAlerts []string `json:"local_alerts"`
}

// CPUSample represents a CPU usage sample for baseline calculation
type CPUSample struct {
	Value     float64
	Timestamp time.Time
}

// AuthFailure represents a failed authentication attempt
type AuthFailure struct {
	IP        string
	Timestamp time.Time
}

// Agent represents the monitoring agent
type Agent struct {
	config       Config
	dockerClient *client.Client
	httpClient   *http.Client
	startTime    time.Time
	lastSendOK   time.Time
	
	// Data buffers
	eventBuffer []DockerEvent
	logBuffer   []LogEntry
	
	// Security monitoring
	authFailures []AuthFailure
	localAlerts  []string
	
	// CPU baseline tracking
	cpuSamples []CPUSample
	
	// Synchronization
	eventMutex   sync.RWMutex
	logMutex     sync.RWMutex
	alertMutex   sync.RWMutex
	cpuMutex     sync.RWMutex
	
	// Network stats for rate calculation
	lastNetStats map[string]psnet.IOCountersStat
	lastNetTime  time.Time
	netMutex     sync.RWMutex
	
	// Queue for failed requests
	payloadQueue []Payload
	queueMutex   sync.Mutex
	
	// Health server
	healthServer *http.Server
	
	// File watcher for auth logs
	authWatcher *fsnotify.Watcher
	
	// Sensitive data patterns
	sensitivePatterns []*regexp.Regexp
}

// Alert scoring weights
var alertWeights = map[string]float64{
	"CPU_SPIKE":           0.4,
	"BRUTE_FORCE":         0.5,
	"SHELL_IN_CONTAINER":  0.6,
	"HTTP_5XX_SPIKE":      0.25,
}

// NewAgent creates a new monitoring agent
func NewAgent(config Config) (*Agent, error) {
	var dockerClient *client.Client
	var err error
	
	// Try to create Docker client, but don't fail if Docker is not available
	dockerClient, err = client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		log.Printf("Warning: Failed to create Docker client, running in degraded mode: %v", err)
		dockerClient = nil
	}

	httpClient := &http.Client{
		Timeout: 30 * time.Second,
	}

	// Compile sensitive data patterns
	patterns := []*regexp.Regexp{
		regexp.MustCompile(`(?i)(password|token|secret|key|auth)=([^\s&]+)`),
		regexp.MustCompile(`(?i)"(password|token|secret|key|auth)"\s*:\s*"([^"]+)"`),
	}

	agent := &Agent{
		config:            config,
		dockerClient:      dockerClient,
		httpClient:        httpClient,
		startTime:         time.Now(),
		eventBuffer:       make([]DockerEvent, 0, 100),
		logBuffer:         make([]LogEntry, 0, config.MaxLogEntries),
		authFailures:      make([]AuthFailure, 0, 1000),
		localAlerts:       make([]string, 0),
		cpuSamples:        make([]CPUSample, 0, config.BaselineSamples),
		lastNetStats:      make(map[string]psnet.IOCountersStat),
		lastNetTime:       time.Now(),
		payloadQueue:      make([]Payload, 0),
		sensitivePatterns: patterns,
	}

	// Create queue directory
	if err := os.MkdirAll("./queue", 0755); err != nil {
		log.Printf("Warning: Failed to create queue directory: %v", err)
	}

	// Load persisted payloads
	if err := agent.loadPersistedPayloads(); err != nil {
		log.Printf("Warning: Failed to load persisted payloads: %v", err)
	}

	// Setup auth log monitoring
	if err := agent.setupAuthLogMonitoring(); err != nil {
		log.Printf("Warning: Failed to setup auth log monitoring: %v", err)
	}

	// Setup health server
	agent.setupHealthServer()

	return agent, nil
}

// setupAuthLogMonitoring sets up file watching for auth logs
func (a *Agent) setupAuthLogMonitoring() error {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return err
	}
	a.authWatcher = watcher

	// Try common auth log paths
	authPaths := []string{"/var/log/auth.log", "/var/log/secure"}
	var watchedPath string
	
	for _, path := range authPaths {
		if _, err := os.Stat(path); err == nil {
			if err := watcher.Add(path); err == nil {
				watchedPath = path
				log.Printf("Monitoring auth log: %s", path)
				break
			}
		}
	}
	
	if watchedPath == "" {
		log.Printf("Warning: No auth log found, security monitoring disabled")
		return nil
	}

	// Start monitoring goroutine
	go a.monitorAuthLog(watchedPath)
	
	return nil
}

// monitorAuthLog monitors auth log for failed login attempts
func (a *Agent) monitorAuthLog(logPath string) {
	// Read existing log entries first
	a.parseAuthLogFile(logPath)
	
	for {
		select {
		case event, ok := <-a.authWatcher.Events:
			if !ok {
				return
			}
			if event.Op&fsnotify.Write == fsnotify.Write {
				a.parseAuthLogFile(logPath)
			}
		case err, ok := <-a.authWatcher.Errors:
			if !ok {
				return
			}
			log.Printf("Auth log watcher error: %v", err)
		}
	}
}

// parseAuthLogFile parses auth log file for failed login attempts
func (a *Agent) parseAuthLogFile(logPath string) {
	file, err := os.Open(logPath)
	if err != nil {
		return
	}
	defer file.Close()

	// Seek to end and read backwards (simplified approach)
	scanner := bufio.NewScanner(file)
	var lines []string
	for scanner.Scan() {
		lines = append(lines, scanner.Text())
	}

	// Process recent lines (last 1000)
	start := 0
	if len(lines) > 1000 {
		start = len(lines) - 1000
	}

	failedAuthPattern := regexp.MustCompile(`Failed password for .* from (\d+\.\d+\.\d+\.\d+)`)
	
	for i := start; i < len(lines); i++ {
		line := lines[i]
		if matches := failedAuthPattern.FindStringSubmatch(line); len(matches) > 1 {
			ip := matches[1]
			a.alertMutex.Lock()
			a.authFailures = append(a.authFailures, AuthFailure{
				IP:        ip,
				Timestamp: time.Now(), // Simplified - should parse timestamp from log
			})
			// Keep buffer manageable
			if len(a.authFailures) > 1000 {
				a.authFailures = a.authFailures[100:]
			}
			a.alertMutex.Unlock()
		}
	}
}

// checkBruteForceAttacks checks for brute force attacks
func (a *Agent) checkBruteForceAttacks() {
	a.alertMutex.Lock()
	defer a.alertMutex.Unlock()

	now := time.Now()
	windowStart := now.Add(-time.Duration(a.config.AuthWindowSeconds) * time.Second)
	
	// Count failures per IP in the window
	ipCounts := make(map[string]int)
	for _, failure := range a.authFailures {
		if failure.Timestamp.After(windowStart) {
			ipCounts[failure.IP]++
		}
	}
	
	// Check for brute force
	for ip, count := range ipCounts {
		if count >= a.config.FailedAuthThreshold {
			alert := fmt.Sprintf("BRUTE_FORCE:%s", ip)
			if !a.containsAlert(alert) {
				a.localAlerts = append(a.localAlerts, alert)
				log.Printf("Brute force detected from IP %s: %d failed attempts", ip, count)
			}
		}
	}
}

// containsAlert checks if alert already exists
func (a *Agent) containsAlert(alert string) bool {
	for _, existing := range a.localAlerts {
		if existing == alert {
			return true
		}
	}
	return false
}

// updateCPUBaseline updates CPU baseline and checks for anomalies
func (a *Agent) updateCPUBaseline(cpuUsage float64) {
	a.cpuMutex.Lock()
	defer a.cpuMutex.Unlock()

	// Add new sample
	sample := CPUSample{
		Value:     cpuUsage,
		Timestamp: time.Now(),
	}
	a.cpuSamples = append(a.cpuSamples, sample)
	
	// Keep only recent samples
	if len(a.cpuSamples) > a.config.BaselineSamples {
		a.cpuSamples = a.cpuSamples[1:]
	}
	
	// Need at least 3 samples for meaningful statistics
	if len(a.cpuSamples) < 3 {
		return
	}
	
	// Calculate mean and standard deviation
	var sum, sumSquares float64
	for _, s := range a.cpuSamples {
		sum += s.Value
		sumSquares += s.Value * s.Value
	}
	
	n := float64(len(a.cpuSamples))
	mean := sum / n
	variance := (sumSquares / n) - (mean * mean)
	stdDev := math.Sqrt(variance)
	
	// Calculate z-score for current sample
	if stdDev > 0 {
		zScore := (cpuUsage - mean) / stdDev
		
		// Check for CPU spike
		if cpuUsage >= a.config.CPUSpikePct && zScore >= 3.0 {
			a.alertMutex.Lock()
			if !a.containsAlert("CPU_SPIKE") {
				a.localAlerts = append(a.localAlerts, "CPU_SPIKE")
				log.Printf("CPU spike detected: %.2f%% (z-score: %.2f)", cpuUsage, zScore)
			}
			a.alertMutex.Unlock()
		}
	}
}

// simulateAttack generates synthetic attack events for testing
func (a *Agent) simulateAttack() {
	if !a.config.SimulateAttack {
		return
	}
	
	log.Printf("Simulating attack events...")
	
	// Simulate brute force
	a.alertMutex.Lock()
	for i := 0; i < a.config.FailedAuthThreshold+5; i++ {
		a.authFailures = append(a.authFailures, AuthFailure{
			IP:        "192.0.2.1",
			Timestamp: time.Now(),
		})
	}
	a.alertMutex.Unlock()
	
	// Simulate CPU spike
	a.cpuMutex.Lock()
	for i := 0; i < 5; i++ {
		a.cpuSamples = append(a.cpuSamples, CPUSample{
			Value:     a.config.CPUSpikePct + 10,
			Timestamp: time.Now(),
		})
	}
	a.cpuMutex.Unlock()
	
	// Simulate shell in container
	a.eventMutex.Lock()
	a.eventBuffer = append(a.eventBuffer, DockerEvent{
		Type:      "container",
		Action:    "exec_create: /bin/bash",
		Container: "test-container",
		Image:     "test-image",
		Timestamp: time.Now(),
	})
	a.eventMutex.Unlock()
	
	a.alertMutex.Lock()
	a.localAlerts = append(a.localAlerts, "SHELL_IN_CONTAINER")
	a.alertMutex.Unlock()
}

// collectSystemMetrics gathers system performance metrics
func (a *Agent) collectSystemMetrics() (SystemMetrics, error) {
	var metrics SystemMetrics

	// CPU usage
	cpuPercent, err := cpu.Percent(time.Second, false)
	if err != nil {
		log.Printf("Error collecting CPU metrics: %v", err)
	} else if len(cpuPercent) > 0 {
		metrics.CPUUsage = cpuPercent[0]
		// Update baseline and check for anomalies
		a.updateCPUBaseline(metrics.CPUUsage)
	}

	// Memory usage
	memInfo, err := mem.VirtualMemory()
	if err != nil {
		log.Printf("Error collecting memory metrics: %v", err)
	} else {
		metrics.MemoryUsage = memInfo.UsedPercent
	}

	// Disk usage (root partition)
	diskInfo, err := disk.Usage("/")
	if err != nil {
		log.Printf("Error collecting disk metrics: %v", err)
	} else {
		metrics.DiskUsage = diskInfo.UsedPercent
	}

	// Network statistics
	netStats, err := psnet.IOCounters(false)
	if err != nil {
		log.Printf("Error collecting network metrics: %v", err)
	} else if len(netStats) > 0 {
		a.netMutex.Lock()
		currentTime := time.Now()
		if !a.lastNetTime.IsZero() {
			timeDiff := currentTime.Sub(a.lastNetTime).Seconds()
			if timeDiff > 0 {
				for _, stat := range netStats {
					if lastStat, exists := a.lastNetStats[stat.Name]; exists {
						rxDiff := stat.BytesRecv - lastStat.BytesRecv
						txDiff := stat.BytesSent - lastStat.BytesSent
						metrics.NetworkRX += uint64(float64(rxDiff) / timeDiff)
						metrics.NetworkTX += uint64(float64(txDiff) / timeDiff)
					}
					a.lastNetStats[stat.Name] = stat
				}
			}
		} else {
			for _, stat := range netStats {
				a.lastNetStats[stat.Name] = stat
			}
		}
		a.lastNetTime = currentTime
		a.netMutex.Unlock()
	}

	// TCP connections
	conns, err := psnet.Connections("tcp")
	if err != nil {
		log.Printf("Error collecting TCP connection metrics: %v", err)
	} else {
		metrics.TCPConns = len(conns)
	}

	return metrics, nil
}

// monitorDockerEvents listens for Docker events
func (a *Agent) monitorDockerEvents(ctx context.Context) {
	if a.dockerClient == nil {
		log.Printf("Docker client not available, skipping Docker monitoring")
		return
	}
	
	eventChan, errChan := a.dockerClient.Events(ctx, types.EventsOptions{})

	for {
		select {
		case event := <-eventChan:
			if event.Type == events.ContainerEventType {
				dockerEvent := DockerEvent{
					Type:      string(event.Type),
					Action:    event.Action,
					Container: event.Actor.Attributes["name"],
					Image:     event.Actor.Attributes["image"],
					Timestamp: time.Unix(event.Time, 0),
				}

				a.eventMutex.Lock()
				a.eventBuffer = append(a.eventBuffer, dockerEvent)
				// Keep buffer size manageable
				if len(a.eventBuffer) > 100 {
					a.eventBuffer = a.eventBuffer[1:]
				}
				a.eventMutex.Unlock()

				log.Printf("Docker event: %s %s %s", dockerEvent.Action, dockerEvent.Container, dockerEvent.Image)

				// Check for shell execution
				if strings.Contains(event.Action, "exec") && 
				   (strings.Contains(event.Action, "/bin/bash") || strings.Contains(event.Action, "/bin/sh")) {
					a.alertMutex.Lock()
					if !a.containsAlert("SHELL_IN_CONTAINER") {
						a.localAlerts = append(a.localAlerts, "SHELL_IN_CONTAINER")
						log.Printf("Shell execution detected in container: %s", dockerEvent.Container)
					}
					a.alertMutex.Unlock()
				}

				// If it's a start event, start monitoring logs for this container
				if event.Action == "start" {
					go a.monitorContainerLogs(ctx, event.Actor.ID)
				}
			}
		case err := <-errChan:
			if err != nil {
				log.Printf("Error monitoring Docker events: %v", err)
				time.Sleep(5 * time.Second) // Wait before retrying
			}
		case <-ctx.Done():
			return
		}
	}
}

// monitorContainerLogs monitors logs for a specific container
func (a *Agent) monitorContainerLogs(ctx context.Context, containerID string) {
	if a.dockerClient == nil {
		return
	}
	
	// Get container info
	containerInfo, err := a.dockerClient.ContainerInspect(ctx, containerID)
	if err != nil {
		log.Printf("Error inspecting container %s: %v", containerID, err)
		return
	}

	// Get initial logs
	logOptions := types.ContainerLogsOptions{
		ShowStdout: true,
		ShowStderr: true,
		Tail:       strconv.Itoa(a.config.TailLines),
		Follow:     true,
		Timestamps: true,
	}

	logReader, err := a.dockerClient.ContainerLogs(ctx, containerID, logOptions)
	if err != nil {
		log.Printf("Error getting logs for container %s: %v", containerID, err)
		return
	}
	defer logReader.Close()

	// Use proper stdcopy decoder
	stdout := &bytes.Buffer{}
	stderr := &bytes.Buffer{}
	
	go func() {
		_, err := stdcopy.StdCopy(stdout, stderr, logReader)
		if err != nil && err != io.EOF {
			log.Printf("Error reading logs for container %s: %v", containerID, err)
		}
	}()

	// Process logs periodically
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			// Process stdout
			for {
				line, err := stdout.ReadString('\n')
				if err != nil {
					break
				}
				a.processLogLine(containerInfo.Name, strings.TrimSpace(line))
			}
			
			// Process stderr
			for {
				line, err := stderr.ReadString('\n')
				if err != nil {
					break
				}
				a.processLogLine(containerInfo.Name, strings.TrimSpace(line))
			}
			
		case <-ctx.Done():
			return
		}
	}
}

// processLogLine processes a single log line
func (a *Agent) processLogLine(containerName, logMessage string) {
	if logMessage == "" {
		return
	}
	
	// Mask sensitive data
	maskedMessage := a.maskSensitiveData(logMessage)
	
	// Truncate if too long
	if len(maskedMessage) > 1024 {
		maskedMessage = maskedMessage[:1021] + "..."
	}
	
	logEntry := LogEntry{
		Container: containerName,
		Message:   maskedMessage,
		Timestamp: time.Now(),
	}

	a.logMutex.Lock()
	a.logBuffer = append(a.logBuffer, logEntry)
	// Keep buffer size manageable
	if len(a.logBuffer) > a.config.MaxLogEntries {
		a.logBuffer = a.logBuffer[1:]
	}
	a.logMutex.Unlock()
}

// maskSensitiveData masks sensitive information in log messages
func (a *Agent) maskSensitiveData(message string) string {
	result := message
	for _, pattern := range a.sensitivePatterns {
		result = pattern.ReplaceAllString(result, "${1}=[REDACTED]")
	}
	return result
}

// calculateScore calculates alert score based on weights
func (a *Agent) calculateScore(alerts []string) float64 {
	var score float64
	for _, alert := range alerts {
		// Extract base alert type (remove IP suffix for BRUTE_FORCE)
		alertType := alert
		if strings.HasPrefix(alert, "BRUTE_FORCE:") {
			alertType = "BRUTE_FORCE"
		}
		
		if weight, exists := alertWeights[alertType]; exists {
			score += weight
		}
	}
	return score
}

// createPayload creates a monitoring payload
func (a *Agent) createPayload() (Payload, error) {
	hostname, err := os.Hostname()
	if err != nil {
		hostname = "unknown"
	}

	metrics, err := a.collectSystemMetrics()
	if err != nil {
		log.Printf("Error collecting system metrics: %v", err)
	}

	// Check for security alerts
	a.checkBruteForceAttacks()
	
	// Simulate attack if enabled
	a.simulateAttack()

	// Copy current events and logs
	a.eventMutex.RLock()
	events := make([]DockerEvent, len(a.eventBuffer))
	copy(events, a.eventBuffer)
	a.eventMutex.RUnlock()

	a.logMutex.RLock()
	logs := make([]LogEntry, len(a.logBuffer))
	copy(logs, a.logBuffer)
	a.logMutex.RUnlock()

	// Copy current alerts
	a.alertMutex.RLock()
	alerts := make([]string, len(a.localAlerts))
	copy(alerts, a.localAlerts)
	a.alertMutex.RUnlock()

	payload := Payload{
		Host:         hostname,
		ServerID:     a.config.ServerID,
		Env:          a.config.Env,
		OwnerTeam:    a.config.OwnerTeam,
		Timestamp:    time.Now(),
		Metrics:      metrics,
		DockerEvents: events,
		Logs:         logs,
		LocalAlerts:  alerts,
		Score:        a.calculateScore(alerts),
	}

	return payload, nil
}

// signPayload creates HMAC signature for the payload with timestamp
func (a *Agent) signPayload(payload []byte, timestamp time.Time) string {
	// Check for clock drift
	now := time.Now()
	if math.Abs(now.Sub(timestamp).Minutes()) > 2 {
		log.Printf("Warning: Clock drift detected: %v", now.Sub(timestamp))
	}
	
	// Sign timestamp + payload
	message := fmt.Sprintf("%d.%s", timestamp.Unix(), string(payload))
	h := hmac.New(sha256.New, []byte(a.config.Secret))
	h.Write([]byte(message))
	return hex.EncodeToString(h.Sum(nil))
}

// sendPayload sends payload to the server with retry logic
func (a *Agent) sendPayload(payload Payload) error {
	payloadBytes, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal payload: %w", err)
	}

	signature := a.signPayload(payloadBytes, payload.Timestamp)

	maxRetries := 3
	baseDelay := time.Second

	for attempt := 0; attempt < maxRetries; attempt++ {
		req, err := http.NewRequest("POST", a.config.ServerURL, bytes.NewBuffer(payloadBytes))
		if err != nil {
			return fmt.Errorf("failed to create request: %w", err)
		}

		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("X-Agent-Signature", fmt.Sprintf("sha256=%s", signature))
		req.Header.Set("X-Agent-Timestamp", strconv.FormatInt(payload.Timestamp.Unix(), 10))

		resp, err := a.httpClient.Do(req)
		if err == nil {
			resp.Body.Close()
			if resp.StatusCode >= 200 && resp.StatusCode < 300 {
				log.Printf("Successfully sent payload to server (status: %d)", resp.StatusCode)
				a.lastSendOK = time.Now()
				return nil
			}
			log.Printf("Server returned error status: %d", resp.StatusCode)
		} else {
			log.Printf("Failed to send payload (attempt %d/%d): %v", attempt+1, maxRetries, err)
		}

		if attempt < maxRetries-1 {
			delay := time.Duration(math.Pow(2, float64(attempt))) * baseDelay
			log.Printf("Retrying in %v...", delay)
			time.Sleep(delay)
		}
	}

	// If all retries failed, queue the payload
	a.queueMutex.Lock()
	a.payloadQueue = append(a.payloadQueue, payload)
	// Keep queue size manageable
	if len(a.payloadQueue) > 50 {
		a.payloadQueue = a.payloadQueue[1:]
	}
	a.queueMutex.Unlock()

	// Persist to disk
	if err := a.persistPayload(payload); err != nil {
		log.Printf("Failed to persist payload: %v", err)
	}

	return fmt.Errorf("failed to send payload after %d attempts", maxRetries)
}

// persistPayload saves payload to disk
func (a *Agent) persistPayload(payload Payload) error {
	// Create filename with timestamp
	filename := fmt.Sprintf("queue_%d.jsonl", time.Now().Unix())
	filepath := filepath.Join("./queue", filename)
	
	file, err := os.OpenFile(filepath, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	defer file.Close()
	
	payloadBytes, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	
	_, err = file.Write(append(payloadBytes, '\n'))
	if err != nil {
		return err
	}
	
	// Rotate files if needed
	go a.rotateQueueFiles()
	
	return nil
}

// rotateQueueFiles manages queue file rotation
func (a *Agent) rotateQueueFiles() {
	files, err := filepath.Glob("./queue/queue_*.jsonl")
	if err != nil {
		return
	}
	
	// Sort files by modification time
	type fileInfo struct {
		path    string
		modTime time.Time
		size    int64
	}
	
	var fileInfos []fileInfo
	for _, file := range files {
		info, err := os.Stat(file)
		if err != nil {
			continue
		}
		fileInfos = append(fileInfos, fileInfo{
			path:    file,
			modTime: info.ModTime(),
			size:    info.Size(),
		})
	}
	
	// Sort by modification time (oldest first)
	sort.Slice(fileInfos, func(i, j int) bool {
		return fileInfos[i].modTime.Before(fileInfos[j].modTime)
	})
	
	// Remove old files if we have more than 10
	if len(fileInfos) > 10 {
		for i := 0; i < len(fileInfos)-10; i++ {
			os.Remove(fileInfos[i].path)
		}
	}
	
	// Remove files larger than 50MB
	for _, info := range fileInfos {
		if info.size > 50*1024*1024 {
			os.Remove(info.path)
		}
	}
}

// loadPersistedPayloads loads payloads from disk
func (a *Agent) loadPersistedPayloads() error {
	files, err := filepath.Glob("./queue/queue_*.jsonl")
	if err != nil {
		return err
	}
	
	for _, file := range files {
		if err := a.loadPayloadsFromFile(file); err != nil {
			log.Printf("Error loading payloads from %s: %v", file, err)
		}
	}
	
	return nil
}

// loadPayloadsFromFile loads payloads from a specific file
func (a *Agent) loadPayloadsFromFile(filename string) error {
	file, err := os.Open(filename)
	if err != nil {
		return err
	}
	defer file.Close()
	
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		var payload Payload
		if err := json.Unmarshal(scanner.Bytes(), &payload); err != nil {
			log.Printf("Error unmarshaling payload: %v", err)
			continue
		}
		
		a.queueMutex.Lock()
		a.payloadQueue = append(a.payloadQueue, payload)
		a.queueMutex.Unlock()
	}
	
	// Remove the file after loading
	os.Remove(filename)
	
	return scanner.Err()
}

// processQueue attempts to send queued payloads
func (a *Agent) processQueue() {
	a.queueMutex.Lock()
	if len(a.payloadQueue) == 0 {
		a.queueMutex.Unlock()
		return
	}

	// Try to send the oldest payload
	payload := a.payloadQueue[0]
	a.queueMutex.Unlock()

	err := a.sendPayload(payload)
	if err == nil {
		// Successfully sent, remove from queue
		a.queueMutex.Lock()
		if len(a.payloadQueue) > 0 {
			a.payloadQueue = a.payloadQueue[1:]
		}
		a.queueMutex.Unlock()
		log.Printf("Successfully sent queued payload")
	}
}

// setupHealthServer sets up the health monitoring HTTP server
func (a *Agent) setupHealthServer() {
	mux := http.NewServeMux()
	
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		a.queueMutex.Lock()
		queueLen := len(a.payloadQueue)
		a.queueMutex.Unlock()
		
		status := HealthStatus{
			UptimeSeconds: int(time.Since(a.startTime).Seconds()),
			LastSendOK:    a.lastSendOK,
			QueueLength:   queueLen,
		}
		
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(status)
	})
	
	mux.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
		metrics, _ := a.collectSystemMetrics()
		
		a.alertMutex.RLock()
		alerts := make([]string, len(a.localAlerts))
		copy(alerts, a.localAlerts)
		a.alertMutex.RUnlock()
		
		status := MetricsStatus{
			CPU:         metrics.CPUUsage,
			Memory:      metrics.MemoryUsage,
			LocalAlerts: alerts,
		}
		
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(status)
	})
	
	a.healthServer = &http.Server{
		Addr:    "localhost:8081",
		Handler: mux,
	}
	
	go func() {
		log.Printf("Health server starting on localhost:8081")
		if err := a.healthServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Printf("Health server error: %v", err)
		}
	}()
}

// Run starts the monitoring agent
func (a *Agent) Run(ctx context.Context) error {
	log.Printf("Starting monitoring agent...")
	log.Printf("Server URL: %s", a.config.ServerURL)
	log.Printf("Interval: %d seconds", a.config.Interval)
	log.Printf("Tail lines: %d", a.config.TailLines)
	log.Printf("Simulate attack: %v", a.config.SimulateAttack)

	// Start Docker event monitoring
	go a.monitorDockerEvents(ctx)

	// Start monitoring existing containers
	if a.dockerClient != nil {
		containers, err := a.dockerClient.ContainerList(ctx, types.ContainerListOptions{})
		if err != nil {
			log.Printf("Error listing containers: %v", err)
		} else {
			for _, container := range containers {
				if container.State == "running" {
					go a.monitorContainerLogs(ctx, container.ID)
				}
			}
		}
	}

	// Main loop for sending payloads
	ticker := time.NewTicker(time.Duration(a.config.Interval) * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			payload, err := a.createPayload()
			if err != nil {
				log.Printf("Error creating payload: %v", err)
				continue
			}

			// Try to process any queued payloads first
			a.processQueue()

			// Send current payload
			if err := a.sendPayload(payload); err != nil {
				log.Printf("Error sending payload: %v", err)
			}

			// Clear processed alerts after sending
			a.alertMutex.Lock()
			a.localAlerts = a.localAlerts[:0]
			a.alertMutex.Unlock()

		case <-ctx.Done():
			log.Printf("Shutting down monitoring agent...")
			
			// Try to send final payload
			if payload, err := a.createPayload(); err == nil {
				a.sendPayload(payload)
			}
			
			// Close health server
			if a.healthServer != nil {
				a.healthServer.Shutdown(context.Background())
			}
			
			// Close auth watcher
			if a.authWatcher != nil {
				a.authWatcher.Close()
			}
			
			return nil
		}
	}
}

// parseConfig parses configuration from command line flags and environment variables
func parseConfig() Config {
	var config Config

	flag.StringVar(&config.ServerURL, "server-url", "", "Server URL for sending payloads")
	flag.StringVar(&config.Secret, "secret", "", "Shared secret for HMAC signing")
	flag.IntVar(&config.Interval, "interval", 30, "Interval in seconds between payload sends")
	flag.IntVar(&config.TailLines, "tail-lines", 100, "Number of initial log lines to tail")
	flag.IntVar(&config.AuthWindowSeconds, "auth-window-seconds", 300, "Window for auth failure detection")
	flag.Float64Var(&config.CPUSpikePct, "cpu-spike-pct", 85.0, "CPU percentage threshold for spike detection")
	flag.IntVar(&config.FailedAuthThreshold, "failed-auth-threshold", 20, "Failed auth attempts threshold")
	flag.IntVar(&config.BaselineSamples, "baseline-samples", 12, "Number of samples for CPU baseline")
	flag.BoolVar(&config.SimulateAttack, "simulate-attack", false, "Enable attack simulation mode")
	flag.StringVar(&config.Env, "env", "", "Environment (prod/stage/dev)")
	flag.StringVar(&config.OwnerTeam, "owner-team", "", "Owner team name")
	flag.StringVar(&config.ServerID, "server-id", "", "Server identifier")
	flag.IntVar(&config.MaxLogEntries, "max-log-entries", 500, "Maximum log entries to keep")
	flag.Parse()

	// Override with environment variables if set
	if serverURL := os.Getenv("SERVER_URL"); serverURL != "" {
		config.ServerURL = serverURL
	}
	if secret := os.Getenv("SECRET"); secret != "" {
		config.Secret = secret
	}
	if interval := os.Getenv("INTERVAL"); interval != "" {
		if i, err := strconv.Atoi(interval); err == nil {
			config.Interval = i
		}
	}
	if tailLines := os.Getenv("TAIL_LINES"); tailLines != "" {
		if i, err := strconv.Atoi(tailLines); err == nil {
			config.TailLines = i
		}
	}
	if authWindow := os.Getenv("AUTH_WINDOW_SECONDS"); authWindow != "" {
		if i, err := strconv.Atoi(authWindow); err == nil {
			config.AuthWindowSeconds = i
		}
	}
	if cpuSpike := os.Getenv("CPU_SPIKE_PCT"); cpuSpike != "" {
		if f, err := strconv.ParseFloat(cpuSpike, 64); err == nil {
			config.CPUSpikePct = f
		}
	}
	if failedAuth := os.Getenv("FAILED_AUTH_THRESHOLD"); failedAuth != "" {
		if i, err := strconv.Atoi(failedAuth); err == nil {
			config.FailedAuthThreshold = i
		}
	}
	if baseline := os.Getenv("BASELINE_SAMPLES"); baseline != "" {
		if i, err := strconv.Atoi(baseline); err == nil {
			config.BaselineSamples = i
		}
	}
	if simulate := os.Getenv("SIMULATE_ATTACK"); simulate == "true" {
		config.SimulateAttack = true
	}
	if env := os.Getenv("ENV"); env != "" {
		config.Env = env
	}
	if team := os.Getenv("OWNER_TEAM"); team != "" {
		config.OwnerTeam = team
	}
	if serverID := os.Getenv("SERVER_ID"); serverID != "" {
		config.ServerID = serverID
	}
	if maxLogs := os.Getenv("MAX_LOG_ENTRIES"); maxLogs != "" {
		if i, err := strconv.Atoi(maxLogs); err == nil {
			config.MaxLogEntries = i
		}
	}

	return config
}

func main() {
	config := parseConfig()

	if config.ServerURL == "" {
		log.Fatal("Server URL is required (use --server-url flag or SERVER_URL environment variable)")
	}
	if config.Secret == "" {
		log.Fatal("Secret is required (use --secret flag or SECRET environment variable)")
	}

	agent, err := NewAgent(config)
	if err != nil {
		log.Fatalf("Failed to create agent: %v", err)
	}

	// Setup graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle signals
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigChan
		log.Printf("Received signal %v, shutting down gracefully...", sig)
		cancel()
	}()

	if err := agent.Run(ctx); err != nil {
		log.Fatalf("Agent error: %v", err)
	}
}