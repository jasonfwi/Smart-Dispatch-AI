"""
Smart Dispatch AI - Flask Web Application
Modern web-based interface for AI-powered dispatch optimization
"""

from flask import Flask, render_template, jsonify, request
from dispatch import SmartDispatchAI
from db_maintenance import DatabaseMaintenance
from typing import Dict, Any, Optional, Callable
from functools import wraps, lru_cache
import traceback
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global AI instance
optimizer: Optional[SmartDispatchAI] = None

# Global maintenance instance
maintenance: Optional[DatabaseMaintenance] = None
MAX_RANGE_KM = 15.0

# Cache for frequently accessed data
_cache: Dict[str, Any] = {}


def init_optimizer():
    """Initialize the Smart Dispatch AI with lazy loading."""
    global optimizer, maintenance
    if optimizer is None:
        logger.info("Initializing Smart Dispatch AI (Local SQLite mode)...")
        try:
            optimizer = SmartDispatchAI(max_range_km=MAX_RANGE_KM)
            logger.info("✓ Local database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize local database: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    if maintenance is None:
        logger.info("Initializing Database Maintenance...")
        try:
            maintenance = DatabaseMaintenance()
            logger.info("✓ Database Maintenance initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Database Maintenance: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    return optimizer


def handle_api_errors(f: Callable) -> Callable:
    """Decorator to handle API errors consistently."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.error(f"Validation error in {f.__name__}: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}\n{traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 500
    return wrapper


def cache_result(cache_key: str, ttl_seconds: int = 300):
    """Decorator to cache results with TTL."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            now = datetime.now().timestamp()
            if cache_key in _cache:
                cached_data, timestamp = _cache[cache_key]
                if now - timestamp < ttl_seconds:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_data
            
            result = f(*args, **kwargs)
            _cache[cache_key] = (result, now)
            return result
        return wrapper
    return decorator


def df_to_dict(df) -> Dict[str, Any]:
    """Efficiently convert Spark DataFrame or pandas DataFrame to dict format."""
    # Check if it's a pandas DataFrame
    if hasattr(df, 'to_dict') and hasattr(df, 'columns') and not hasattr(df, 'collect'):
        # It's a pandas DataFrame
        rows = df.to_dict('records')
        columns = list(df.columns)
        return {
            'data': rows,
            'columns': columns,
            'count': len(rows)
        }
    else:
        # It's a Spark DataFrame
        rows = df.collect()
        # Get columns from DataFrame schema (more reliable than Row.keys())
        columns = df.columns
        return {
            'data': [row.asDict() for row in rows],
            'columns': columns,
            'count': len(rows)
        }


@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')


@app.route('/api/init', methods=['POST'])
@handle_api_errors
def api_init():
    """Initialize optimizer."""
    data = request.get_json() or {}
    global MAX_RANGE_KM
    MAX_RANGE_KM = float(data.get('max_range_km', 15.0))
    
    opt = init_optimizer()
    
    # Get dropdowns data (cached for performance)
    states = opt.get_unique_states()
    cities = opt.get_unique_cities()
    city_state_mapping = opt.get_city_state_mapping()
    
    return jsonify({
        'success': True,
        'states': states,
        'cities': cities,
        'city_state_mapping': city_state_mapping,
        'message': 'Smart Dispatch AI initialized successfully'
    })


@app.route('/api/cities', methods=['GET'])
@handle_api_errors
def api_cities():
    """Get cities, optionally filtered by state."""
    opt = init_optimizer()
    state = request.args.get('state') or None
    cities = opt.get_unique_cities(state=state)
    
    return jsonify({
        'success': True,
        'cities': cities
    })


@app.route('/api/unassigned', methods=['POST'])
@handle_api_errors
def api_unassigned():
    """Get unassigned dispatches."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    date = data.get('date') or None
    city = data.get('city') or None
    state = data.get('state') or None
    limit = int(data.get('limit', 100))
    
    result = opt.get_unassigned_dispatches(
        date=date,
        city=city,
        state=state,
        limit=limit
    )
    
    # Efficient DataFrame to dict conversion
    result_dict = df_to_dict(result)
    
    return jsonify({
        'success': True,
        **result_dict
    })


@app.route('/api/technician/assignments', methods=['POST'])
@handle_api_errors
def api_tech_assignments():
    """Check technician assignments."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    tech_id = data.get('tech_id')
    date = data.get('date') or None
    
    if not tech_id:
        raise ValueError('tech_id required')
    
    # Get structured data instead of capturing stdout
    result = opt.check_technician_assignments(tech_id, date)
    
    return jsonify({
        'success': True,
        'data': result
    })


@app.route('/api/technician/availability', methods=['POST'])
@handle_api_errors
def api_tech_availability():
    """Check technician availability. Supports tech_id or city/state query."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    tech_id = data.get('tech_id')
    city = data.get('city')
    state = data.get('state')
    date = data.get('date') or None
    
    # If tech_id provided, check single technician
    if tech_id:
        result = opt.check_technician_availability(tech_id, date)
        tech_info = opt._get_technician_data_cached(tech_id)
        
        # Build response with all technician info
        response_data = {
            'tech_id': tech_id,
            'name': tech_info.name if tech_info else '',
            'city': tech_info.location.city if tech_info and tech_info.location else '',
            'state': tech_info.location.state if tech_info and tech_info.location else '',
            'primary_skill': tech_info.primary_skill if tech_info else '',
            'available': result.available,
            'start_time': result.start_time,
            'end_time': result.end_time,
            'available_minutes': result.available_minutes or 0,
            'assigned_minutes': result.assigned_minutes or 0,
            'remaining_minutes': result.remaining_minutes if hasattr(result, 'remaining_minutes') else ((result.available_minutes or 0) - (result.assigned_minutes or 0)),
            'utilization_pct': result.utilization_pct if hasattr(result, 'utilization_pct') else ((result.assigned_minutes or 0) / (result.available_minutes or 1) * 100) if result.available_minutes else 0.0,
            'reason': result.reason or ''
        }
        
        return jsonify({
            'success': True,
            'single': True,
            'data': response_data
        })
    
    # If city/state provided, get list of technicians and their availability
    if city or state:
        if not city or not state:
            raise ValueError('Both city and state are required for location-based queries')
        
        # Get technicians by location
        techs_df = opt.get_technicians_by_location(city=city, state=state)
        
        # Handle both Spark DataFrame and pandas DataFrame
        import pandas as pd
        if techs_df is None:
            return jsonify({
                'success': True,
                'single': False,
                'count': 0,
                'results': []
            })
        
        # Convert to list of dicts (handle both Spark and pandas)
        if isinstance(techs_df, pd.DataFrame):
            techs = techs_df.to_dict('records')
            if len(techs) == 0:
                return jsonify({
                    'success': True,
                    'single': False,
                    'count': 0,
                    'results': []
                })
        else:
            # Spark DataFrame
            if techs_df.count() == 0:
                return jsonify({
                    'success': True,
                    'single': False,
                    'count': 0,
                    'results': []
                })
            techs = techs_df.select("Technician_id", "Name", "City", "State").collect()
        
        # Get availability for each technician
        results = []
        for tech_row in techs:
            # Handle both Spark Row and dict
            if isinstance(tech_row, dict):
                # pandas dict
                tech_id_val = str(tech_row.get("Technician_id", ""))
                tech_name = str(tech_row.get("Name", ""))
                tech_city = str(tech_row.get("City", ""))
                tech_state = str(tech_row.get("State", ""))
            else:
                # Spark Row (uses dict-style access, not .get())
                tech_id_val = str(tech_row["Technician_id"]) if tech_row["Technician_id"] else ""
                tech_name = str(tech_row["Name"]) if tech_row["Name"] else ""
                tech_city = str(tech_row["City"]) if tech_row["City"] else ""
                tech_state = str(tech_row["State"]) if tech_row["State"] else ""
            
            if not tech_id_val:
                continue
                
            try:
                result = opt.check_technician_availability(tech_id_val, date)
                tech_info = opt._get_technician_data_cached(tech_id_val)
                
                # Get city/state from tech_info.location if available, otherwise use row data
                if tech_info and tech_info.location:
                    final_city = tech_info.location.city or tech_city
                    final_state = tech_info.location.state or tech_state
                    final_name = tech_info.name or tech_name
                    final_skill = tech_info.primary_skill
                else:
                    final_city = tech_city
                    final_state = tech_state
                    final_name = tech_name
                    final_skill = None
                
                results.append({
                    'tech_id': tech_id_val,
                    'name': final_name,
                    'city': final_city,
                    'state': final_state,
                    'available': result.available,
                    'start_time': result.start_time,
                    'end_time': result.end_time,
                    'available_minutes': result.available_minutes or 0,
                    'assigned_minutes': result.assigned_minutes or 0,
                    'remaining_minutes': result.remaining_minutes if hasattr(result, 'remaining_minutes') else ((result.available_minutes or 0) - (result.assigned_minutes or 0)),
                    'utilization_pct': result.utilization_pct if hasattr(result, 'utilization_pct') else ((result.assigned_minutes or 0) / (result.available_minutes or 1) * 100) if result.available_minutes else 0.0,
                    'reason': result.reason or '',
                    'primary_skill': final_skill or ''
                })
            except Exception as e:
                logger.warning(f"Error checking availability for {tech_id_val}: {e}")
                results.append({
                    'tech_id': tech_id_val,
                    'name': tech_name,
                    'city': tech_city,
                    'state': tech_state,
                    'available': False,
                    'reason': f'Error: {str(e)}'
                })
        
        return jsonify({
            'success': True,
            'single': False,
            'count': len(results),
            'results': results
        })
    
    raise ValueError('Either tech_id or both city and state are required')


@app.route('/api/dispatches/available', methods=['POST'])
@handle_api_errors
def api_available_dispatches():
    """Find available dispatches for technician."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    tech_id = data.get('tech_id')
    date = data.get('date')
    
    if not tech_id or not date:
        raise ValueError('tech_id and date required')
    
    result = opt.find_available_dispatches(tech_id, date)
    
    if result is None:
        return jsonify({
            'success': True,
            'data': [],
            'columns': [],
            'count': 0
        })
    
    result_dict = df_to_dict(result)
    
    return jsonify({
        'success': True,
        **result_dict
    })


@app.route('/api/technicians/available', methods=['POST'])
@handle_api_errors
def api_available_technicians():
    """Find available technicians for dispatch."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    dispatch_id = data.get('dispatch_id')
    enable_range_expansion = data.get('enable_range_expansion', True)
    
    if not dispatch_id:
        raise ValueError('dispatch_id required')
    
    result = opt.find_available_technicians(str(dispatch_id), enable_range_expansion=enable_range_expansion)
    
    if result is None:
        return jsonify({
            'success': True,
            'data': [],
            'columns': [],
            'count': 0
        })
    
    result_dict = df_to_dict(result)
    
    return jsonify({
        'success': True,
        **result_dict
    })


@app.route('/api/technicians/list', methods=['POST'])
@handle_api_errors
def api_list_technicians():
    """List available technicians for date."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    date = data.get('date')
    city = data.get('city') or None
    state = data.get('state') or None
    
    if not date:
        raise ValueError('date required')
    
    result = opt.list_available_technicians(date, city, state)
    
    if result is None:
        return jsonify({
            'success': True,
            'data': [],
            'columns': [],
            'count': 0
        })
    
    result_dict = df_to_dict(result)
    
    return jsonify({
        'success': True,
        **result_dict
    })


@app.route('/api/availability/summary', methods=['POST'])
@handle_api_errors
def api_availability_summary():
    """Get availability summary for date range."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    city = data.get('city') or None
    state = data.get('state') or None
    
    if not start_date or not end_date:
        raise ValueError('start_date and end_date required')
    
    result = opt.get_technician_availability_summary(start_date, end_date, city, state)
    
    if result is None:
        return jsonify({
            'success': True,
            'data': [],
            'columns': [],
            'count': 0
        })
    
    result_dict = df_to_dict(result)
    
    return jsonify({
        'success': True,
        **result_dict
    })


@app.route('/api/auto-assign', methods=['POST'])
@handle_api_errors
def api_auto_assign():
    """Auto-assign dispatches with optional scoring algorithm and range expansion."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    date = data.get('date')
    state = data.get('state')
    city = data.get('city')
    dry_run = data.get('dry_run', True)
    use_scoring = data.get('use_scoring', True)
    enable_range_expansion = data.get('enable_range_expansion', True)
    
    if not date:
        raise ValueError('date required')
    
    logger.info(f"Auto-assign request: date={date}, state={state}, city={city}, "
                f"dry_run={dry_run}, scoring={use_scoring}, range_expansion={enable_range_expansion}")
    
    # Get unassigned dispatches with filters
    unassigned = opt.get_unassigned_dispatches(limit=1000, city=city, state=state, date=date)
    
    if not unassigned or len(unassigned) == 0:
        return jsonify({
            'success': True,
            'results': {'total': 0, 'assigned': 0, 'unassigned': 0, 'assignments': [], 'unassignable': []},
            'statistics': {'total': 0, 'assigned': 0, 'unassigned': 0, 'success_rate': 0, 
                         'avg_score': 0, 'total_travel_time_min': 0, 'total_travel_time_hrs': 0},
            'message': f'No unassigned dispatches found for {date} with filters: State={state or "Any"}, City={city or "Any"}'
        })
    
    # Process dispatches
    assignments, unassignable = [], []
    total_travel_time = 0.0
    
    for dispatch in unassigned:
        dispatch_id = dispatch.get("Dispatch_id")
        if not dispatch_id:
            continue
            
        available = opt.find_available_technicians(dispatch_id, enable_range_expansion=enable_range_expansion)
        
        if available and len(available) > 0:
            if use_scoring:
                best = max(available, key=lambda t: t.get("Score", 0))
            else:
                best = min(available, key=lambda t: t.get("Distance_km", float('inf')))
            
            assignments.append({
                "Dispatch_id": dispatch_id,
                "Technician_id": best["Technician_id"],
                "Technician_name": best.get("Name", ""),
                "Distance_km": best.get("Distance_km", 0),
                "Travel_time_min": best.get("Travel_time_min", 0),
                "Score": best.get("Score", 0),
                "Priority": str(dispatch.get("Priority", "Medium"))
            })
            total_travel_time += best.get("Travel_time_min", 0)
        else:
            unassignable.append({
                "Dispatch_id": dispatch_id,
                "Reason": "No available technicians"
            })
    
    results = {
        "total": len(unassigned),
        "assigned": len(assignments),
        "unassigned": len(unassignable),
        "success_rate": round(len(assignments)/len(unassigned)*100, 1) if unassigned else 0,
        "avg_score": round(sum(a.get("Score", 0) for a in assignments) / len(assignments), 1) if assignments else 0.0,
        "total_travel_time": round(total_travel_time, 1),
        "assignments": assignments,
        "unassignable": unassignable
    }
    
    return jsonify({
        'success': True,
        'results': results,
        'statistics': {
            'total': results['total'],
            'assigned': results['assigned'],
            'unassigned': results['unassigned'],
            'success_rate': results.get('success_rate', 0),
            'avg_score': results.get('avg_score', 0),
            'total_travel_time_min': results.get('total_travel_time', 0),
            'total_travel_time_hrs': round(results.get('total_travel_time', 0) / 60, 1)
        }
    })


@app.route('/api/auto-assign/commit', methods=['POST'])
@handle_api_errors
def api_commit_assignments():
    """Commit auto-assignments to the database."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    date = data.get('date')
    assignments = data.get('assignments', [])
    
    if not date:
        raise ValueError('date required')
    
    if not assignments or len(assignments) == 0:
        raise ValueError('assignments list required')
    
    logger.info(f"Committing {len(assignments)} assignments for date {date}")
    
    committed = []
    failed = []
    
    # Check if using local DB
    is_local = hasattr(opt, 'db') and opt.db is not None
    
    for assignment in assignments:
        dispatch_id = assignment.get('dispatch_id')
        technician_id = assignment.get('technician_id')
        
        if not dispatch_id or not technician_id:
            failed.append(f"{dispatch_id or 'Unknown'}: Missing dispatch_id or technician_id")
            continue
        
        try:
            logger.info(f"Assigning {dispatch_id} to technician {technician_id}")
            
            if is_local:
                # Update in local database using transaction
                with opt.db.transaction():
                    opt.db.execute_non_query(
                        "UPDATE current_dispatches SET Assigned_technician_id = ? WHERE Dispatch_id = ?",
                        (technician_id, dispatch_id)
                    )
                committed.append(dispatch_id)
                logger.info(f"✅ Committed assignment {dispatch_id} → {technician_id}")
            else:
                # Should not reach here in local-only mode
                logger.error(f"Database connection not available for assignment {dispatch_id} → {technician_id}")
                failed.append(f"{dispatch_id}: Database connection not available")
                
        except Exception as e:
            logger.error(f"Error committing assignment {dispatch_id} → {technician_id}: {e}")
            failed.append(f"{dispatch_id}: {str(e)}")
    
    return jsonify({
        'success': True,
        'committed': len(committed),
        'failed_count': len(failed),
        'committed_ids': committed,
        'failed': failed
    })


@app.route('/api/dispatches/valid-addresses', methods=['GET'])
@handle_api_errors
def api_valid_addresses():
    """Get all valid addresses from database."""
    opt = init_optimizer()
    addresses = opt.get_valid_addresses()
    
    return jsonify({
        'success': True,
        'count': len(addresses),
        'addresses': addresses
    })


@app.route('/api/dispatches/valid-priorities', methods=['GET'])
@handle_api_errors
def api_valid_priorities():
    """Get all valid priority values."""
    opt = init_optimizer()
    priorities = opt.get_valid_priorities()
    
    return jsonify({
        'success': True,
        'priorities': priorities
    })


@app.route('/api/dispatches/valid-reasons', methods=['GET'])
@handle_api_errors
def api_valid_reasons():
    """Get all valid dispatch reason values."""
    opt = init_optimizer()
    reasons = opt.get_valid_dispatch_reasons()
    
    return jsonify({
        'success': True,
        'count': len(reasons),
        'reasons': reasons
    })


@app.route('/api/dispatches/valid-skills', methods=['GET'])
@handle_api_errors
def api_valid_skills():
    """Get all valid skill values."""
    opt = init_optimizer()
    skills = opt.get_valid_skills()
    
    return jsonify({
        'success': True,
        'skills': skills
    })


@app.route('/api/locations/states', methods=['GET'])
@handle_api_errors
def api_get_states():
    """Get all unique states."""
    opt = init_optimizer()
    states = opt.get_unique_states()
    
    return jsonify({
        'success': True,
        'states': states
    })


@app.route('/api/locations/addresses', methods=['GET'])
@handle_api_errors
def api_get_addresses():
    """Get addresses, optionally filtered by city and/or state."""
    opt = init_optimizer()
    city = request.args.get('city', '').strip() or None
    state = request.args.get('state', '').strip() or None
    
    addresses = opt.get_addresses_by_location(city=city, state=state)
    
    return jsonify({
        'success': True,
        'addresses': addresses,
        'count': len(addresses)
    })


@app.route('/api/dispatches/validate-address', methods=['POST'])
@handle_api_errors
def api_validate_address():
    """Validate that an address exists in the database."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    address = data.get('address')
    city = data.get('city')
    state = data.get('state')
    
    if not all([address, city, state]):
        raise ValueError('address, city, and state required')
    
    result = opt.validate_address(address, city, state)
    
    return jsonify({
        'success': True,
        **result
    })


@app.route('/api/dispatches/create', methods=['POST'])
@handle_api_errors
def api_create_dispatch():
    """Create a new dispatch with validation."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    # Required fields
    required_fields = ['customer_address', 'city', 'state', 'appointment_datetime',
                      'duration_min', 'required_skill', 'priority', 'dispatch_reason']
    
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise ValueError(f'Missing required fields: {missing}')
    
    # Optional flags
    auto_assign = data.get('auto_assign', False)
    commit_to_db = data.get('commit_to_db', False)
    
    logger.info(f"Creating dispatch: {data.get('customer_address')}, "
                f"auto_assign={auto_assign}, commit={commit_to_db}")
    
    # Parse datetime string to datetime object
    from datetime import datetime as dt
    dt_str = data['appointment_datetime']
    try:
        # Try ISO format first (handles both with and without timezone)
        appointment_dt = dt.fromisoformat(dt_str.replace('Z', '+00:00'))
        if appointment_dt.tzinfo:
            appointment_dt = appointment_dt.replace(tzinfo=None)  # Remove timezone
    except ValueError:
        # Fallback: parse as simple format YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM
        try:
            appointment_dt = dt.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            appointment_dt = dt.strptime(dt_str, '%Y-%m-%dT%H:%M')
    
    result = opt.create_dispatch(
        customer_address=data['customer_address'],
        city=data['city'],
        state=data['state'],
        appointment_datetime=appointment_dt,
        duration_min=data['duration_min'],
        required_skill=data['required_skill'],
        priority=data['priority'],
        dispatch_reason=data['dispatch_reason'],
        auto_assign=auto_assign,
        commit_to_db=commit_to_db
    )
    
    return jsonify(result)


@app.route('/api/dispatches/pending', methods=['GET'])
@handle_api_errors
def api_pending_dispatches():
    """Get all pending dispatches not yet committed to database."""
    opt = init_optimizer()
    pending = opt.get_pending_dispatches()
    
    return jsonify({
        'success': True,
        'count': len(pending),
        'dispatches': pending
    })


@app.route('/api/dispatches/pending/clear', methods=['POST'])
@handle_api_errors
def api_clear_pending():
    """Clear all pending dispatches without committing."""
    opt = init_optimizer()
    result = opt.clear_pending_dispatches()
    
    return jsonify(result)


@app.route('/api/dispatches/commit', methods=['POST'])
@handle_api_errors
def api_commit_dispatches():
    """Commit all pending dispatches to the database."""
    opt = init_optimizer()
    result = opt.commit_pending_dispatches()
    
    return jsonify(result)


@app.route('/api/capacity/city', methods=['POST'])
@handle_api_errors
def api_city_capacity():
    """Get capacity information for a city/state/date. Supports overview mode."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    city = data.get('city') or None
    state = data.get('state') or None
    date = data.get('date')
    
    if not state:
        raise ValueError('state is required')
    
    if not date:
        raise ValueError('date is required')
    
    logger.info(f"Capacity check: city={city}, state={state} on {date}")
    capacity = opt.get_city_capacity(city=city, state=state, target_date=date)
    
    # Check if it's overview mode (returns list) or single result (returns dict)
    if isinstance(capacity, list):
        return jsonify({
            'success': True,
            'overview': True,
            'count': len(capacity),
            'results': capacity
        })
    else:
        return jsonify({
            'success': True,
            'overview': False,
            **capacity
        })


@app.route('/api/capacity/check', methods=['POST'])
@handle_api_errors
def api_check_capacity():
    """Check if there is sufficient capacity for a dispatch."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    city = data.get('city')
    state = data.get('state')
    date = data.get('date')
    duration_min = data.get('duration_min')
    
    if not all([city, state, date, duration_min]):
        raise ValueError('city, state, date, and duration_min required')
    
    result = opt.check_capacity_available(city, state, date, duration_min)
    
    return jsonify({
        'success': True,
        **result
    })


@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint."""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'optimizer_initialized': optimizer is not None,
        'cache_size': len(_cache),
        'database_mode': 'local'
    })


