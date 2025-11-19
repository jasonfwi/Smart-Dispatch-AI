// ================================
// SMART DISPATCH AI - FRONTEND
// ================================

// Global state
const state = {
    initialized: false,
    currentData: [],
    currentColumns: [],
    editedRows: new Map(), // rowIndex -> {column: value}
    cityStateMapping: {},
    allCities: [],
    allStates: [],
    validSkills: [],
    validPriorities: [],
    addressOptions: [], // For autocomplete
    currentQueryContext: null, // Track what type of query was last run
    modalOriginalData: null, // Store original data for filtering in results modal
    techListOriginalData: null, // Store original data for filtering in tech list modal
    autoAssignData: null // Store auto-assignment data for commit
};

// ================================
// INITIALIZATION
// ================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize application
    restoreSystemMessagesState();
    restoreSelectedTab();
    initialize();
});

async function initialize() {
    try {
        showLoading(true);
        logMessage('Initializing Smart Dispatch AI...', 'header');
        
        // Load database mode indicator (don't block on this)
        loadDatabaseMode().catch(err => {
            console.warn('Failed to load database mode:', err);
        });
        
        const maxRange = document.getElementById('maxRange').value;
        
        const response = await fetch('/api/init', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({max_range_km: parseFloat(maxRange)})
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            state.initialized = true;
            state.allStates = data.states || [];
            state.allCities = data.cities || [];
            state.cityStateMapping = data.city_state_mapping || {};
            
            // Populate dropdowns
            if (data.states && Array.isArray(data.states)) {
                populateStateDropdown(data.states);
            } else {
                console.error('Invalid states data received:', data.states);
            }
            if (data.cities && Array.isArray(data.cities)) {
                populateCityDropdown(data.cities);
            } else {
                console.error('Invalid cities data received:', data.cities);
            }
            
            // Populate creation form dropdowns
            if (data.states && Array.isArray(data.states)) {
                populateCreateStateDropdown(data.states);
            }
            
            // Load skills and priorities
            loadSkillsAndPriorities();
            
            // Set minimum date to tomorrow
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            const tomorrowStr = tomorrow.toISOString().split('T')[0];
            // Set minimum date to tomorrow for all date fields
            const createDateEl = document.getElementById('createDate');
            if (createDateEl) {
                createDateEl.min = tomorrowStr;
                createDateEl.value = tomorrowStr;
            }
            const startDateEl = document.getElementById('startDate');
            if (startDateEl) startDateEl.min = tomorrowStr;
            const endDateEl = document.getElementById('endDate');
            if (endDateEl) endDateEl.min = tomorrowStr;
            const capDateEl = document.getElementById('capDate');
            if (capDateEl) {
                capDateEl.min = tomorrowStr;
                capDateEl.value = tomorrowStr;
            }
            const assignDateEl = document.getElementById('assignDate');
            if (assignDateEl) {
                assignDateEl.min = tomorrowStr;
                assignDateEl.value = tomorrowStr;
            }
            
            // Populate capacity and assignment dropdowns
            if (data.states && Array.isArray(data.states)) {
                populateCapStateDropdown(data.states);
                populateAssignStateDropdown(data.states);
            }
            
            // Populate technician tab dropdowns
            if (data.states && Array.isArray(data.states)) {
                populateTechStateDropdown(data.states);
                populateCalStateDropdown(data.states);
            }
            
            // Set minimum dates for technician tab
            const techDateEl = document.getElementById('techDate');
            if (techDateEl) techDateEl.min = tomorrowStr;
            const techStartDateEl = document.getElementById('techStartDate');
            if (techStartDateEl) techStartDateEl.min = tomorrowStr;
            const techEndDateEl = document.getElementById('techEndDate');
            if (techEndDateEl) techEndDateEl.min = tomorrowStr;
            
            // Refresh pending dispatches count
            refreshPending();
            
            logMessage(`✅ ${data.message}`, 'success');
            logMessage(`📍 Loaded ${data.states.length - 1} states`, 'success');
            logMessage(`🏙️ Loaded ${data.cities.length - 1} cities`, 'success');
            
            updateStatus('ready', '✅ Ready');
        } else {
            throw new Error(data.error || 'Unknown initialization error');
        }
    } catch (error) {
        logMessage(`❌ Initialization failed: ${error.message}`, 'error');
        logMessage(`Check browser console (F12) for details`, 'error');
        updateStatus('error', '❌ Error');
        console.error('Initialization error:', error);
        if (error.stack) {
            console.error('Error stack:', error.stack);
        }
    } finally {
        showLoading(false);
    }
}

async function reinitialize() {
    state.initialized = false;
    clearAll();
    await initialize();
}

// Load and display database mode indicator
async function loadDatabaseMode() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        
        if (data.success && data.database_mode) {
            const dbModeBadge = document.getElementById('dbModeBadge');
            const dbModeText = document.getElementById('dbModeText');
            
            if (dbModeBadge && dbModeText) {
                const mode = data.database_mode;
                const isLocal = mode === 'local';
                
                // Update text
                dbModeText.textContent = 'Local DB';
                
                // Update styling
                dbModeBadge.className = 'db-mode-badge db-mode-local';
                
                // Update tooltip
                dbModeBadge.title = 'Using Local SQLite Database';
            }
        }
    } catch (error) {
        console.error('Failed to load database mode:', error);
        // Set default to Local DB
        const dbModeText = document.getElementById('dbModeText');
        if (dbModeText) {
            dbModeText.textContent = 'Local DB';
        }
    }
}

// ================================
// DROPDOWN MANAGEMENT
// ================================

function populateStateDropdown(states) {
    const select = document.getElementById('state');
    if (!select) {
        console.error('State dropdown element not found');
        return;
    }
    if (!states || !Array.isArray(states)) {
        console.error('Invalid states data:', states);
        return;
    }
    select.innerHTML = '<option value="">-- All States --</option>';
    states.filter(s => s).forEach(state => {
        const option = document.createElement('option');
        option.value = state;
        option.textContent = state;
        select.appendChild(option);
    });
}

function populateCityDropdown(cities) {
    const select = document.getElementById('city');
    if (!select) {
        console.error('City dropdown element not found');
        return;
    }
    if (!cities || !Array.isArray(cities)) {
        console.error('Invalid cities data:', cities);
        return;
    }
    select.innerHTML = '<option value="">-- All Cities --</option>';
    cities.filter(c => c).forEach(city => {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        select.appendChild(option);
    });
}

async function onStateChange() {
    const selectedState = document.getElementById('state').value;
    
    if (selectedState) {
        try {
            const response = await fetch(`/api/cities?state=${encodeURIComponent(selectedState)}`);
            const data = await response.json();
            
            if (data.success) {
                populateCityDropdown(data.cities);
                
                // Clear city if it's not in the filtered list
                const citySelect = document.getElementById('city');
                const currentCity = citySelect.value;
                if (currentCity && !data.cities.includes(currentCity)) {
                    citySelect.value = '';
                }
            }
        } catch (error) {
            console.error('Error loading cities:', error);
        }
    } else {
        // Reset to all cities
        populateCityDropdown(state.allCities);
    }
}

function onCityChange() {
    const city = document.getElementById('city').value;
    
    if (city && state.cityStateMapping[city]) {
        const stateValue = state.cityStateMapping[city];
        document.getElementById('state').value = stateValue;
    }
}

// Technician tab dropdown functions
function populateTechStateDropdown(states) {
    const select = document.getElementById('techState');
    if (!select) {
        console.warn('Tech state dropdown element not found');
        return;
    }
    if (!states || !Array.isArray(states)) {
        console.error('Invalid states data:', states);
        return;
    }
    select.innerHTML = '<option value="">-- All States --</option>';
    states.filter(s => s).forEach(state => {
        const option = document.createElement('option');
        option.value = state;
        option.textContent = state;
        select.appendChild(option);
    });
}