@app.route('/api/cache/clear', methods=['POST'])
def api_clear_cache():
    """Clear the API cache."""
    global _cache
    cache_size = len(_cache)
    _cache.clear()
    logger.info(f"Cleared {cache_size} cache entries")
    return jsonify({
        'success': True,
        'message': f'Cleared {cache_size} cache entries'
    })


@app.route('/api/technician/calendar', methods=['POST'])
@handle_api_errors
def api_get_technician_calendar():
    """Get technician calendar entries by ID or name."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    tech_id = data.get('tech_id') or None
    tech_name = data.get('tech_name') or None
    start_date = data.get('start_date') or None
    end_date = data.get('end_date') or None
    
    if not tech_id and not tech_name:
        raise ValueError('tech_id or tech_name required')
    
    result = opt.get_technician_calendar(tech_id, tech_name, start_date, end_date)
    
    if result is None:
        tech_identifier = tech_id or tech_name or 'Unknown'
        return jsonify({
            'success': False,
            'error': f'Technician "{tech_identifier}" not found in database'
        })
    
    result_dict = df_to_dict(result)
    
    # Check if result is empty (technician exists but no calendar entries)
    if result_dict.get('count', 0) == 0:
        tech_identifier = tech_id or tech_name or 'Unknown'
        logger.info(f"Technician {tech_identifier} found but has no calendar entries")
        # Still return success with empty data so form can be populated
        return jsonify({
            'success': True,
            'message': f'Technician "{tech_identifier}" found but has no calendar entries',
            **result_dict
        })
    
    return jsonify({
        'success': True,
        **result_dict
    })


@app.route('/api/technicians/by-location', methods=['POST'])
@handle_api_errors
def api_get_technicians_by_location():
    """Get list of technicians by city/state."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    city = data.get('city') or None
    state = data.get('state') or None
    
    if not city and not state:
        raise ValueError('city or state required')
    
    result = opt.get_technicians_by_location(city, state)
    
    if result is None:
        return jsonify({
            'success': True,
            'data': [],
            'columns': [],
            'count': 0
        })
    
    result_dict = df_to_dict(result)
    
    return jsonify({
        'success': True,
        **result_dict
    })