async function onTechStateChange() {
    const selectedState = document.getElementById('techState').value;
    const citySelect = document.getElementById('techCity');
    
    if (selectedState) {
        try {
            const response = await fetch(`/api/cities?state=${encodeURIComponent(selectedState)}`);
            const data = await response.json();
            
            if (data.success) {
                citySelect.innerHTML = '<option value="">-- All Cities --</option>';
                data.cities.filter(c => c).forEach(city => {
                    const option = document.createElement('option');
                    option.value = city;
                    option.textContent = city;
                    citySelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading cities:', error);
        }
    } else {
        citySelect.innerHTML = '<option value="">-- All Cities --</option>';
        state.allCities.filter(c => c).forEach(city => {
            const option = document.createElement('option');
            option.value = city;
            option.textContent = city;
            citySelect.appendChild(option);
        });
    }
}

function onTechCityChange() {
    const city = document.getElementById('techCity').value;
    
    if (city && state.cityStateMapping[city]) {
        const stateValue = state.cityStateMapping[city];
        document.getElementById('techState').value = stateValue;
    }
}

function clearTechFields() {
    document.getElementById('techIdTech').value = '';
    document.getElementById('techDispatchId').value = '';
    document.getElementById('techDate').value = '';
    document.getElementById('techStartDate').value = '';
    document.getElementById('techEndDate').value = '';
    document.getElementById('techState').value = '';
    document.getElementById('techCity').value = '';
    document.getElementById('techCity').innerHTML = '<option value="">-- All Cities --</option>';
    logMessage('🧹 Technician fields cleared', 'info');
}

// ================================
// DISPATCH CREATION FUNCTIONS
// ================================

function populateCreateStateDropdown(states) {
    const select = document.getElementById('createState');
    if (!select) {
        console.error('Create state dropdown element not found');
        return;
    }
    if (!states || !Array.isArray(states)) {
        console.error('Invalid states data:', states);
        return;
    }
    select.innerHTML = '<option value="">-- Select State --</option>';
    states.filter(s => s).forEach(state => {
        const option = document.createElement('option');
        option.value = state;
        option.textContent = state;
        select.appendChild(option);
    });
}

async function onCreateStateChange() {
    const selectedState = document.getElementById('createState').value;
    const citySelect = document.getElementById('createCity');
    
    // Clear city and address
    citySelect.value = '';
    document.getElementById('createAddress').value = '';
    document.getElementById('addressList').innerHTML = '';
    state.addressOptions = [];
    
    if (selectedState) {
        try {
            const response = await fetch(`/api/cities?state=${encodeURIComponent(selectedState)}`);
            const data = await response.json();
            
            if (data.success) {
                citySelect.innerHTML = '<option value="">-- Select City --</option>';
                data.cities.filter(c => c).forEach(city => {
                    const option = document.createElement('option');
                    option.value = city;
                    option.textContent = city;
                    citySelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading cities:', error);
            logMessage(`❌ Failed to load cities: ${error.message}`, 'error');
        }
    } else {
        citySelect.innerHTML = '<option value="">-- Select City --</option>';
    }
}

async function onCreateCityChange() {
    const city = document.getElementById('createCity').value;
    const state = document.getElementById('createState').value;
    
    // Clear address
    document.getElementById('createAddress').value = '';
    document.getElementById('addressList').innerHTML = '';
    state.addressOptions = [];
    
    if (city && state) {
        // Load addresses for this city/state
        try {
            const response = await fetch(`/api/locations/addresses?city=${encodeURIComponent(city)}&state=${encodeURIComponent(state)}`);
            const data = await response.json();
            
            if (data.success) {
                state.addressOptions = data.addresses;
                updateAddressList(data.addresses);
            }
        } catch (error) {
            console.error('Error loading addresses:', error);
        }
    }
}

function updateAddressList(addresses) {
    const datalist = document.getElementById('addressList');
    datalist.innerHTML = '';
    
    addresses.forEach(addr => {
        const option = document.createElement('option');
        option.value = addr.address;
        option.setAttribute('data-city', addr.city);
        option.setAttribute('data-state', addr.state);
        datalist.appendChild(option);
    });
}

// ================================
// CAPACITY MANAGEMENT FUNCTIONS
// ================================

function populateCapStateDropdown(states) {
    const select = document.getElementById('capState');
    if (!select) {
        console.warn('Capacity state dropdown element not found');
        return;
    }
    if (!states || !Array.isArray(states)) {
        console.error('Invalid states data:', states);
        return;
    }
    select.innerHTML = '<option value="">-- Select State --</option>';
    states.filter(s => s).forEach(state => {
        const option = document.createElement('option');
        option.value = state;
        option.textContent = state;
        select.appendChild(option);
    });
}

async function onCapStateChange() {
    const selectedState = document.getElementById('capState').value;
    const citySelect = document.getElementById('capCity');
    
    if (selectedState) {
        try {
            const response = await fetch(`/api/cities?state=${encodeURIComponent(selectedState)}`);
            const data = await response.json();
            
            if (data.success) {
                citySelect.innerHTML = '<option value="">-- All Cities --</option>';
                data.cities.filter(c => c).forEach(city => {
                    const option = document.createElement('option');
                    option.value = city;
                    option.textContent = city;
                    citySelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading cities:', error);
        }
    } else {
        citySelect.innerHTML = '<option value="">-- All Cities --</option>';
        state.allCities.filter(c => c).forEach(city => {
            const option = document.createElement('option');
            option.value = city;
            option.textContent = city;
            citySelect.appendChild(option);
        });
    }
}

async function checkCapacity() {
    if (!checkInitialized()) return;
    
    const stateValue = document.getElementById('capState').value;
    const city = document.getElementById('capCity').value;
    const date = document.getElementById('capDate').value;
    
    if (!stateValue) {
        alert('Please select a state');
        document.getElementById('capState').focus();
        return;
    }
    
    if (!date) {
        alert('Please enter a date');
        document.getElementById('capDate').focus();
        return;
    }
    
    try {
        showLoading(true);
        logMessage('🔍 Checking capacity...', 'header');
        
        const params = {
            date: date,
            state: stateValue || null,
            city: city || null
        };
        
        const response = await fetch('/api/capacity/city', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (data.overview) {
                // Overview mode - multiple city/state combinations
                logMessage('', '');
                logMessage(`📊 Capacity Overview (${data.count} locations):`, 'header');
                logMessage(`   Date: ${date}`);
                logMessage(`   Filter: ${stateValue ? `State: ${stateValue}` : 'All States'}`);
                
                // Calculate totals
                const totals = data.results.reduce((acc, cap) => {
                    acc.total_technicians += cap.total_technicians || 0;
                    acc.available_technicians += cap.available_technicians || 0;
                    acc.total_capacity_min += cap.total_capacity_min || 0;
                    acc.allocated_min += cap.allocated_min || 0;
                    acc.available_min += cap.available_min || 0;
                    return acc;
                }, {
                    total_technicians: 0,
                    available_technicians: 0,
                    total_capacity_min: 0,
                    allocated_min: 0,
                    available_min: 0
                });
                
                const total_utilization = totals.total_capacity_min > 0 
                    ? (totals.allocated_min / totals.total_capacity_min * 100).toFixed(1)
                    : 0;
                
                logMessage('', '');
                logMessage('📈 Summary Totals:', 'header');
                logMessage(`   Total Technicians: ${totals.total_technicians}`);
                logMessage(`   Available Technicians: ${totals.available_technicians}`);
                logMessage(`   Total Capacity: ${(totals.total_capacity_min / 60).toFixed(1)} hrs`);
                logMessage(`   Allocated: ${(totals.allocated_min / 60).toFixed(1)} hrs`);
                logMessage(`   Available: ${(totals.available_min / 60).toFixed(1)} hrs`);
                logMessage(`   Utilization: ${total_utilization}%`);
                
                // Display in user-friendly capacity modal
                showCapacityModal(data.results, true, date, stateValue);
            } else {
                // Single city/state mode
                const cap = data;
                logMessage('', '');
                logMessage('📊 Capacity Details:', 'header');
                logMessage(`   City: ${cap.city || 'All'}, State: ${cap.state || 'All'}`);
                logMessage(`   Date: ${cap.date}`);
                logMessage(`   Total Capacity: ${cap.total_capacity_hrs} hrs`);
                logMessage(`   Allocated: ${cap.allocated_hrs} hrs`);
                logMessage(`   Available: ${cap.available_hrs} hrs`);
                logMessage(`   Utilization: ${cap.utilization_pct}%`);
                
                if (cap.available_hrs > 0) {
                    logMessage(`   ✅ Capacity available`, 'success');
                } else {
                    logMessage(`   ⚠️ No capacity available`, 'warning');
                }
                
                // Display in user-friendly capacity modal
                showCapacityModal([cap], false, date, stateValue);
            }
        } else {
            logMessage(`❌ Error: ${data.error}`, 'error');
        }
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'error');
        console.error(error);
    } finally {
        showLoading(false);
    }
}

// ================================
// PENDING DISPATCHES FUNCTIONS
// ================================

async function refreshPending() {
    if (!checkInitialized()) return;
    
    try {
        showLoading(true);
        const response = await fetch('/api/dispatches/pending');
        const data = await response.json();
        
        if (data.success) {
            const pending = data.pending || [];
            const count = pending.length;
            
            // Update badge in tab and pending section
            updatePendingBadge(count);
            const badge = document.getElementById('pendingCount');
            if (badge) {
                if (count > 0) {
                    badge.textContent = count;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            }
            
            // Display pending list
            const listDiv = document.getElementById('pendingList');
            if (listDiv) {
                if (count === 0) {
                    listDiv.innerHTML = '<p class="text-muted">No pending dispatches</p>';
                } else {
                    let html = '<table class="pending-table" style="width: 100%; font-size: 12px;">';
                    html += '<thead><tr><th>ID</th><th>Address</th><th>City</th><th>State</th><th>Date</th><th>Time</th><th>Priority</th></tr></thead><tbody>';
                    pending.forEach(dispatch => {
                        html += `<tr>
                            <td>${dispatch.dispatch_id || 'N/A'}</td>
                            <td>${dispatch.address || 'N/A'}</td>
                            <td>${dispatch.city || 'N/A'}</td>
                            <td>${dispatch.state || 'N/A'}</td>
                            <td>${dispatch.date || 'N/A'}</td>
                            <td>${dispatch.time || 'N/A'}</td>
                            <td>${dispatch.priority || 'N/A'}</td>
                        </tr>`;
                    });
                    html += '</tbody></table>';
                    listDiv.innerHTML = html;
                }
            }
            
            logMessage(`✅ Refreshed pending dispatches: ${count} found`, 'success');
        } else {
            logMessage(`❌ Error: ${data.error}`, 'error');
        }
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'error');
        console.error(error);
    } finally {
        showLoading(false);
    }
}

async function commitPending() {
    if (!checkInitialized()) return;
    
    if (!confirm('Are you sure you want to commit all pending dispatches to the database?')) {
        return;
    }
    
    try {
        showLoading(true);
        logMessage('💾 Committing pending dispatches...', 'header');
        
        const response = await fetch('/api/dispatches/commit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        
        if (data.success) {
            logMessage(`✅ Successfully committed ${data.committed || 0} dispatches`, 'success');
            await refreshPending();
        } else {
            logMessage(`❌ Error: ${data.error}`, 'error');
        }
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'error');
        console.error(error);
    } finally {
        showLoading(false);
    }
}

async function clearPending() {
    if (!checkInitialized()) return;
    
    if (!confirm('Are you sure you want to clear all pending dispatches? This cannot be undone.')) {
        return;
    }
    
    try {
        showLoading(true);
        logMessage('🗑️ Clearing pending dispatches...', 'header');
        
        const response = await fetch('/api/dispatches/pending/clear', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        
        if (data.success) {
            logMessage('✅ All pending dispatches cleared', 'success');
            const badge = document.getElementById('pendingCount');
            if (badge) badge.style.display = 'none';
            const listDiv = document.getElementById('pendingList');
            if (listDiv) listDiv.innerHTML = '<p class="text-muted">No pending dispatches</p>';
        } else {
            logMessage(`❌ Error: ${data.error}`, 'error');
        }
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'error');
        console.error(error);
    } finally {
        showLoading(false);
    }
}

// ================================
// AUTO-ASSIGNMENT FUNCTIONS
// ================================

function populateAssignStateDropdown(states) {
    const select = document.getElementById('assignState');
    if (!select) {
        console.warn('Assign state dropdown element not found');
        return;
    }
    if (!states || !Array.isArray(states)) {
        console.error('Invalid states data:', states);
        return;
    }
    select.innerHTML = '<option value="">-- All States --</option>';
    states.filter(s => s).forEach(state => {
        const option = document.createElement('option');
        option.value = state;
        option.textContent = state;
        select.appendChild(option);
    });
}

async function onAssignStateChange() {
    const selectedState = document.getElementById('assignState').value;
    const citySelect = document.getElementById('assignCity');
    
    if (selectedState) {
        try {
            const response = await fetch(`/api/cities?state=${encodeURIComponent(selectedState)}`);
            const data = await response.json();
            
            if (data.success) {
                citySelect.innerHTML = '<option value="">-- All Cities --</option>';
                data.cities.filter(c => c).forEach(city => {
                    const option = document.createElement('option');
                    option.value = city;
                    option.textContent = city;
                    citySelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading cities:', error);
        }
    } else {
        citySelect.innerHTML = '<option value="">-- All Cities --</option>';
        state.allCities.filter(c => c).forEach(city => {
            const option = document.createElement('option');
            option.value = city;
            option.textContent = city;
            citySelect.appendChild(option);
        });
    }
}

async function runAutoAssign() {
    if (!checkInitialized()) return;
    
    const date = document.getElementById('assignDate').value;
    if (!date) {
        alert('Please enter a date');
        return;
    }
    
    const stateValue = document.getElementById('assignState').value;
    const city = document.getElementById('assignCity').value;
    const useScoring = document.getElementById('useScoring').checked;
    const rangeExpansion = document.getElementById('rangeExpansion').checked;
    
    try {
        showLoading(true);
        logMessage(`🤖 Running auto-assignment (dry run)...`, 'header');
        if (stateValue || city) {
            logMessage(`   Location filter: ${city || 'Any City'}, ${stateValue || 'Any State'}`, 'info');
        }
        
        const response = await fetch('/api/auto-assign', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                date: date,
                state: stateValue || null,
                city: city || null,
                dry_run: true, // Always dry run first
                use_scoring: useScoring,
                enable_range_expansion: rangeExpansion
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const results = data.results;
            const stats = data.statistics;
            
            // Store assignment data for commit
            state.autoAssignData = {
                date: date,
                state: stateValue || null,
                city: city || null,
                use_scoring: useScoring,
                enable_range_expansion: rangeExpansion,
                assignments: results.assignments || [],
                unassignable: results.unassignable || []
            };
            
            // Show results in specialized modal
            showAutoAssignModal(results, stats, date, stateValue, city);
        } else {
            logMessage(`❌ Error: ${data.error}`, 'error');
        }
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'error');
        console.error(error);
    } finally {
        showLoading(false);
    }
}

async function onAddressTyping() {
    const typed = document.getElementById('createAddress').value.toLowerCase();
    const city = document.getElementById('createCity').value;
    const stateValue = document.getElementById('createState').value;
    
    if (!typed) {
        document.getElementById('addressList').innerHTML = '';
        return;
    }
    
    // Filter addresses based on typed text
    let matching = [];
    
    if (city && stateValue && state.addressOptions.length > 0) {
        // Use already loaded addresses
        matching = state.addressOptions.filter(addr => 
            addr.address.toLowerCase().includes(typed)
        );
    } else {
        // Load all addresses and filter
        try {
            const response = await fetch(`/api/locations/addresses?city=${encodeURIComponent(city || '')}&state=${encodeURIComponent(stateValue || '')}`);
            const data = await response.json();
            
            if (data.success) {
                matching = data.addresses.filter(addr => 
                    addr.address.toLowerCase().includes(typed)
                ).slice(0, 50); // Limit to 50 suggestions
                state.addressOptions = matching;
            }
        } catch (error) {
            console.error('Error loading addresses:', error);
            return;
        }
    }
    
    updateAddressList(matching.slice(0, 50)); // Limit to 50 suggestions
}

async function loadSkillsAndPriorities() {
    try {
        // Load skills
        const skillsResponse = await fetch('/api/dispatches/valid-skills');
        const skillsData = await skillsResponse.json();
        
        if (skillsData.success) {
            state.validSkills = skillsData.skills;
            const skillSelect = document.getElementById('createSkill');
            skillSelect.innerHTML = '<option value="">-- Select Skill --</option>';
            skillsData.skills.forEach(skill => {
                const option = document.createElement('option');
                option.value = skill;
                option.textContent = skill;
                skillSelect.appendChild(option);
            });
        }
        
        // Load priorities
        const prioritiesResponse = await fetch('/api/dispatches/valid-priorities');
        const prioritiesData = await prioritiesResponse.json();
        
        if (prioritiesData.success) {
            state.validPriorities = prioritiesData.priorities;
            const prioritySelect = document.getElementById('createPriority');
            prioritySelect.innerHTML = '<option value="">-- Select Priority --</option>';
            prioritiesData.priorities.forEach(priority => {
                const option = document.createElement('option');
                option.value = priority;
                option.textContent = priority;
                prioritySelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading skills/priorities:', error);
        logMessage(`⚠️ Failed to load some options: ${error.message}`, 'warning');
    }
}

async function createDispatch() {
    if (!state.initialized) {
        logMessage('❌ Please wait for initialization to complete', 'error');
        return;
    }
    
    // Get form values
    const address = document.getElementById('createAddress').value.trim();
    const city = document.getElementById('createCity').value.trim();
    const stateValue = document.getElementById('createState').value.trim();
    const dateStr = document.getElementById('createDate').value;
    const timeStr = document.getElementById('createTime').value;
    const duration = parseInt(document.getElementById('createDuration').value);
    const skill = document.getElementById('createSkill').value.trim();
    const priority = document.getElementById('createPriority').value.trim();
    const reason = document.getElementById('createReason').value.trim() || 'N/A';
    const autoAssign = document.getElementById('createAutoAssign').checked;
    const commitToDb = document.getElementById('createCommit').checked;
    
    // Validation
    if (!address || !city || !stateValue || !dateStr || !timeStr || !duration || !skill || !priority) {
        logMessage('❌ Please fill all required fields', 'error');
        return;
    }
    
    // Combine date and time (HTML5 time input gives HH:MM format)
    const appointmentDatetime = `${dateStr}T${timeStr}:00`;
    
    try {
        showLoading(true);
        logMessage('Creating dispatch...', 'info');
        
        const response = await fetch('/api/dispatches/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                customer_address: address,
                city: city,
                state: stateValue,
                appointment_datetime: appointmentDatetime,
                duration_min: duration,
                required_skill: skill,
                priority: priority,
                dispatch_reason: reason,
                auto_assign: autoAssign,
                commit_to_db: commitToDb
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            logMessage(`✅ Dispatch created successfully! ID: ${data.dispatch.dispatch_id}`, 'success');
            if (data.assigned) {
                logMessage(`✅ Auto-assigned to technician`, 'success');
            }
            
            // Clear form
            document.getElementById('createAddress').value = '';
            document.getElementById('createCity').value = '';
            document.getElementById('createState').value = '';
            document.getElementById('createReason').value = '';
            
            // Reset to defaults
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            document.getElementById('createDate').value = tomorrow.toISOString().split('T')[0];
            document.getElementById('createTime').value = '10:00';
            document.getElementById('createDuration').value = '120';
        } else {
            logMessage(`❌ Failed to create dispatch: ${data.error}`, 'error');
        }
    } catch (error) {
        logMessage(`❌ Error creating dispatch: ${error.message}`, 'error');
        console.error(error);
    } finally {
        showLoading(false);
    }
}

async function checkCapacityForDispatch() {
    const city = document.getElementById('createCity').value.trim();
    const stateValue = document.getElementById('createState').value.trim();
    const dateStr = document.getElementById('createDate').value;
    const duration = parseInt(document.getElementById('createDuration').value);
    
    if (!city || !stateValue || !dateStr || !duration) {
        logMessage('❌ Please fill city, state, date, and duration', 'error');
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch('/api/capacity/check', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                city: city,
                state: stateValue,
                date: dateStr,
                duration_min: duration
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const cap = data.capacity;
            if (data.available) {
                logMessage(`✅ Capacity available: ${cap.available_hrs} hrs (${cap.utilization_pct}% utilized)`, 'success');
            } else {
                logMessage(`❌ Insufficient capacity: ${cap.allocated_hrs} hrs allocated, ${cap.total_capacity_hrs} hrs total`, 'error');
            }
        } else {
            logMessage(`❌ Capacity check failed: ${data.error}`, 'error');
        }
    } catch (error) {
        logMessage(`❌ Error checking capacity: ${error.message}`, 'error');
        console.error(error);
    } finally {
        showLoading(false);
    }
}

// ================================
// SECTION TOGGLE
// ================================

function toggleSection(sectionId) {
    const button = event.currentTarget;
    const content = document.getElementById(`${sectionId}-section`);
    
    button.classList.toggle('collapsed');
    content.classList.toggle('hidden');
}

// ================================
// API CALLS
// ================================

async function viewUnassigned() {
    if (!checkInitialized()) return;
    
    const date = document.getElementById('startDate').value || null;
    const city = document.getElementById('city').value || null;
    const stateValue = document.getElementById('state').value || null;
    
    const params = {
        date: date,
        city: city,
        state: stateValue,
        limit: 100
    };
    
    // Populate filters back to form after query
    if (date) {
        const createDateField = document.getElementById('createDate');
        if (createDateField && !createDateField.value) {
            createDateField.value = date;
        }
    }
    if (city) {
        const createCityField = document.getElementById('createCity');
        if (createCityField && !createCityField.value) {
            createCityField.value = city;
            onCreateCityChange();
        }
    }
    if (stateValue) {
        const createStateField = document.getElementById('createState');
        if (createStateField && !createStateField.value) {
            createStateField.value = stateValue;
            onCreateStateChange();
        }
    }
    
    await executeQuery('/api/unassigned', params, 'Unassigned Dispatches', 'dispatch');
}

async function checkAssignments() {
    if (!checkInitialized()) return;
    
    // Check both old and new field IDs for backward compatibility
    const techId = document.getElementById('techIdTech')?.value || document.getElementById('techId')?.value;
    if (!techId) {
        alert('Please enter a Technician ID');
        return;
    }
    
    const date = document.getElementById('techDate')?.value || document.getElementById('startDate')?.value || null;
    
    const params = {
        tech_id: techId,
        date: date
    };
    
    // Populate technician ID in form if not already set
    const techIdField = document.getElementById('techIdTech');
    if (techIdField && !techIdField.value) {
        techIdField.value = techId;
    }
    
    await executeOutputQuery('/api/technician/assignments', params, 'technician');
}

async function checkAvailability() {
    if (!checkInitialized()) return;
    
    // Check both old and new field IDs for backward compatibility
    const techId = document.getElementById('techIdTech')?.value || document.getElementById('techId')?.value;
    const city = document.getElementById('techCity')?.value || null;
    const stateValue = document.getElementById('techState')?.value || null;
    const date = document.getElementById('techDate')?.value || document.getElementById('startDate')?.value || null;
    
    // Must have either tech_id OR both city and state
    if (!techId && (!city || !stateValue)) {
        alert('Please enter either a Technician ID, or select both City and State');
        return;
    }
    
    const params = {
        date: date
    };
    
    // Add tech_id or city/state to params
    if (techId) {
        params.tech_id = techId;
    } else {
        params.city = city;
        params.state = stateValue;
    }
    
    try {
        showLoading(true);
        logMessage('🔍 Checking technician availability...', 'header');
        
        const response = await fetch('/api/technician/availability', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (data.single) {
                // Single technician result - show user-friendly display
                showAvailabilityModal([data.data], false, date);
            } else {
                // Multiple technicians result - show user-friendly display
                showAvailabilityModal(data.results, true, date, city, stateValue);
            }
        } else {
            logMessage(`❌ Error: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'error');
        console.error(error);
    } finally {
        showLoading(false);
    }
}

async function findDispatches() {
    if (!checkInitialized()) return;
    
    // Check both old and new field IDs for backward compatibility
    const techId = document.getElementById('techIdTech')?.value || document.getElementById('techId')?.value;
    const date = document.getElementById('techDate')?.value || document.getElementById('startDate')?.value;
    
    if (!techId || !date) {
        alert('Please enter both Technician ID and Date');
        return;
    }
    
    // Populate technician ID in technician tab if not already set
    const techIdField = document.getElementById('techIdTech');
    if (techIdField && !techIdField.value) {
        techIdField.value = techId;
    }
    if (date) {
        const techDateField = document.getElementById('techDate');
        if (techDateField && !techDateField.value) {
            techDateField.value = date;
        }
    }
    
    const params = {tech_id: techId, date: date};
    await executeQuery('/api/dispatches/available', params, 'Available Dispatches', 'dispatch');
}

async function findTechnicians() {
    if (!checkInitialized()) return;
    
    // Check both old and new field IDs for backward compatibility
    const dispatchId = document.getElementById('techDispatchId')?.value || document.getElementById('dispatchId')?.value;
    if (!dispatchId) {
        alert('Please enter a Dispatch ID');
        return;
    }
    
    // Populate dispatch ID in both tabs
    const techDispatchIdField = document.getElementById('techDispatchId');
    if (techDispatchIdField && !techDispatchIdField.value) {
        techDispatchIdField.value = dispatchId;
    }
    const dispatchIdField = document.getElementById('dispatchId');
    if (dispatchIdField && !dispatchIdField.value) {
        dispatchIdField.value = dispatchId;
    }
    
    const params = {dispatch_id: parseInt(dispatchId)};
    await executeQuery('/api/technicians/available', params, 'Available Technicians', 'technician');
}

async function listAvailable() {
    if (!checkInitialized()) return;
    
    // Check both old and new field IDs for backward compatibility
    const date = document.getElementById('techDate')?.value || document.getElementById('startDate')?.value;
    if (!date) {
        alert('Please enter a Date');
        return;
    }
    
    const city = document.getElementById('techCity')?.value || document.getElementById('city')?.value || null;
    const stateValue = document.getElementById('techState')?.value || document.getElementById('state')?.value || null;
    
    // Populate fields in technician tab
    const techDateField = document.getElementById('techDate');
    if (techDateField && !techDateField.value) {
        techDateField.value = date;
    }
    if (city) {
        const techCityField = document.getElementById('techCity');
        if (techCityField && !techCityField.value) {
            techCityField.value = city;
            onTechCityChange();
        }
    }
    if (stateValue) {
        const techStateField = document.getElementById('techState');
        if (techStateField && !techStateField.value) {
            techStateField.value = stateValue;
            onTechStateChange();
        }
    }
    
    const params = {
        date: date,
        city: city,
        state: stateValue
    };
    
    await executeQuery('/api/technicians/list', params, 'Available Technicians', 'technician');
}

async function availabilitySummary() {
    if (!checkInitialized()) return;
    
    // Check both old and new field IDs for backward compatibility
    const startDate = document.getElementById('techStartDate')?.value || document.getElementById('startDate')?.value;
    const endDate = document.getElementById('techEndDate')?.value || document.getElementById('endDate')?.value;
    
    if (!startDate || !endDate) {
        alert('Please enter both Start Date and End Date');
        return;
    }
    
    const city = document.getElementById('techCity')?.value || document.getElementById('city')?.value || null;
    const stateValue = document.getElementById('techState')?.value || document.getElementById('state')?.value || null;
    
    // Populate fields in technician tab
    const techStartDateField = document.getElementById('techStartDate');
    if (techStartDateField && !techStartDateField.value) {
        techStartDateField.value = startDate;
    }
    const techEndDateField = document.getElementById('techEndDate');
    if (techEndDateField && !techEndDateField.value) {
        techEndDateField.value = endDate;
    }
    if (city) {
        const techCityField = document.getElementById('techCity');
        if (techCityField && !techCityField.value) {
            techCityField.value = city;
            onTechCityChange();
        }
    }
    if (stateValue) {
        const techStateField = document.getElementById('techState');
        if (techStateField && !techStateField.value) {
            techStateField.value = stateValue;
            onTechStateChange();
        }
    }
    
    const params = {
        start_date: startDate,
        end_date: endDate,
        city: city,
        state: stateValue
    };
    
    await executeQuery('/api/availability/summary', params, 'Availability Summary', 'technician');
}

async function autoAssign() {
    if (!checkInitialized()) return;
    
    const date = document.getElementById('startDate').value;
    if (!date) {
        alert('Please enter a Date');
        return;
    }
    
    try {
        showLoading(true);
        logMessage('🤖 Running auto-assignment (dry run)...', 'header');
        
        const response = await fetch('/api/auto-assign', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({date: date, dry_run: true})
        });
        
        const data = await response.json();
        
        if (data.success) {
            const results = data.results;
            logMessage('', '');
            logMessage('📊 Assignment Summary:', 'header');
            logMessage(`   Total: ${results.total}`);
            logMessage(`   ✅ Assigned: ${results.assigned}`, 'success');
            logMessage(`   ⚠️ Unassignable: ${results.unassignable}`, 'warning');
        } else {
            logMessage(`❌ Error: ${data.error}`, 'error');
        }
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'error');
        console.error(error);
    } finally {
        showLoading(false);
    }
}

// ================================
// QUERY EXECUTION
// ================================

async function executeQuery(endpoint, params, title, queryContext = null) {
    try {
        showLoading(true);
        logMessage(`📊 Fetching ${title}...`, 'header');
        
        // Set query context for form population
        state.currentQueryContext = queryContext;
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        
        const data = await response.json();
        
        if (data.success) {
            state.currentData = data.data;
            state.currentColumns = data.columns;
            state.editedRows.clear();
            
            // Show results in modal instead of data grid
            showResultsModal(title, data.data, data.columns);
            logMessage(`✅ Loaded ${data.count} rows`, 'success');
            if (queryContext) {
                logMessage(`💡 Click on any row in the modal to populate the ${queryContext} form`, 'info');
            }
        } else {
            logMessage(`❌ Error: ${data.error}`, 'error');
            if (data.traceback) {
                console.error(data.traceback);
            }
        }
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'error');
        console.error(error);
    } finally {
        showLoading(false);
    }
}

async function executeOutputQuery(endpoint, params, queryContext = null) {
    try {
        showLoading(true);
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Check if we have structured data to display in modal
            if (data.data && Array.isArray(data.data) && data.data.length > 0) {
                // Convert to grid format
                const columns = Object.keys(data.data[0]);
                state.currentData = data.data;
                state.currentColumns = columns;
                state.currentQueryContext = queryContext;
                state.editedRows.clear();
                
                showResultsModal('Query Results', data.data, columns);
                logMessage(`✅ Loaded ${data.data.length} rows`, 'success');
                if (queryContext) {
                    logMessage(`💡 Click on any row in the modal to populate the ${queryContext} form`, 'info');
                }
            } else if (data.output) {
                // Display output in messages (legacy text output)
                const lines = data.output.split('\n');
                lines.forEach(line => {
                    if (line.trim()) {
                        logMessage(line);
                    }
                });
            } else if (data.data && typeof data.data === 'object' && !Array.isArray(data.data)) {
                // Single object result - convert to array for display
                const columns = Object.keys(data.data);
                state.currentData = [data.data];
                state.currentColumns = columns;
                state.currentQueryContext = queryContext;
                state.editedRows.clear();
                
                showResultsModal('Query Results', [data.data], columns);
                logMessage(`✅ Loaded result`, 'success');
                if (queryContext) {
                    logMessage(`💡 Click on the row in the modal to populate the ${queryContext} form`, 'info');
                }
            }
            
            // Populate forms based on query context
            if (queryContext === 'technician' && params.tech_id) {
                const techIdField = document.getElementById('techIdTech');
                if (techIdField) {
                    techIdField.value = params.tech_id;
                }
                if (params.date) {
                    const techDateField = document.getElementById('techDate');
                    if (techDateField) {
                        techDateField.value = params.date;
                    }
                }
            }
        } else {
            logMessage(`❌ Error: ${data.error}`, 'error');
        }
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'error');
        console.error(error);
    } finally {
        showLoading(false);
    }
}

// ================================
// DATA GRID RENDERING (REMOVED - Using Modal Instead)
// ================================
// All query results now display in the resultsModal
// See showResultsModal() function below

// Fields that should not be editable
const NON_EDITABLE_FIELDS = ['technician_name', 'num_assignments', 'technician_id', 'utilization_pct', 'Technician_name', 'Num_assignments', 'Technician_id', 'Utilization_pct'];

// Show capacity details in a user-friendly format
function showCapacityModal(data, isOverview, date, stateFilter) {
    const modal = document.getElementById('resultsModal');
    const modalTitle = document.getElementById('resultsModalTitle');
    const modalContent = document.getElementById('resultsModalContent');
    const exportBtn = document.getElementById('exportResultsBtn');
    
    modalTitle.textContent = isOverview ? `Capacity Overview - ${date}` : 'Capacity Details';
    
    if (!data || data.length === 0) {
        modalContent.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>No capacity data available</p>
                <p class="text-muted">No technicians found for the selected location and date</p>
            </div>
        `;
        exportBtn.style.display = 'none';
    } else {
        let html = '';
        
        if (isOverview) {
            // Overview mode - show summary cards
            const totals = data.reduce((acc, cap) => {
                acc.total_technicians += cap.total_technicians || 0;
                acc.available_technicians += cap.available_technicians || 0;
                acc.total_capacity_min += cap.total_capacity_min || 0;
                acc.allocated_min += cap.allocated_min || 0;
                acc.available_min += cap.available_min || 0;
                return acc;
            }, {
                total_technicians: 0,
                available_technicians: 0,
                total_capacity_min: 0,
                allocated_min: 0,
                available_min: 0
            });
            
            const total_utilization = totals.total_capacity_min > 0 
                ? (totals.allocated_min / totals.total_capacity_min * 100)
                : 0;
            
            const statusClass = total_utilization >= 100 ? 'status-critical' : 
                              total_utilization >= 90 ? 'status-warning' : 'status-good';
            const statusIcon = total_utilization >= 100 ? '⚠️' : 
                              total_utilization >= 90 ? '⚡' : '✅';
            const statusText = total_utilization >= 100 ? 'Over Capacity' : 
                             total_utilization >= 90 ? 'High Utilization' : 'Good Capacity';
            
            html += `
                <div class="capacity-summary">
                    <div class="capacity-header">
                        <h4><i class="fas fa-map-marked-alt"></i> Overview Summary</h4>
                        <div class="capacity-status ${statusClass}">
                            <span class="status-icon">${statusIcon}</span>
                            <span class="status-text">${statusText}</span>
                        </div>
                    </div>
                    <div class="capacity-stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Total Locations</div>
                            <div class="stat-value">${data.length}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Total Technicians</div>
                            <div class="stat-value">${totals.total_technicians.toLocaleString()}</div>
                            <div class="stat-sub">${totals.available_technicians.toLocaleString()} available</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Total Capacity</div>
                            <div class="stat-value">${(totals.total_capacity_min / 60).toFixed(1)} hrs</div>
                            <div class="stat-sub">${(totals.total_capacity_min).toLocaleString()} minutes</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Allocated</div>
                            <div class="stat-value">${(totals.allocated_min / 60).toFixed(1)} hrs</div>
                            <div class="stat-sub">${(totals.allocated_min).toLocaleString()} minutes</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Available</div>
                            <div class="stat-value ${totals.available_min < 0 ? 'text-danger' : ''}">${(totals.available_min / 60).toFixed(1)} hrs</div>
                            <div class="stat-sub">${(totals.available_min).toLocaleString()} minutes</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Utilization</div>
                            <div class="stat-value">${total_utilization.toFixed(1)}%</div>
                            <div class="progress-bar-container">
                                <div class="progress-bar" style="width: ${Math.min(total_utilization, 100)}%; background-color: ${total_utilization >= 100 ? '#dc3545' : total_utilization >= 90 ? '#ffc107' : '#28a745'};"></div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Location details table
            html += `
                <div class="capacity-details-section">
                    <h4><i class="fas fa-list"></i> Location Details</h4>
                    <div class="capacity-table-container">
                        <table class="capacity-table">
                            <thead>
                                <tr>
                                    <th>Location</th>
                                    <th>Technicians</th>
                                    <th>Total Capacity</th>
                                    <th>Allocated</th>
                                    <th>Available</th>
                                    <th>Utilization</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            data.forEach(cap => {
                const util = cap.utilization_pct || 0;
                const statusClass = cap.over_capacity ? 'status-critical' : 
                                  util >= 90 ? 'status-warning' : 'status-good';
                const statusIcon = cap.over_capacity ? '🔴' : 
                                 util >= 90 ? '🟡' : '🟢';
                const statusText = cap.over_capacity ? 'Over Capacity' : 
                                 util >= 90 ? 'High' : 'Good';
                
                html += `
                    <tr>
                        <td><strong>${escapeHtml(cap.city || 'All')}, ${escapeHtml(cap.state || 'All')}</strong></td>
                        <td>${cap.available_technicians || 0} / ${cap.total_technicians || 0}</td>
                        <td>${(cap.total_capacity_hrs || 0).toFixed(1)} hrs</td>
                        <td>${(cap.allocated_hrs || 0).toFixed(1)} hrs</td>
                        <td class="${(cap.available_hrs || 0) < 0 ? 'text-danger' : ''}">${(cap.available_hrs || 0).toFixed(1)} hrs</td>
                        <td>
                            <div class="utilization-cell">
                                <span>${util.toFixed(1)}%</span>
                                <div class="progress-bar-container small">
                                    <div class="progress-bar" style="width: ${Math.min(util, 100)}%; background-color: ${cap.over_capacity ? '#dc3545' : util >= 90 ? '#ffc107' : '#28a745'};"></div>
                                </div>
                            </div>
                        </td>
                        <td class="${statusClass}">
                            <span class="status-badge">${statusIcon} ${statusText}</span>
                        </td>
                    </tr>
                `;
            });
            
            html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } else {
            // Single location mode - show detailed card
            const cap = data[0];
            const util = cap.utilization_pct || 0;
            const statusClass = cap.over_capacity ? 'status-critical' : 
                              util >= 90 ? 'status-warning' : 'status-good';
            const statusIcon = cap.over_capacity ? '🔴' : 
                             util >= 90 ? '⚡' : '✅';
            const statusText = cap.over_capacity ? 'Over Capacity' : 
                             util >= 90 ? 'High Utilization' : 'Good Capacity';
            
            html += `
                <div class="capacity-detail-card">
                    <div class="capacity-header">
                        <h4><i class="fas fa-map-marker-alt"></i> ${escapeHtml(cap.city || 'All')}, ${escapeHtml(cap.state || 'All')}</h4>
                        <div class="capacity-status ${statusClass}">
                            <span class="status-icon">${statusIcon}</span>
                            <span class="status-text">${statusText}</span>
                        </div>
                    </div>
                    
                    <div class="capacity-info">
                        <div class="info-row">
                            <span class="info-label"><i class="fas fa-calendar"></i> Date:</span>
                            <span class="info-value">${escapeHtml(cap.date || date)}</span>
                        </div>
                    </div>
                    
                    <div class="capacity-stats-grid">
                        <div class="stat-card">
                            <div class="stat-label"><i class="fas fa-users"></i> Technicians</div>
                            <div class="stat-value">${cap.total_technicians || 0}</div>
                            <div class="stat-sub">${cap.available_technicians || 0} available</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label"><i class="fas fa-clock"></i> Total Capacity</div>
                            <div class="stat-value">${(cap.total_capacity_hrs || 0).toFixed(1)} hrs</div>
                            <div class="stat-sub">${(cap.total_capacity_min || 0).toLocaleString()} minutes</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label"><i class="fas fa-tasks"></i> Allocated</div>
                            <div class="stat-value">${(cap.allocated_hrs || 0).toFixed(1)} hrs</div>
                            <div class="stat-sub">${(cap.allocated_min || 0).toLocaleString()} minutes</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label"><i class="fas fa-check-circle"></i> Available</div>
                            <div class="stat-value ${(cap.available_hrs || 0) < 0 ? 'text-danger' : ''}">${(cap.available_hrs || 0).toFixed(1)} hrs</div>
                            <div class="stat-sub">${(cap.available_min || 0).toLocaleString()} minutes</div>
                        </div>
                        <div class="stat-card stat-card-wide">
                            <div class="stat-label"><i class="fas fa-percentage"></i> Utilization</div>
                            <div class="stat-value">${util.toFixed(1)}%</div>
                            <div class="progress-bar-container">
                                <div class="progress-bar" style="width: ${Math.min(util, 100)}%; background-color: ${cap.over_capacity ? '#dc3545' : util >= 90 ? '#ffc107' : '#28a745'};"></div>
                            </div>
                            <div class="stat-sub">${cap.over_capacity ? '⚠️ Exceeds capacity' : util >= 90 ? '⚡ High utilization' : '✅ Healthy capacity'}</div>
                        </div>
                    </div>
                    
                    ${cap.over_capacity ? `
                        <div class="capacity-alert alert-danger">
                            <i class="fas fa-exclamation-triangle"></i>
                            <strong>Warning:</strong> This location is over capacity. 
                            ${Math.abs(cap.available_hrs || 0).toFixed(1)} hours over the available capacity.
                        </div>
                    ` : ''}
                    
                    ${util >= 90 && !cap.over_capacity ? `
                        <div class="capacity-alert alert-warning">
                            <i class="fas fa-exclamation-circle"></i>
                            <strong>Notice:</strong> This location is at ${util.toFixed(1)}% capacity. 
                            Consider adding more technicians or reducing allocations.
                        </div>
                    ` : ''}
                </div>
            `;
        }
        
        modalContent.innerHTML = html;
        exportBtn.style.display = 'inline-block';
        
        // Store data for export
        state.currentData = data;
        state.currentColumns = isOverview ? ['city', 'state', 'date', 'total_technicians', 
            'available_technicians', 'total_capacity_hrs', 'allocated_hrs', 
            'available_hrs', 'utilization_pct', 'over_capacity'] : Object.keys(data[0]);
    }
    
    modal.classList.add('active');
}

// Show availability details in a user-friendly format
function showAvailabilityModal(data, isMultiple, date, city, state) {
    const modal = document.getElementById('resultsModal');
    const modalTitle = document.getElementById('resultsModalTitle');
    const modalContent = document.getElementById('resultsModalContent');
    const exportBtn = document.getElementById('exportResultsBtn');
    
    modalTitle.textContent = isMultiple ? `Technician Availability - ${city}, ${state}` : 'Technician Availability';
    
    if (!data || data.length === 0) {
        modalContent.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>No availability data available</p>
                <p class="text-muted">No technicians found for the selected criteria</p>
            </div>
        `;
        exportBtn.style.display = 'none';
    } else {
        let html = '';
        
        // Format time helper - removes date, keeps only time
        const formatTime = (timeStr) => {
            if (!timeStr) return 'N/A';
            
            let timeOnly = String(timeStr).trim();
            
            // If it's a timestamp with 'T' separator (ISO format: 2025-01-15T14:30:00)
            if (timeOnly.includes('T')) {
                timeOnly = timeOnly.split('T')[1] || timeOnly;
            }
            
            // Remove date part if present (YYYY-MM-DD HH:MM:SS format)
            if (timeOnly.match(/^\d{4}-\d{2}-\d{2}/)) {
                const parts = timeOnly.split(' ');
                timeOnly = parts.length > 1 ? parts[1] : timeOnly;
            }
            
            // Remove milliseconds (everything after decimal point)
            if (timeOnly.includes('.')) {
                timeOnly = timeOnly.split('.')[0];
            }
            
            // Remove timezone info (handle +HH:MM, -HH:MM, or Z)
            // Match pattern like +05:00 or -05:00 at the end
            timeOnly = timeOnly.replace(/[+-]\d{2}:\d{2}$/, ''); // Remove +05:00 or -05:00
            timeOnly = timeOnly.replace(/Z$/, ''); // Remove trailing Z
            
            // Extract just HH:MM:SS or HH:MM (first 8 or 5 characters if it matches time pattern)
            if (timeOnly.match(/^\d{2}:\d{2}:\d{2}/)) {
                return timeOnly.substring(0, 8); // HH:MM:SS
            }
            if (timeOnly.match(/^\d{2}:\d{2}/)) {
                return timeOnly.substring(0, 5); // HH:MM
            }
            
            return timeOnly || 'N/A';
        };
        
        // Format minutes to hours/minutes
        const formatMinutes = (minutes) => {
            if (!minutes && minutes !== 0) return '0 min';
            const hrs = Math.floor(minutes / 60);
            const mins = minutes % 60;
            if (hrs > 0 && mins > 0) return `${hrs} hr ${mins} min`;
            if (hrs > 0) return `${hrs} hr`;
            return `${mins} min`;
        };
        
        if (isMultiple) {
            // Multiple technicians - show summary and list
            const availableCount = data.filter(r => r.available).length;
            const unavailableCount = data.length - availableCount;
            const totalAvailableMinutes = data.filter(r => r.available).reduce((sum, r) => sum + (r.available_minutes || 0), 0);
            const totalAssignedMinutes = data.filter(r => r.available).reduce((sum, r) => sum + (r.assigned_minutes || 0), 0);
            const totalRemainingMinutes = totalAvailableMinutes - totalAssignedMinutes;
            const avgUtilization = availableCount > 0 
                ? data.filter(r => r.available).reduce((sum, r) => sum + (r.utilization_pct || 0), 0) / availableCount
                : 0;
            
            html += `
                <div class="availability-summary">
                    <div class="capacity-header">
                        <h4><i class="fas fa-users"></i> Availability Summary</h4>
                        <div class="capacity-status ${availableCount > 0 ? 'status-good' : 'status-critical'}">
                            <span class="status-icon">${availableCount > 0 ? '✅' : '❌'}</span>
                            <span class="status-text">${availableCount} Available</span>
                        </div>
                    </div>
                    <div class="capacity-info">
                        <div class="info-row">
                            <span class="info-label"><i class="fas fa-calendar"></i> Date:</span>
                            <span class="info-value">${date || 'All Days'}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label"><i class="fas fa-map-marker-alt"></i> Location:</span>
                            <span class="info-value">${city || 'All'}, ${state || 'All'}</span>
                        </div>
                    </div>
                    <div class="capacity-stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Total Technicians</div>
                            <div class="stat-value">${data.length}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Available</div>
                            <div class="stat-value" style="color: #28a745;">${availableCount}</div>
                            <div class="stat-sub">${unavailableCount} unavailable</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Total Capacity</div>
                            <div class="stat-value">${formatMinutes(totalAvailableMinutes)}</div>
                            <div class="stat-sub">${totalAvailableMinutes.toLocaleString()} minutes</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Assigned</div>
                            <div class="stat-value">${formatMinutes(totalAssignedMinutes)}</div>
                            <div class="stat-sub">${totalAssignedMinutes.toLocaleString()} minutes</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Remaining</div>
                            <div class="stat-value ${totalRemainingMinutes < 0 ? 'text-danger' : ''}">${formatMinutes(totalRemainingMinutes)}</div>
                            <div class="stat-sub">${totalRemainingMinutes.toLocaleString()} minutes</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Avg Utilization</div>
                            <div class="stat-value">${avgUtilization.toFixed(1)}%</div>
                            <div class="progress-bar-container">
                                <div class="progress-bar" style="width: ${Math.min(avgUtilization, 100)}%; background-color: ${avgUtilization >= 100 ? '#dc3545' : avgUtilization >= 90 ? '#ffc107' : '#28a745'};"></div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Technician details table
            html += `
                <div class="capacity-details-section">
                    <h4><i class="fas fa-list"></i> Technician Details</h4>
                    <div class="capacity-table-container">
                        <table class="capacity-table">
                            <thead>
                                <tr>
                                    <th>Technician</th>
                                    <th>Location</th>
                                    <th>Status</th>
                                    <th>Time Window</th>
                                    <th>Available</th>
                                    <th>Assigned</th>
                                    <th>Remaining</th>
                                    <th>Utilization</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            data.forEach(tech => {
                const util = tech.utilization_pct || 0;
                const statusClass = tech.available ? 'status-good' : 'status-critical';
                const statusIcon = tech.available ? '🟢' : '🔴';
                const statusText = tech.available ? 'Available' : (tech.reason || 'Unavailable');
                
                html += `
                    <tr>
                        <td>
                            <strong>${escapeHtml(tech.name || tech.tech_id || 'N/A')}</strong><br>
                            <small style="color: #666;">${escapeHtml(tech.tech_id || '')}</small>
                            ${tech.primary_skill ? `<br><small style="color: #888;"><i class="fas fa-tools"></i> ${escapeHtml(tech.primary_skill)}</small>` : ''}
                        </td>
                        <td>${escapeHtml(tech.city || '')}, ${escapeHtml(tech.state || '')}</td>
                        <td class="${statusClass}">
                            <span class="status-badge">${statusIcon} ${statusText}</span>
                        </td>
                        <td>
                            ${tech.available ? `
                                <div>${formatTime(tech.start_time)} - ${formatTime(tech.end_time)}</div>
                            ` : `<span style="color: #999;">-</span>`}
                        </td>
                        <td>${tech.available ? formatMinutes(tech.available_minutes || 0) : '-'}</td>
                        <td>${tech.available ? formatMinutes(tech.assigned_minutes || 0) : '-'}</td>
                        <td class="${(tech.remaining_minutes || 0) < 0 ? 'text-danger' : ''}">${tech.available ? formatMinutes(tech.remaining_minutes || 0) : '-'}</td>
                        <td>
                            ${tech.available ? `
                                <div class="utilization-cell">
                                    <span>${util.toFixed(1)}%</span>
                                    <div class="progress-bar-container small">
                                        <div class="progress-bar" style="width: ${Math.min(util, 100)}%; background-color: ${util >= 100 ? '#dc3545' : util >= 90 ? '#ffc107' : '#28a745'};"></div>
                                    </div>
                                </div>
                            ` : '-'}
                        </td>
                    </tr>
                `;
            });
            
            html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } else {
            // Single technician - show detailed card
            const tech = data[0];
            const util = tech.utilization_pct || 0;
            const statusClass = tech.available ? 'status-good' : 'status-critical';
            const statusIcon = tech.available ? '✅' : '❌';
            const statusText = tech.available ? 'Available' : (tech.reason || 'Unavailable');
            
            html += `
                <div class="capacity-detail-card">
                    <div class="capacity-header">
                        <h4><i class="fas fa-user"></i> ${escapeHtml(tech.name || tech.tech_id || 'Technician')}</h4>
                        <div class="capacity-status ${statusClass}">
                            <span class="status-icon">${statusIcon}</span>
                            <span class="status-text">${statusText}</span>
                        </div>
                    </div>
                    
                    <div class="capacity-info">
                        <div class="info-row">
                            <span class="info-label"><i class="fas fa-id-badge"></i> Technician ID:</span>
                            <span class="info-value">${escapeHtml(tech.tech_id || 'N/A')}</span>
                        </div>
                        ${tech.city || tech.state ? `
                        <div class="info-row">
                            <span class="info-label"><i class="fas fa-map-marker-alt"></i> Location:</span>
                            <span class="info-value">${escapeHtml(tech.city || '')}, ${escapeHtml(tech.state || '')}</span>
                        </div>
                        ` : ''}
                        ${tech.primary_skill ? `
                        <div class="info-row">
                            <span class="info-label"><i class="fas fa-tools"></i> Primary Skill:</span>
                            <span class="info-value">${escapeHtml(tech.primary_skill)}</span>
                        </div>
                        ` : ''}
                        <div class="info-row">
                            <span class="info-label"><i class="fas fa-calendar"></i> Date:</span>
                            <span class="info-value">${date || 'All Days'}</span>
                        </div>
                    </div>
            `;
            
            if (tech.available) {
                html += `
                    <div class="capacity-stats-grid">
                        <div class="stat-card">
                            <div class="stat-label"><i class="fas fa-clock"></i> Start Time</div>
                            <div class="stat-value" style="font-size: 1.4rem;">${formatTime(tech.start_time)}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label"><i class="fas fa-clock"></i> End Time</div>
                            <div class="stat-value" style="font-size: 1.4rem;">${formatTime(tech.end_time)}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label"><i class="fas fa-check-circle"></i> Available Capacity</div>
                            <div class="stat-value">${formatMinutes(tech.available_minutes || 0)}</div>
                            <div class="stat-sub">${(tech.available_minutes || 0).toLocaleString()} minutes</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label"><i class="fas fa-tasks"></i> Assigned</div>
                            <div class="stat-value">${formatMinutes(tech.assigned_minutes || 0)}</div>
                            <div class="stat-sub">${(tech.assigned_minutes || 0).toLocaleString()} minutes</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label"><i class="fas fa-hourglass-half"></i> Remaining</div>
                            <div class="stat-value ${(tech.remaining_minutes || 0) < 0 ? 'text-danger' : ''}">${formatMinutes(tech.remaining_minutes || 0)}</div>
                            <div class="stat-sub">${(tech.remaining_minutes || 0).toLocaleString()} minutes</div>
                        </div>
                        <div class="stat-card stat-card-wide">
                            <div class="stat-label"><i class="fas fa-percentage"></i> Utilization</div>
                            <div class="stat-value">${util.toFixed(1)}%</div>
                            <div class="progress-bar-container">
                                <div class="progress-bar" style="width: ${Math.min(util, 100)}%; background-color: ${util >= 100 ? '#dc3545' : util >= 90 ? '#ffc107' : '#28a745'};"></div>
                            </div>
                            <div class="stat-sub">${util >= 100 ? '⚠️ Over capacity' : util >= 90 ? '⚡ High utilization' : '✅ Healthy capacity'}</div>
                        </div>
                    </div>
                `;
            } else {
                html += `
                    <div class="capacity-alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i>
                        <strong>Not Available</strong>
                        <div style="margin-top: 8px;">${escapeHtml(tech.reason || 'No reason specified')}</div>
                    </div>
                `;
            }
            
            html += `</div>`;
        }
        
        modalContent.innerHTML = html;
        exportBtn.style.display = 'inline-block';
        
        // Store data for export
        state.currentData = data;
        state.currentColumns = isMultiple ? ['tech_id', 'name', 'city', 'state', 'available', 'start_time', 'end_time', 
            'available_minutes', 'assigned_minutes', 'remaining_minutes', 'utilization_pct', 'reason', 'primary_skill'] : Object.keys(data[0]);
    }
    
    modal.classList.add('active');
}

function showResultsModal(title, data, columns) {
    const modal = document.getElementById('resultsModal');
    const modalTitle = document.getElementById('resultsModalTitle');
    const modalContent = document.getElementById('resultsModalContent');
    const exportBtn = document.getElementById('exportResultsBtn');
    
    const rowCount = data ? data.length : 0;
    modalTitle.textContent = `${title}${rowCount > 0 ? ` (${rowCount} ${rowCount === 1 ? 'row' : 'rows'})` : ''}`;
    
    if (!data || data.length === 0) {
        modalContent.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox" style="font-size: 3rem; color: var(--color-text-muted); margin-bottom: 1rem;"></i>
                <h4 style="margin: 0 0 0.5rem 0; color: var(--color-text);">No data to display</h4>
                <p class="text-muted" style="margin: 0;">The query returned no results. Try adjusting your filters.</p>
            </div>
        `;
        exportBtn.style.display = 'none';
    } else {
        // Add search/filter functionality
        let html = `
            <div class="modal-toolbar" style="margin-bottom: 1rem; display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 200px;">
                    <input type="text" id="modalSearchInput" class="form-control" placeholder="🔍 Search results..." 
                           style="width: 100%; padding: 0.5rem; border: 1px solid var(--color-border); border-radius: 4px;"
                           onkeyup="filterModalTable(this.value)">
                </div>
                <div style="color: var(--color-text-muted); font-size: 0.9rem;">
                    <i class="fas fa-info-circle"></i> ${rowCount} ${rowCount === 1 ? 'result' : 'results'}
                    ${state.currentQueryContext ? ' • Click row to populate form' : ''}
                </div>
            </div>
        `;
        
        html += '<div class="modal-table-container" style="max-height: 60vh; overflow-y: auto; border: 1px solid var(--color-border); border-radius: 4px;">';
        html += '<table class="data-table modal-table" id="modalResultsTable"><thead><tr>';
        
        // Header row
        html += '<th style="width: 50px;">#</th>';
        columns.forEach(col => {
            html += `<th>${escapeHtml(col)}</th>`;
        });
        if (state.currentQueryContext) {
            html += '<th style="width: 100px;">Action</th>';
        }
        html += '</tr></thead><tbody>';
        
        // Data rows
        data.forEach((row, rowIndex) => {
            html += `<tr class="modal-row ${state.currentQueryContext ? 'clickable-row' : ''}" 
                          data-row-index="${rowIndex}"
                          ${state.currentQueryContext ? `onclick="populateFormFromRow(${rowIndex})"` : ''}
                          style="cursor: ${state.currentQueryContext ? 'pointer' : 'default'};">`;
            html += `<td style="font-weight: 600; color: var(--color-text-muted);">${rowIndex + 1}</td>`;
            
            columns.forEach(col => {
                const value = row[col] !== null && row[col] !== undefined ? row[col] : '';
                const displayValue = escapeHtml(String(value));
                const isNonEditable = NON_EDITABLE_FIELDS.includes(col);
                const cellClass = isNonEditable ? 'read-only' : '';
                html += `<td class="${cellClass}" data-column="${escapeHtml(col)}">${displayValue || '<span style="color: var(--color-text-muted);">—</span>'}</td>`;
            });
            
            if (state.currentQueryContext) {
                html += `<td><button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); populateFormFromRow(${rowIndex})" 
                           title="Click to populate ${state.currentQueryContext} form">
                           <i class="fas fa-arrow-right"></i> Use
                        </button></td>`;
            }
            
            html += '</tr>';
        });
        
        html += '</tbody></table></div>';
        modalContent.innerHTML = html;
        exportBtn.style.display = 'inline-block';
        
        // Store original data for filtering
        state.modalOriginalData = data;
    }
    
    modal.classList.add('active');
    
    // Focus search input if it exists
    setTimeout(() => {
        const searchInput = document.getElementById('modalSearchInput');
        if (searchInput) {
            searchInput.focus();
        }
    }, 100);
}

function closeResultsModal() {
    document.getElementById('resultsModal').classList.remove('active');
    state.modalOriginalData = null;
    // Hide commit button if it was shown
    const commitBtn = document.getElementById('commitAssignmentsBtn');
    if (commitBtn) {
        commitBtn.style.display = 'none';
    }
}

// Show auto-assignment results modal with editable technician fields
function showAutoAssignModal(results, stats, date, stateValue, city) {
    const modal = document.getElementById('resultsModal');
    const modalTitle = document.getElementById('resultsModalTitle');
    const modalContent = document.getElementById('resultsModalContent');
    const exportBtn = document.getElementById('exportResultsBtn');
    const commitBtn = document.getElementById('commitAssignmentsBtn');
    
    modalTitle.textContent = `Auto-Assignment Results - ${date}${stateValue || city ? ` (${city || ''}${city && stateValue ? ', ' : ''}${stateValue || ''})` : ''}`;
    
    const assignments = results.assignments || [];
    const unassignable = results.unassignable || [];
    
    if (assignments.length === 0 && unassignable.length === 0) {
        modalContent.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox" style="font-size: 3rem; color: var(--color-text-muted); margin-bottom: 1rem;"></i>
                <h4 style="margin: 0 0 0.5rem 0; color: var(--color-text);">No Dispatches Found</h4>
                <p class="text-muted" style="margin: 0;">No unassigned dispatches found for the selected date and filters.</p>
            </div>
        `;
        exportBtn.style.display = 'none';
        if (commitBtn) commitBtn.style.display = 'none';
    } else {
        // Summary section
        let html = `
            <div class="capacity-summary" style="margin-bottom: 1.5rem;">
                <div class="capacity-header">
                    <h4><i class="fas fa-chart-bar"></i> Assignment Summary</h4>
                </div>
                <div class="capacity-stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Total Dispatches</div>
                        <div class="stat-value">${stats.total}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Successfully Assigned</div>
                        <div class="stat-value" style="color: #28a745;">${stats.assigned}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Unassignable</div>
                        <div class="stat-value" style="color: #dc3545;">${stats.unassigned}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Success Rate</div>
                        <div class="stat-value">${stats.success_rate}%</div>
                        <div class="progress-bar-container">
                            <div class="progress-bar" style="width: ${stats.success_rate}%; background-color: ${stats.success_rate >= 80 ? '#28a745' : stats.success_rate >= 50 ? '#ffc107' : '#dc3545'};"></div>
                        </div>
                    </div>
                    ${stats.avg_score > 0 ? `
                    <div class="stat-card">
                        <div class="stat-label">Average Score</div>
                        <div class="stat-value">${stats.avg_score}</div>
                    </div>
                    ` : ''}
                    ${stats.total_travel_time_min > 0 ? `
                    <div class="stat-card">
                        <div class="stat-label">Total Travel Time</div>
                        <div class="stat-value">${Math.round(stats.total_travel_time_min)} min</div>
                        <div class="stat-sub">${stats.total_travel_time_hrs} hours</div>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        // Assignments table with editable technician fields
        if (assignments.length > 0) {
            html += `
                <div class="capacity-details-section">
                    <h4><i class="fas fa-list"></i> Assignments (${assignments.length})</h4>
                    <p class="helper-text" style="margin-bottom: 1rem; color: var(--color-text-muted);">
                        <i class="fas fa-edit"></i> Click on Technician ID or Name to change assignment, or use the search button to find alternatives
                    </p>
                    <div class="modal-table-container" style="max-height: 50vh; overflow-y: auto;">
                        <table class="data-table modal-table" id="autoAssignTable">
                            <thead>
                                <tr>
                                    <th style="width: 50px;">#</th>
                                    <th>Dispatch ID</th>
                                    <th>Priority</th>
                                    <th>Technician ID</th>
                                    <th>Technician Name</th>
                                    <th>Distance (km)</th>
                                    <th>Travel Time (min)</th>
                                    <th>Score</th>
                                    <th style="width: 100px;">Action</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            assignments.forEach((assignment, index) => {
                html += `
                    <tr class="assignment-row" data-dispatch-id="${escapeHtml(assignment.Dispatch_id)}" data-index="${index}">
                        <td style="font-weight: 600; color: var(--color-text-muted);">${index + 1}</td>
                        <td><strong>${escapeHtml(assignment.Dispatch_id)}</strong></td>
                        <td><span style="padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.85rem; font-weight: 600; background-color: ${(assignment.Priority || 'Medium').toLowerCase() === 'high' ? '#dc3545' : (assignment.Priority || 'Medium').toLowerCase() === 'medium' ? '#ffc107' : '#6c757d'}; color: white;">${escapeHtml(assignment.Priority || 'Medium')}</span></td>
                        <td>
                            <input type="text" 
                                   class="tech-id-input form-control" 
                                   value="${escapeHtml(assignment.Technician_id)}" 
                                   data-original="${escapeHtml(assignment.Technician_id)}"
                                   style="width: 100%; padding: 0.25rem 0.5rem; font-size: 0.9rem;"
                                   placeholder="Tech ID">
                        </td>
                        <td>
                            <input type="text" 
                                   class="tech-name-input form-control" 
                                   value="${escapeHtml(assignment.Technician_name || '')}" 
                                   data-original="${escapeHtml(assignment.Technician_name || '')}"
                                   style="width: 100%; padding: 0.25rem 0.5rem; font-size: 0.9rem;"
                                   placeholder="Tech Name">
                        </td>
                        <td>${(assignment.Distance_km || 0).toFixed(2)}</td>
                        <td>${Math.round(assignment.Travel_time_min || 0)}</td>
                        <td><strong>${(assignment.Score || 0).toFixed(1)}</strong></td>
                        <td>
                            <button class="btn btn-sm btn-secondary" onclick="findTechForDispatch('${escapeHtml(assignment.Dispatch_id)}', ${index})" title="Find available technicians">
                                <i class="fas fa-search"></i>
                            </button>
                        </td>
                    </tr>
                `;
            });
            
            html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }
        
        // Unassignable dispatches
        if (unassignable.length > 0) {
            html += `
                <div class="capacity-details-section" style="margin-top: 1.5rem;">
                    <h4><i class="fas fa-exclamation-triangle"></i> Unassignable Dispatches (${unassignable.length})</h4>
                    <div class="capacity-alert alert-warning">
                        <i class="fas fa-info-circle"></i>
                        <strong>${unassignable.length} dispatch(es) could not be assigned</strong>
                        <div style="margin-top: 0.5rem;">
            `;
            unassignable.forEach((item, index) => {
                html += `<div>• ${escapeHtml(item.Dispatch_id)}: ${escapeHtml(item.Reason || 'No reason specified')}</div>`;
            });
            html += `
                        </div>
                    </div>
                </div>
            `;
        }
        
        modalContent.innerHTML = html;
        exportBtn.style.display = 'inline-block';
        if (commitBtn) {
            commitBtn.style.display = 'inline-block';
        }
        
        // Add change listeners to track modifications
        document.querySelectorAll('.tech-id-input, .tech-name-input').forEach(input => {
            input.addEventListener('change', function() {
                const row = this.closest('tr');
                const dispatchId = row.dataset.dispatchId;
                const index = parseInt(row.dataset.index);
                
                // Update state.autoAssignData
                if (state.autoAssignData && state.autoAssignData.assignments[index]) {
                    if (this.classList.contains('tech-id-input')) {
                        state.autoAssignData.assignments[index].Technician_id = this.value;
                    } else if (this.classList.contains('tech-name-input')) {
                        state.autoAssignData.assignments[index].Technician_name = this.value;
                    }
                }
            });
        });
    }
    
    modal.classList.add('active');
}

// Find available technicians for a dispatch (for manual override)
async function findTechForDispatch(dispatchId, rowIndex) {
    if (!checkInitialized()) return;
    
    try {
        showLoading(true);
        logMessage(`🔍 Finding available technicians for dispatch ${dispatchId}...`, 'header');
        
        const response = await fetch('/api/technicians/available', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                dispatch_id: parseInt(dispatchId),
                enable_range_expansion: state.autoAssignData ? state.autoAssignData.enable_range_expansion : true
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.data && data.data.length > 0) {
            // Show technician selection modal
            showTechSelectionModal(data.data, dispatchId, rowIndex);
        } else {
            alert(`No available technicians found for dispatch ${dispatchId}`);
        }
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'error');
        console.error(error);
    } finally {
        showLoading(false);
    }
}

// Show technician selection modal for manual override
function showTechSelectionModal(technicians, dispatchId, rowIndex) {
    const modal = document.getElementById('techListModal');
    const modalTitle = document.getElementById('techListModalTitle');
    const modalContent = document.getElementById('techListModalContent');
    
    modalTitle.textContent = `Select Technician for Dispatch ${dispatchId}`;
    
    let html = `
        <div class="modal-table-container" style="max-height: 60vh; overflow-y: auto;">
            <table class="data-table modal-table">
                <thead>
                    <tr>
                        <th>Technician ID</th>
                        <th>Name</th>
                        <th>Distance (km)</th>
                        <th>Travel Time (min)</th>
                        <th>Score</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    technicians.forEach(tech => {
        const techId = tech.Technician_id || tech.technician_id || '';
        const techName = tech.Name || tech.name || '';
        html += `
            <tr>
                <td><strong>${escapeHtml(techId)}</strong></td>
                <td>${escapeHtml(techName)}</td>
                <td>${((tech.Distance_km || tech.distance_km || 0)).toFixed(2)}</td>
                <td>${Math.round(tech.Travel_time_min || tech.travel_time_min || 0)}</td>
                <td><strong>${((tech.Score || tech.score || 0)).toFixed(1)}</strong></td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="selectTechForAssignment('${escapeHtml(techId)}', '${escapeHtml(techName.replace(/'/g, "\\'"))}', '${dispatchId}', ${rowIndex})">
                        <i class="fas fa-check"></i> Select
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    modalContent.innerHTML = html;
    modal.classList.add('active');
}

// Select technician for assignment override
function selectTechForAssignment(techId, techName, dispatchId, rowIndex) {
    // Update the assignment row
    const row = document.querySelector(`tr[data-dispatch-id="${dispatchId}"]`);
    if (row) {
        const techIdInput = row.querySelector('.tech-id-input');
        const techNameInput = row.querySelector('.tech-name-input');
        
        if (techIdInput) {
            techIdInput.value = techId;
            techIdInput.dispatchEvent(new Event('change'));
        }
        if (techNameInput) {
            techNameInput.value = techName;
            techNameInput.dispatchEvent(new Event('change'));
        }
    }
    
    // Update state
    if (state.autoAssignData && state.autoAssignData.assignments[rowIndex]) {
        state.autoAssignData.assignments[rowIndex].Technician_id = techId;
        state.autoAssignData.assignments[rowIndex].Technician_name = techName;
    }
    
    // Close technician selection modal
    closeTechListModal();
    
    logMessage(`✅ Updated assignment: ${dispatchId} → ${techName} (${techId})`, 'success');
}

// Commit assignments to database
async function commitAssignments() {
    if (!state.autoAssignData || !state.autoAssignData.assignments || state.autoAssignData.assignments.length === 0) {
        alert('No assignments to commit');
        return;
    }
    
    // Collect current assignments from the form (in case user made changes)
    const assignments = [];
    document.querySelectorAll('.assignment-row').forEach(row => {
        const dispatchId = row.dataset.dispatchId;
        const techIdInput = row.querySelector('.tech-id-input');
        const techNameInput = row.querySelector('.tech-name-input');
        
        if (techIdInput && techIdInput.value.trim()) {
            assignments.push({
                dispatch_id: dispatchId,
                technician_id: techIdInput.value.trim(),
                technician_name: techNameInput ? techNameInput.value.trim() : ''
            });
        }
    });
    
    if (assignments.length === 0) {
        alert('No valid assignments to commit. Please ensure all assignments have a Technician ID.');
        return;
    }
    
    if (!confirm(`Commit ${assignments.length} assignment(s) to the database?`)) {
        return;
    }
    
    try {
        showLoading(true);
        logMessage(`💾 Committing ${assignments.length} assignment(s)...`, 'header');
        
        const response = await fetch('/api/auto-assign/commit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                date: state.autoAssignData.date,
                assignments: assignments
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            logMessage(`✅ Successfully committed ${data.committed} assignment(s)`, 'success');
            if (data.failed && data.failed.length > 0) {
                logMessage(`⚠️ ${data.failed.length} assignment(s) failed: ${data.failed.join(', ')}`, 'warning');
            }
            
            // Close modal and refresh
            closeResultsModal();
            state.autoAssignData = null;
            
            // Refresh pending count
            refreshPending();
        } else {
            logMessage(`❌ Error committing assignments: ${data.error}`, 'error');
        }
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'error');
        console.error(error);
    } finally {
        showLoading(false);
    }
}

// Filter modal table rows based on search input
function filterModalTable(searchTerm) {
    const table = document.getElementById('modalResultsTable');
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr.modal-row');
    const term = searchTerm.toLowerCase().trim();
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        let matches = false;
        
        cells.forEach(cell => {
            const text = cell.textContent.toLowerCase();
            if (text.includes(term)) {
                matches = true;
            }
        });
        
        row.style.display = matches ? '' : 'none';
    });
    
    // Update visible count
    const visibleRows = Array.from(rows).filter(r => r.style.display !== 'none').length;
    const infoText = document.querySelector('.modal-toolbar .fas.fa-info-circle')?.parentElement;
    if (infoText && term) {
        infoText.innerHTML = `<i class="fas fa-info-circle"></i> Showing ${visibleRows} of ${rows.length} results`;
    }
}

function exportResults() {
    if (!state.currentData || state.currentData.length === 0) {
        alert('No data to export');
        return;
    }
    
    const csv = generateCSV(state.currentData, state.currentColumns);
    downloadCSV(csv, 'query_results.csv');
    logMessage('📥 Results exported to CSV', 'success');
}

function toggleConfigSection() {
    const configSection = document.getElementById('configSection');
    const toggleBtn = configSection.nextElementSibling.querySelector('button');
    
    if (configSection.style.display === 'none') {
        configSection.style.display = 'block';
        toggleBtn.innerHTML = '<i class="fas fa-cog"></i> Hide Configuration';
    } else {
        configSection.style.display = 'none';
        toggleBtn.innerHTML = '<i class="fas fa-cog"></i> Show Configuration';
    }
}

// ================================
// CELL EDITING
// ================================

let currentEditCell = null;

function editCell(rowIndex, column) {
    currentEditCell = {rowIndex, column};
    
    const currentValue = state.currentData[rowIndex][column];
    const displayValue = currentValue !== null && currentValue !== undefined ? currentValue : '';
    
    const editLabel = document.getElementById('editLabel');
    const editInput = document.getElementById('editInput');
    const editHelp = document.getElementById('editHelp');
    
    // Format column name for display (remove underscores, capitalize)
    const displayColumn = column.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    editLabel.textContent = `Edit: ${displayColumn}`;
    editLabel.innerHTML = `<i class="fas fa-edit"></i> Edit: <strong>${escapeHtml(displayColumn)}</strong>`;
    
    // Detect field type and set appropriate input type
    const lowerCol = column.toLowerCase();
    if (lowerCol.includes('date')) {
        editInput.type = 'date';
    } else if (lowerCol.includes('time')) {
        editInput.type = 'time';
    } else if (lowerCol.includes('email')) {
        editInput.type = 'email';
    } else if (lowerCol.includes('number') || lowerCol.includes('count') || lowerCol.includes('min')) {
        editInput.type = 'number';
    } else {
        editInput.type = 'text';
    }
    
    editInput.value = displayValue;
    editInput.maxLength = null;
    
    // Show help text
    if (editHelp) {
        editHelp.textContent = `Press Enter to save, Esc to cancel`;
    }
    
    document.getElementById('editModal').classList.add('active');
    setTimeout(() => {
        editInput.focus();
        editInput.select();
    }, 100);
}

function closeEditModal() {
    document.getElementById('editModal').classList.remove('active');
    currentEditCell = null;
}

function saveEdit() {
    if (!currentEditCell) return;
    
    const {rowIndex, column} = currentEditCell;
    const editInput = document.getElementById('editInput');
    const newValue = editInput.value;
    
    // Update data
    state.currentData[rowIndex][column] = newValue;
    
    // Track edit
    if (!state.editedRows.has(rowIndex)) {
        state.editedRows.set(rowIndex, {});
    }
    state.editedRows.get(rowIndex)[column] = newValue;
    
    // Re-render modal with updated data
    const modalTitle = document.getElementById('resultsModalTitle');
    if (modalTitle && document.getElementById('resultsModal').classList.contains('active')) {
        showResultsModal(modalTitle.textContent.split(' (')[0], state.currentData, state.currentColumns);
    }
    updateEditIndicator();
    
    closeEditModal();
    logMessage(`✅ Updated ${column}`, 'success');
}

// Keyboard shortcuts for modals
document.addEventListener('keydown', function(e) {
    // Edit Modal shortcuts
    if (document.getElementById('editModal').classList.contains('active')) {
        if (e.key === 'Enter' && !e.shiftKey && document.activeElement === document.getElementById('editInput')) {
            e.preventDefault();
            saveEdit();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            closeEditModal();
        }
    }
    
    // Results Modal shortcuts
    if (document.getElementById('resultsModal').classList.contains('active')) {
        if (e.key === 'Escape') {
            e.preventDefault();
            closeResultsModal();
        }
    }
    
    // Technician List Modal shortcuts
    if (document.getElementById('techListModal').classList.contains('active')) {
        if (e.key === 'Escape') {
            e.preventDefault();
            closeTechListModal();
        }
    }
    
    // Technician Calendar Modal shortcuts
    if (document.getElementById('techCalendarModal').classList.contains('active')) {
        if (e.key === 'Escape') {
            e.preventDefault();
            closeTechCalendarModal();
        }
    }
});

function updateEditIndicator() {
    // Edit indicator removed with data grid - edits are tracked but not displayed
    // Edits can still be exported via exportEdits() function
}

function undoAll() {
    if (state.editedRows.size === 0) return;
    
    if (confirm('Undo all edits and reload original data?')) {
        state.editedRows.clear();
        // Re-render modal with original data
        const modalTitle = document.getElementById('resultsModalTitle')?.textContent || 'Query Results';
        showResultsModal(modalTitle, state.currentData, state.currentColumns);
        updateEditIndicator();
        logMessage('↩️ All edits undone', 'warning');
    }
}

// ================================
// DATA EXPORT
// ================================

function exportData() {
    if (!state.currentData || state.currentData.length === 0) {
        alert('No data to export');
        return;
    }
    
    const csv = generateCSV(state.currentData, state.currentColumns);
    downloadCSV(csv, 'dispatch_data.csv');
    logMessage('📥 Data exported to CSV', 'success');
}

function exportEdits() {
    if (state.editedRows.size === 0) {
        alert('No edits to export');
        return;
    }
    
    let text = 'Edited Data:\n\n';
    
    state.editedRows.forEach((changes, rowIndex) => {
        text += `Row ${rowIndex + 1}:\n`;
        Object.entries(changes).forEach(([col, value]) => {
            text += `  ${col}: ${value}\n`;
        });
        text += '\n';
    });
    
    downloadText(text, 'dispatch_edits.txt');
    logMessage('📥 Edits exported', 'success');
}

function generateCSV(data, columns) {
    let csv = columns.join(',') + '\n';
    
    data.forEach(row => {
        const values = columns.map(col => {
            const value = row[col];
            const str = value !== null && value !== undefined ? String(value) : '';
            // Escape quotes and wrap in quotes if contains comma
            return str.includes(',') || str.includes('"') 
                ? `"${str.replace(/"/g, '""')}"` 
                : str;
        });
        csv += values.join(',') + '\n';
    });
    
    return csv;
}

function downloadCSV(csv, filename) {
    const blob = new Blob([csv], {type: 'text/csv'});
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

function downloadText(text, filename) {
    const blob = new Blob([text], {type: 'text/plain'});
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// ================================
// FORM POPULATION FROM QUERY RESULTS
// ================================

function populateFormFromRow(rowIndex) {
    if (!state.currentData || rowIndex >= state.currentData.length) {
        logMessage('❌ Invalid row index', 'error');
        return;
    }
    
    const row = state.currentData[rowIndex];
    const context = state.currentQueryContext;
    
    if (!context) {
        logMessage('❌ No query context available', 'error');
        return;
    }
    
    try {
        if (context === 'dispatch') {
            populateDispatchForm(row);
        } else if (context === 'technician') {
            populateTechnicianForm(row);
        } else {
            logMessage(`❌ Unknown context: ${context}`, 'error');
        }
        
        logMessage(`✅ Form populated from row ${rowIndex + 1}`, 'success');
    } catch (error) {
        logMessage(`❌ Error populating form: ${error.message}`, 'error');
        console.error(error);
    }
}

function populateDispatchForm(row) {
    // Populate Create Dispatch form
    // Handle various field name variations
    const address = row.Customer_address || row.Address || row.address || row.customer_address;
    if (address) {
        document.getElementById('createAddress').value = address;
    }
    
    const city = row.City || row.city;
    if (city) {
        document.getElementById('createCity').value = city;
        // Trigger city change to update state if needed
        onCreateCityChange();
    }
    
    const stateValue = row.State || row.state;
    if (stateValue) {
        document.getElementById('createState').value = stateValue;
        // Trigger state change to update cities
        onCreateStateChange();
    }
    
    const appointmentDt = row.Appointment_start_datetime || row.appointment_start_datetime || row.Appointment_datetime || row.appointment_datetime;
    if (appointmentDt) {
        const dt = new Date(appointmentDt);
        if (!isNaN(dt.getTime())) {
            document.getElementById('createDate').value = dt.toISOString().split('T')[0];
            const hours = String(dt.getHours()).padStart(2, '0');
            const minutes = String(dt.getMinutes()).padStart(2, '0');
            document.getElementById('createTime').value = `${hours}:${minutes}`;
        }
    }
    
    const duration = row.Duration_min || row.duration_min || row.Duration || row.duration;
    if (duration) {
        document.getElementById('createDuration').value = duration;
    }
    
    const skill = row.Required_skill || row.required_skill || row.Skill || row.skill;
    if (skill) {
        document.getElementById('createSkill').value = skill;
    }
    
    const priority = row.Priority || row.priority;
    if (priority) {
        document.getElementById('createPriority').value = priority;
    }
    
    // Populate Dispatch ID in queries tab if available
    const dispatchId = row.Dispatch_id || row.dispatch_id;
    if (dispatchId) {
        const dispatchIdField = document.getElementById('dispatchId');
        if (dispatchIdField) {
            dispatchIdField.value = dispatchId;
        }
        // Also populate in technician tab
        const techDispatchIdField = document.getElementById('techDispatchId');
        if (techDispatchIdField) {
            techDispatchIdField.value = dispatchId;
        }
    }
    
    // Populate location filters in queries tab
    if (city) {
        const queryCityField = document.getElementById('city');
        if (queryCityField) {
            queryCityField.value = city;
            onCityChange();
        }
    }
    if (stateValue) {
        const queryStateField = document.getElementById('state');
        if (queryStateField) {
            queryStateField.value = stateValue;
            onStateChange();
        }
    }
    
    // Switch to Create Dispatch tab
    switchTab('create');
}

function populateTechnicianForm(row) {
    // Populate Technician tab fields
    // Handle various field name variations
    const techId = row.Technician_id || row.technician_id || row.Tech_id;
    if (techId) {
        const techIdField = document.getElementById('techIdTech');
        if (techIdField) {
            techIdField.value = techId;
        }
    }
    
    const city = row.City || row.city;
    if (city) {
        const techCityField = document.getElementById('techCity');
        if (techCityField) {
            techCityField.value = city;
            onTechCityChange();
        }
    }
    
    const stateValue = row.State || row.state;
    if (stateValue) {
        const techStateField = document.getElementById('techState');
        if (techStateField) {
            techStateField.value = stateValue;
            onTechStateChange();
        }
    }
    
    const date = row.Date || row.date || row.Appointment_date;
    if (date) {
        const techDateField = document.getElementById('techDate');
        if (techDateField) {
            techDateField.value = date;
        }
    }
    
    const startDate = row.Start_date || row.start_date;
    if (startDate) {
        const techStartDateField = document.getElementById('techStartDate');
        if (techStartDateField) {
            techStartDateField.value = startDate;
        }
    }
    
    const endDate = row.End_date || row.end_date;
    if (endDate) {
        const techEndDateField = document.getElementById('techEndDate');
        if (techEndDateField) {
            techEndDateField.value = endDate;
        }
    }
    
    // Populate Dispatch ID if available (for finding technicians for a dispatch)
    const dispatchId = row.Dispatch_id || row.dispatch_id;
    if (dispatchId) {
        const techDispatchIdField = document.getElementById('techDispatchId');
        if (techDispatchIdField) {
            techDispatchIdField.value = dispatchId;
        }
        // Also populate in queries tab
        const dispatchIdField = document.getElementById('dispatchId');
        if (dispatchIdField) {
            dispatchIdField.value = dispatchId;
        }
    }
    
    // Switch to Technicians tab
    switchTab('technician');
}

// ================================
// UI HELPERS
// ================================

function logMessage(message, type = '') {
    const container = document.getElementById('systemMessages');
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.textContent = message;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function clearMessages() {
    document.getElementById('systemMessages').innerHTML = '';
}

function toggleSystemMessages() {
    const panel = document.getElementById('systemMessagesPanel');
    const icon = document.getElementById('systemMessagesToggleIcon');
    const isMinimized = panel.classList.contains('minimized');
    
    if (isMinimized) {
        // Expand
        panel.classList.remove('minimized');
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
        localStorage.setItem('systemMessagesMinimized', 'false');
    } else {
        // Minimize
        panel.classList.add('minimized');
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
        localStorage.setItem('systemMessagesMinimized', 'true');
    }
}

// Restore minimized state on page load
function restoreSystemMessagesState() {
    // System Messages - start minimized by default
    const sysMinimized = localStorage.getItem('systemMessagesMinimized');
    const panel = document.getElementById('systemMessagesPanel');
    const icon = document.getElementById('systemMessagesToggleIcon');
    if (panel && icon) {
        // Default to minimized if not explicitly set to expanded
        if (sysMinimized !== 'false') {
            panel.classList.add('minimized');
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }
    }
    
    // Data grid panel removed - all results display in modal
}

// Data grid removed - all results now display in modal

// ================================
// TAB MANAGEMENT
// ================================

function switchTab(tabName) {
    // Hide all tab panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab panel
    const selectedPanel = document.getElementById(`tab-${tabName}`);
    if (selectedPanel) {
        selectedPanel.classList.add('active');
    }
    
    // Add active class to selected tab button
    const selectedBtn = document.querySelector(`[data-tab="${tabName}"]`);
    if (selectedBtn) {
        selectedBtn.classList.add('active');
    }
    
    // Save selected tab to localStorage
    localStorage.setItem('selectedTab', tabName);
}

// Restore selected tab on page load
function restoreSelectedTab() {
    const savedTab = localStorage.getItem('selectedTab') || 'queries';
    switchTab(savedTab);
}

// Update pending count badge
function updatePendingBadge(count) {
    const badge = document.getElementById('pendingCountBadge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    }
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

function updateStatus(type, text) {
    const badge = document.getElementById('statusBadge');
    badge.className = `status-badge ${type}`;
    badge.innerHTML = text;
}

function checkInitialized() {
    if (!state.initialized) {
        alert('Please wait for the optimizer to initialize');
        return false;
    }
    return true;
}

function clearAll() {
    // Clear inputs
    document.getElementById('techId').value = '';
    document.getElementById('dispatchId').value = '';
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    document.getElementById('city').value = '';
    document.getElementById('state').value = '';
    
    // Clear data
    state.currentData = [];
    state.currentColumns = [];
    state.editedRows.clear();
    
    // Clear displays
    clearMessages();
    document.getElementById('gridContainer').innerHTML = `
        <div class="empty-state">
            <i class="fas fa-inbox"></i>
            <p>No data to display</p>
            <p class="text-muted">Run a query to see results</p>
        </div>
    `;
    updateEditIndicator();
    
    logMessage('🧹 All fields cleared', 'success');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ================================
// TECHNICIAN CALENDAR FUNCTIONS
// ================================

// Populate calendar state dropdown
function populateCalStateDropdown(states) {
    const dropdown = document.getElementById('calState');
    if (!dropdown) {
        console.warn('Calendar state dropdown element not found');
        return;
    }
    if (!states || !Array.isArray(states)) {
        console.error('Invalid states data:', states);
        return;
    }
    
    dropdown.innerHTML = '<option value="">-- All States --</option>';
    states.filter(s => s).forEach(state => {
        const option = document.createElement('option');
        option.value = state;
        option.textContent = state;
        dropdown.appendChild(option);
    });
    
    // Also populate city dropdown with all cities initially
    const cityDropdown = document.getElementById('calCity');
    if (cityDropdown && state.allCities && state.allCities.length > 0) {
        cityDropdown.innerHTML = '<option value="">-- All Cities --</option>';
        state.allCities.filter(c => c).forEach(city => {
            const option = document.createElement('option');
            option.value = city;
            option.textContent = city;
            cityDropdown.appendChild(option);
        });
    }
}

// Handle calendar state change
async function onCalStateChange() {
    const stateValue = document.getElementById('calState').value;
    const cityDropdown = document.getElementById('calCity');
    
    if (!cityDropdown) return;
    
    if (!stateValue) {
        cityDropdown.innerHTML = '<option value="">-- All Cities --</option>';
        // Populate with all cities if no state selected
        if (state.allCities && state.allCities.length > 0) {
            state.allCities.filter(c => c).forEach(city => {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                cityDropdown.appendChild(option);
            });
        }
        return;
    }
    
    // Get cities for this state from API
    try {
        const response = await fetch(`/api/cities?state=${encodeURIComponent(stateValue)}`);
        const data = await response.json();
        
        if (data.success && data.cities) {
            cityDropdown.innerHTML = '<option value="">-- All Cities --</option>';
            data.cities.filter(c => c).forEach(city => {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                cityDropdown.appendChild(option);
            });
        } else {
            // Fallback to cityStateMapping if API fails
            const cities = state.cityStateMapping[stateValue] || [];
            cityDropdown.innerHTML = '<option value="">-- All Cities --</option>';
            cities.forEach(city => {
                if (city) {
                    const option = document.createElement('option');
                    option.value = city;
                    option.textContent = city;
                    cityDropdown.appendChild(option);
                }
            });
        }
    } catch (error) {
        console.error('Error loading cities for state:', error);
        // Fallback to cityStateMapping
        const cities = state.cityStateMapping[stateValue] || [];
        cityDropdown.innerHTML = '<option value="">-- All Cities --</option>';
        cities.forEach(city => {
            if (city) {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                cityDropdown.appendChild(option);
            }
        });
    }
}

// Handle calendar city change
function onCalCityChange() {
    // Can add additional logic if needed
}

// Clear calendar fields
function clearCalFields() {
    document.getElementById('calTechId').value = '';
    document.getElementById('calTechName').value = '';
    document.getElementById('calState').value = '';
    document.getElementById('calCity').value = '';
    document.getElementById('calStartDate').value = '';
    document.getElementById('calEndDate').value = '';
    onCalStateChange();
}

// Query technician calendar by ID/Name
async function queryTechCalendar() {
    if (!checkInitialized()) return;
    
    const techId = document.getElementById('calTechId').value.trim();
    const techName = document.getElementById('calTechName').value.trim();
    const startDate = document.getElementById('calStartDate').value || null;
    const endDate = document.getElementById('calEndDate').value || null;
    
    if (!techId && !techName) {
        alert('Please enter either Technician ID or Name');
        return;
    }
    
    try {
        showLoading(true);
        logMessage(`📅 Fetching calendar for ${techId || techName}...`, 'header');
        
        const response = await fetch('/api/technician/calendar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                tech_id: techId || null,
                tech_name: techName || null,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.data && data.data.length > 0) {
            // Show calendar entries in modal with edit capability
            showTechCalendarModal(data.data, data.columns);
            logMessage(`✅ Loaded ${data.count} calendar entries`, 'success');
        } else {
            logMessage(`❌ ${data.error || 'No calendar entries found'}`, 'error');
            alert(data.error || 'No calendar entries found');
        }
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'error');
        console.error(error);
    } finally {
        showLoading(false);
    }
}

// Query technicians by location
async function queryTechByLocation() {
    if (!checkInitialized()) return;
    
    const city = document.getElementById('calCity').value.trim();
    const stateValue = document.getElementById('calState').value.trim();
    
    if (!city && !stateValue) {
        alert('Please enter City or State');
        return;
    }
    
    try {
        showLoading(true);
        logMessage(`🔍 Finding technicians in ${city || ''} ${stateValue || ''}...`, 'header');
        
        const response = await fetch('/api/technicians/by-location', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                city: city || null,
                state: stateValue || null
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.data && data.data.length > 0) {
            // Show technician list modal
            showTechListModal(data.data, data.columns);
            logMessage(`✅ Found ${data.count} technicians`, 'success');
        } else {
            logMessage(`❌ No technicians found`, 'error');
            alert('No technicians found in this location');
        }
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'error');
        console.error(error);
    } finally {
        showLoading(false);
    }
}

// Show technician list modal
function showTechListModal(data, columns) {
    const modal = document.getElementById('techListModal');
    const modalTitle = document.getElementById('techListModalTitle');
    const modalContent = document.getElementById('techListModalContent');
    
    const rowCount = data ? data.length : 0;
    modalTitle.textContent = `Select Technician${rowCount > 0 ? ` (${rowCount} ${rowCount === 1 ? 'found' : 'found'})` : ''}`;
    
    if (!data || data.length === 0) {
        modalContent.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-user-slash" style="font-size: 3rem; color: var(--color-text-muted); margin-bottom: 1rem;"></i>
                <h4 style="margin: 0 0 0.5rem 0; color: var(--color-text);">No Technicians Found</h4>
                <p class="text-muted" style="margin: 0;">No technicians match your search criteria. Try adjusting your location filters.</p>
            </div>
        `;
    } else {
        let html = `
            <div class="modal-toolbar" style="margin-bottom: 1rem; display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 200px;">
                    <input type="text" id="techListSearchInput" class="form-control" placeholder="🔍 Search technicians..." 
                           style="width: 100%; padding: 0.5rem; border: 1px solid var(--color-border); border-radius: 4px;"
                           onkeyup="filterTechListTable(this.value)">
                </div>
                <div style="color: var(--color-text-muted); font-size: 0.9rem;">
                    <i class="fas fa-info-circle"></i> ${rowCount} ${rowCount === 1 ? 'technician' : 'technicians'} • Click row to select
                </div>
            </div>
        `;
        
        html += '<div class="modal-table-container" style="max-height: 60vh; overflow-y: auto; border: 1px solid var(--color-border); border-radius: 4px;">';
        html += '<table class="data-table modal-table" id="techListTable"><thead><tr>';
        columns.forEach(col => {
            html += `<th>${escapeHtml(col)}</th>`;
        });
        html += '<th style="width: 120px;">Action</th></tr></thead><tbody>';
        
        data.forEach((row, rowIndex) => {
            const techId = row['Technician_id'] || '';
            const techName = escapeHtml(String(row['Name'] || ''));
            html += `<tr class="clickable-row tech-list-row" 
                          onclick="selectTechnicianFromList('${techId}', '${techName}')"
                          style="cursor: pointer;"
                          title="Click to select this technician">`;
            columns.forEach(col => {
                const value = row[col] !== null && row[col] !== undefined ? row[col] : '';
                html += `<td>${escapeHtml(String(value)) || '<span style="color: var(--color-text-muted);">—</span>'}</td>`;
            });
            html += `<td><button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); selectTechnicianFromList('${techId}', '${techName}')" 
                       title="Select this technician">
                       <i class="fas fa-check"></i> Select
                    </button></td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table></div>';
        modalContent.innerHTML = html;
        
        // Store original data for filtering
        state.techListOriginalData = data;
    }
    
    modal.classList.add('active');
    
    // Focus search input if it exists
    setTimeout(() => {
        const searchInput = document.getElementById('techListSearchInput');
        if (searchInput) {
            searchInput.focus();
        }
    }, 100);
}

// Filter technician list table
function filterTechListTable(searchTerm) {
    const table = document.getElementById('techListTable');
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr.tech-list-row');
    const term = searchTerm.toLowerCase().trim();
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        let matches = false;
        
        cells.forEach(cell => {
            const text = cell.textContent.toLowerCase();
            if (text.includes(term)) {
                matches = true;
            }
        });
        
        row.style.display = matches ? '' : 'none';
    });
    
    // Update visible count
    const visibleRows = Array.from(rows).filter(r => r.style.display !== 'none').length;
    const infoText = document.querySelector('#techListModal .modal-toolbar .fas.fa-info-circle')?.parentElement;
    if (infoText && term) {
        infoText.innerHTML = `<i class="fas fa-info-circle"></i> Showing ${visibleRows} of ${rows.length} technicians`;
    }
}

// Close technician list modal
function closeTechListModal() {
    document.getElementById('techListModal').classList.remove('active');
}

// Select technician from list and load calendar
function selectTechnicianFromList(techId, techName) {
    closeTechListModal();
    
    // Populate the search fields
    document.getElementById('calTechId').value = techId;
    document.getElementById('calTechName').value = techName;
    
    // Clear the city/state fields to avoid confusion
    document.getElementById('calState').value = '';
    document.getElementById('calCity').value = '';
    
    // Query the calendar - this will show the same modal as individual tech query
    queryTechCalendar();
}

// Show technician calendar modal with editable form
function showTechCalendarModal(data, columns) {
    const modal = document.getElementById('techCalendarModal');
    const modalTitle = document.getElementById('techCalendarModalTitle');
    const modalContent = document.getElementById('techCalendarModalContent');
    
    if (!data || data.length === 0) {
        alert('No calendar data to display');
        return;
    }
    
    if (!modal || !modalTitle || !modalContent) {
        console.error('Modal elements not found');
        alert('Modal elements not found. Please refresh the page.');
        return;
    }
    
    // Ensure the form exists - preserve it if it does, recreate if it doesn't
    let formExists = document.getElementById('techCalendarForm');
    if (!formExists) {
        // Form was removed, recreate it from template
        const formHtml = `
            <form id="techCalendarForm">
                <div class="form-grid">
                    <div class="form-group">
                        <label for="calFormTechId">Technician ID</label>
                        <input type="text" id="calFormTechId" readonly class="read-only-field">
                    </div>
                    <div class="form-group">
                        <label for="calFormTechName">Technician Name</label>
                        <input type="text" id="calFormTechName" readonly class="read-only-field">
                    </div>
                    <div class="form-group">
                        <label for="calFormDate">Date</label>
                        <input type="date" id="calFormDate" required>
                    </div>
                    <div class="form-group">
                        <label for="calFormAvailable">Available</label>
                        <select id="calFormAvailable" required>
                            <option value="1">Yes</option>
                            <option value="0">No</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="calFormStartTime">Start Time</label>
                        <input type="time" id="calFormStartTime">
                    </div>
                    <div class="form-group">
                        <label for="calFormEndTime">End Time</label>
                        <input type="time" id="calFormEndTime">
                    </div>
                    <div class="form-group">
                        <label for="calFormMaxAssignments">Max Assignments (hours)</label>
                        <input type="number" id="calFormMaxAssignments" min="0" step="1">
                    </div>
                    <div class="form-group">
                        <label for="calFormCity">City</label>
                        <input type="text" id="calFormCity" placeholder="e.g., Dallas">
                    </div>
                    <div class="form-group">
                        <label for="calFormState">State</label>
                        <input type="text" id="calFormState" placeholder="e.g., TX" maxlength="2">
                    </div>
                    <div class="form-group form-group-full">
                        <label>Update Type</label>
                        <div class="form-options" style="margin-top: 8px;">
                            <label>
                                <input type="radio" name="calUpdateType" id="calUpdateSingleDay" value="single" checked>
                                Single Day Update
                            </label>
                            <label>
                                <input type="radio" name="calUpdateType" id="calUpdatePermanent" value="permanent">
                                Permanent Move
                            </label>
                        </div>
                    </div>
                    <div class="form-group form-group-full">
                        <label for="calFormReason">Reason (if unavailable)</label>
                        <input type="text" id="calFormReason" placeholder="Enter reason for unavailability">
                    </div>
                </div>
            </form>
        `;
        modalContent.innerHTML = formHtml;
    } else {
        // Form exists, just remove any existing calendar table
        const existingTable = modalContent.querySelector('.calendar-entries-table');
        if (existingTable) {
            existingTable.remove();
        }
    }
    
    // Filter out columns that should not appear in table (shown in form instead)
    const excludedColumns = ['Technician_id', 'Name', 'City', 'State'];
    const filteredColumns = columns.filter(col => !excludedColumns.includes(col));
    
    // Define column order: Date first, then others
    const priorityColumns = ['Date'];
    const orderedColumns = [];
    const remainingColumns = [];
    
    // Add priority columns in order
    priorityColumns.forEach(col => {
        if (filteredColumns.includes(col)) {
            orderedColumns.push(col);
        }
    });
    
    // Add remaining columns (excluding priority ones and excluded columns)
    filteredColumns.forEach(col => {
        if (!priorityColumns.includes(col) && !excludedColumns.includes(col)) {
            remainingColumns.push(col);
        }
    });
    
    // Combine ordered and remaining columns
    const finalColumns = [...orderedColumns, ...remainingColumns];
    
    // Helper function to format column names (replace _ with spaces and capitalize)
    function formatColumnName(colName) {
        return colName
            .replace(/_/g, ' ')
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
    }
    
    // Use first entry for initial form population
    const firstEntry = data[0];
    const techId = firstEntry['Technician_id'] || '';
    const techName = firstEntry['Name'] || '';
    
    // Update modal title
    modalTitle.textContent = `Calendar: ${techName} (${techId})`;
    
    // Store all entries for navigation
    window.currentCalendarEntries = data;
    window.currentCalendarIndex = 0;
    
    // Populate form with first entry
    populateCalendarForm(firstEntry);
    
    // Attach date change listener to update datetime fields
    const dateField = document.getElementById('calFormDate');
    if (dateField) {
        // Remove existing listeners by cloning
        const newDateField = dateField.cloneNode(true);
        dateField.parentNode.replaceChild(newDateField, dateField);
        newDateField.addEventListener('change', updateDateTimeFields);
    }
    
    // Show calendar entries table below form
    let html = '<div class="calendar-entries-table" style="margin-top: 20px;"><h4>All Calendar Entries</h4>';
    html += '<table class="data-table"><thead><tr>';
    finalColumns.forEach(col => {
        html += `<th>${escapeHtml(formatColumnName(col))}</th>`;
    });
    html += '<th>Action</th></tr></thead><tbody>';
    
    data.forEach((row, rowIndex) => {
        html += '<tr>';
        finalColumns.forEach(col => {
            const value = row[col] !== null && row[col] !== undefined ? row[col] : '';
            html += `<td>${escapeHtml(String(value))}</td>`;
        });
        html += `<td><button class="btn btn-sm btn-primary" onclick="loadCalendarEntry(${rowIndex})">Edit</button></td>`;
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    
    // Append table to modal content (don't overwrite the form)
    modalContent.insertAdjacentHTML('beforeend', html);
    
    // Scroll to top to show the form
    modalContent.scrollTop = 0;
    
    // Show the modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

// Helper function - no longer needed since time fields don't include dates
// Keeping for backward compatibility but it's a no-op now
function updateDateTimeFields() {
    // Time fields are now separate from date, so no update needed
    return;
}

// Populate calendar form with entry data
function populateCalendarForm(entry) {
    // Populate Technician ID and Name (read-only fields)
    const techId = entry['Technician_id'] || '';
    const techName = entry['Name'] || '';
    document.getElementById('calFormTechId').value = techId;
    document.getElementById('calFormTechName').value = techName;
    
    // Update modal title
    const modalTitle = document.getElementById('techCalendarModalTitle');
    if (modalTitle) {
        modalTitle.textContent = `Calendar: ${techName} (${techId})`;
    }
    
    // Populate editable fields
    const dateValue = entry['Date'] || '';
    const dateField = document.getElementById('calFormDate');
    dateField.value = dateValue;
    
    // Remove existing event listener if any, then add new one
    const newDateField = dateField.cloneNode(true);
    dateField.parentNode.replaceChild(newDateField, dateField);
    newDateField.addEventListener('change', updateDateTimeFields);
    
    document.getElementById('calFormAvailable').value = entry['Available'] || '1';
    
    // Extract time only (HH:MM) from Start_time timestamp
    if (entry['Start_time']) {
        const startTime = new Date(entry['Start_time']);
        const hours = String(startTime.getHours()).padStart(2, '0');
        const minutes = String(startTime.getMinutes()).padStart(2, '0');
        document.getElementById('calFormStartTime').value = `${hours}:${minutes}`;
    } else {
        document.getElementById('calFormStartTime').value = '';
    }
    
    // Extract time only (HH:MM) from End_time timestamp
    if (entry['End_time']) {
        const endTime = new Date(entry['End_time']);
        const hours = String(endTime.getHours()).padStart(2, '0');
        const minutes = String(endTime.getMinutes()).padStart(2, '0');
        document.getElementById('calFormEndTime').value = `${hours}:${minutes}`;
    } else {
        document.getElementById('calFormEndTime').value = '';
    }
    
    document.getElementById('calFormMaxAssignments').value = entry['Max_assignments'] || '';
    
    // Populate City and State (editable fields)
    document.getElementById('calFormCity').value = entry['City'] || '';
    document.getElementById('calFormState').value = entry['State'] || '';
    
    // Set default to single day update
    document.getElementById('calUpdateSingleDay').checked = true;
    document.getElementById('calUpdatePermanent').checked = false;
    
    document.getElementById('calFormReason').value = entry['Reason'] || '';
}

// Load specific calendar entry into form
function loadCalendarEntry(index) {
    if (window.currentCalendarEntries && window.currentCalendarEntries[index]) {
        const entry = window.currentCalendarEntries[index];
        
        // Ensure form exists before populating
        const modalContent = document.getElementById('techCalendarModalContent');
        if (!modalContent || !document.getElementById('techCalendarForm')) {
            console.error('Calendar form not found, cannot load entry');
            return;
        }
        
        // Populate form with selected entry
        populateCalendarForm(entry);
        window.currentCalendarIndex = index;
        
        // Re-attach date change listener (populateCalendarForm might have cloned the field)
        const dateField = document.getElementById('calFormDate');
        if (dateField) {
            // Remove existing listeners by cloning
            const newDateField = dateField.cloneNode(true);
            dateField.parentNode.replaceChild(newDateField, dateField);
            newDateField.addEventListener('change', updateDateTimeFields);
        }
        
        // Scroll to top of form to show populated fields
        if (modalContent) {
            modalContent.scrollTop = 0;
            
            // Highlight the form section briefly to draw attention
            const form = document.getElementById('techCalendarForm');
            if (form) {
                form.style.transition = 'box-shadow 0.3s ease';
                form.style.boxShadow = '0 0 10px rgba(0, 123, 255, 0.5)';
                setTimeout(() => {
                    form.style.boxShadow = '';
                }, 1000);
            }
        }
    }
}

// Close technician calendar modal
function closeTechCalendarModal() {
    const modal = document.getElementById('techCalendarModal');
    if (modal) {
        modal.classList.remove('active');
    }
    document.body.style.overflow = ''; // Restore scrolling
    
    window.currentCalendarEntries = null;
    window.currentCalendarIndex = 0;
    
    // Remove the table but keep the form
    const modalContent = document.getElementById('techCalendarModalContent');
    if (modalContent) {
        const existingTable = modalContent.querySelector('.calendar-entries-table');
        if (existingTable) {
            existingTable.remove();
        }
        // Reset form fields
        const form = document.getElementById('techCalendarForm');
        if (form) {
            form.reset();
        }
    }
    
    // Reset form HTML to original (only if needed)
    if (modalContent && !modalContent.querySelector('#techCalendarForm')) {
        modalContent.innerHTML = `
        <form id="techCalendarForm">
            <div class="form-grid">
                <div class="form-group">
                    <label for="calFormTechId">Technician ID</label>
                    <input type="text" id="calFormTechId" readonly class="read-only-field">
                </div>
                <div class="form-group">
                    <label for="calFormTechName">Technician Name</label>
                    <input type="text" id="calFormTechName" readonly class="read-only-field">
                </div>
                <div class="form-group">
                    <label for="calFormDate">Date</label>
                    <input type="date" id="calFormDate" required>
                </div>
                <div class="form-group">
                    <label for="calFormAvailable">Available</label>
                    <select id="calFormAvailable" required>
                        <option value="1">Yes</option>
                        <option value="0">No</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="calFormStartTime">Start Time</label>
                    <input type="time" id="calFormStartTime">
                </div>
                <div class="form-group">
                    <label for="calFormEndTime">End Time</label>
                    <input type="time" id="calFormEndTime">
                </div>
                <div class="form-group">
                    <label for="calFormMaxAssignments">Max Assignments (hours)</label>
                    <input type="number" id="calFormMaxAssignments" min="0" step="1">
                </div>
                <div class="form-group">
                    <label for="calFormCity">City</label>
                    <input type="text" id="calFormCity" placeholder="e.g., Dallas">
                </div>
                <div class="form-group">
                    <label for="calFormState">State</label>
                    <input type="text" id="calFormState" placeholder="e.g., TX" maxlength="2">
                </div>
                <div class="form-group form-group-full">
                    <label>Update Type</label>
                    <div class="form-options" style="margin-top: 8px;">
                        <label>
                            <input type="radio" name="calUpdateType" id="calUpdateSingleDay" value="single" checked>
                            Single Day Update
                        </label>
                        <label>
                            <input type="radio" name="calUpdateType" id="calUpdatePermanent" value="permanent">
                            Permanent Move
                        </label>
                    </div>
                </div>
                <div class="form-group form-group-full">
                    <label for="calFormReason">Reason (if unavailable)</label>
                    <input type="text" id="calFormReason" placeholder="Enter reason for unavailability">
                </div>
            </div>
        </form>
        `;
    }
}

// Save technician calendar changes
async function saveTechCalendar() {
    const techId = document.getElementById('calFormTechId').value;
    const date = document.getElementById('calFormDate').value;
    const available = parseInt(document.getElementById('calFormAvailable').value);
    const startTimeInput = document.getElementById('calFormStartTime').value;
    const endTimeInput = document.getElementById('calFormEndTime').value;
    const maxAssignments = document.getElementById('calFormMaxAssignments').value;
    const reason = document.getElementById('calFormReason').value;
    
    if (!techId || !date) {
        alert('Technician ID and Date are required');
        return;
    }
    
    // Combine date from Date field with time from time inputs (HH:MM format)
    let startTime = null;
    let endTime = null;
    
    if (startTimeInput && date) {
        // Time input is in HH:MM format, combine with date
        startTime = new Date(date + 'T' + startTimeInput + ':00').toISOString();
    }
    
    if (endTimeInput && date) {
        // Time input is in HH:MM format, combine with date
        endTime = new Date(date + 'T' + endTimeInput + ':00').toISOString();
    }
    
    try {
        showLoading(true);
        logMessage(`💾 Saving calendar changes for ${techId} on ${date}...`, 'header');
        
        const response = await fetch('/api/technician/calendar/update', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                tech_id: techId,
                date: date,
                available: available,
                start_time: startTime,
                end_time: endTime,
                max_assignments: parseInt(maxAssignments) || null,
                reason: reason || null
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            logMessage(`✅ Calendar updated successfully`, 'success');
            alert('Calendar updated successfully!');
            closeTechCalendarModal();
            // Refresh calendar data
            queryTechCalendar();
        } else {
            logMessage(`❌ Error: ${data.error}`, 'error');
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        logMessage(`❌ Error: ${error.message}`, 'error');
        console.error(error);
        alert(`Error: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