@app.route('/api/technician/calendar/update', methods=['POST'])
@handle_api_errors
def api_update_technician_calendar():
    """Update a technician calendar entry."""
    opt = init_optimizer()
    data = request.get_json() or {}
    
    tech_id = data.get('tech_id')
    date = data.get('date')
    
    if not tech_id or not date:
        raise ValueError('tech_id and date required')
    
    available = data.get('available')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    max_assignments = data.get('max_assignments')
    city = data.get('city')
    state = data.get('state')
    update_type = data.get('update_type', 'single')
    reason = data.get('reason')
    
    success = opt.update_technician_calendar(
        tech_id, date, available, start_time, end_time, max_assignments, reason,
        city=city, state=state, update_type=update_type
    )
    
    if not success:
        return jsonify({
            'success': False,
            'error': 'Calendar entry not found or update failed'
        })
    
    return jsonify({
        'success': True,
        'message': 'Calendar update successful'
    })


# ================================
# DATABASE MAINTENANCE ENDPOINTS
# ================================

@app.route('/api/maintenance/history', methods=['POST'])
@handle_errors
def api_get_history():
    """Get change history with optional filters."""
    if not checkInitialized():
        return jsonify({'success': False, 'error': 'System not initialized'})
    
    data = request.json or {}
    table_name = data.get('table_name')
    limit = data.get('limit', 100)
    offset = data.get('offset', 0)
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    # Use maintenance instance
    history = maintenance.get_change_history(
        table_name=table_name,
        limit=limit,
        offset=offset,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify({
        'success': True,
        'history': history,
        'count': len(history)
    })


@app.route('/api/maintenance/stats', methods=['GET'])
@handle_errors
def api_get_stats():
    """Get database change statistics."""
    if not checkInitialized():
        return jsonify({'success': False, 'error': 'System not initialized'})
    
    # Use maintenance instance
    stats = maintenance.get_change_stats()
    
    return jsonify({
        'success': True,
        'stats': stats
    })


@app.route('/api/maintenance/rollback', methods=['POST'])
@handle_errors
def api_rollback_change():
    """Rollback a specific change."""
    if not checkInitialized():
        return jsonify({'success': False, 'error': 'System not initialized'})
    
    data = request.json or {}
    change_id = data.get('change_id')
    
    if not change_id:
        return jsonify({'success': False, 'error': 'change_id is required'})
    
    # Use maintenance instance
    success = maintenance.rollback_change(change_id)
    
    if success:
        # Clear cache after rollback
        _cache.clear()
        return jsonify({
            'success': True,
            'message': f'Successfully rolled back change {change_id}'
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Failed to rollback change {change_id}'
        })


@app.route('/api/maintenance/delete', methods=['POST'])
@handle_errors
def api_delete_record():
    """Delete a record from the database."""
    if not checkInitialized():
        return jsonify({'success': False, 'error': 'System not initialized'})
    
    data = request.json or {}
    table_name = data.get('table_name')
    record_id = data.get('record_id')
    reason = data.get('reason', 'User requested deletion')
    
    if not table_name or not record_id:
        return jsonify({'success': False, 'error': 'table_name and record_id are required'})
    
    # Validate table name
    valid_tables = ['current_dispatches', 'technicians', 'technician_calendar', 'dispatch_history']
    if table_name not in valid_tables:
        return jsonify({'success': False, 'error': f'Invalid table name. Must be one of: {", ".join(valid_tables)}'})
    
    # Use maintenance instance
    success = maintenance.delete_record(table_name, record_id, reason)
    
    if success:
        # Clear cache after deletion
        _cache.clear()
        return jsonify({
            'success': True,
            'message': f'Successfully deleted record {record_id} from {table_name}'
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Failed to delete record {record_id} from {table_name}'
        })


if __name__ == '__main__':
    logger.info("🚀 Starting Smart Dispatch AI Web App...")
    logger.info("📍 Open your browser to: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)

