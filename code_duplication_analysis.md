# Code Duplication Analysis - Modules Folder

## Executive Summary

The modules folder contains significant code duplication that can be reduced to improve maintainability, consistency, and reduce the potential for bugs. This analysis identifies **7 major areas** where duplication exists and provides concrete recommendations for refactoring.

## Major Duplication Issues Identified

### 1. **Duplicate `add_to_rig_log` Function** ⚠️ HIGH PRIORITY

**Issue**: The exact same function is duplicated across multiple modules:
- `modules/fluorescence.py` (line 265)
- `modules/laser_power.py` (line 439) 
- `modules/pulse_width.py` (line 209)

**Current Code Pattern**:
```python
def add_to_rig_log(activity, description):
    """Add an entry to the rig log."""
    
    # Load existing rig log
    rig_log_df = load_dataframe(RIG_LOG_FILE, pd.DataFrame({
        "Date": [],
        "Researcher": [],
        "Activity": [],
        "Description": [],
        "Category": []
    }))
    
    # Create new entry
    new_entry = pd.DataFrame({
        "Date": [datetime.now().strftime("%Y-%m-%d %H:%M")],
        "Researcher": [st.session_state.researcher],
        "Activity": [activity],
        "Description": [description],
        "Category": ["Measurement"]  # Category varies by module
    })
    
    # Append and save...
```

**Recommendation**: 
- Move this function to `modules/data_utils.py` 
- Add a `category` parameter with a sensible default
- Remove all duplicate implementations

### 2. **Repetitive Import Statements** ⚠️ MEDIUM PRIORITY

**Issue**: Nearly identical import patterns across modules:

**From `data_utils`**:
```python
# fluorescence.py, laser_power.py, pulse_width.py all import similar sets:
from modules.data_utils import load_dataframe, save_dataframe, ensure_columns, safe_numeric_conversion, filter_dataframe, calculate_statistics, linear_regression
```

**From `ui_components`**:
```python
# Most modules import large subsets of the same functions:
from modules.ui_components import create_header, create_info_box, create_warning_box, create_success_box, create_metric_row, create_data_editor, create_plot, create_tab_section, create_form_section, display_image, get_image_path
```

**Recommendation**:
- Create module-specific import groups in `__init__.py`
- Use star imports for commonly used function groups
- Create utility import functions for common patterns

### 3. **Duplicate Constants** ⚠️ MEDIUM PRIORITY

**Issue**: The same constants are defined in multiple modules:

```python
# Defined in 4 different modules:
RIG_LOG_FILE = "rig_log.csv"
```

**Found in**:
- `modules/fluorescence.py` (line 18)
- `modules/laser_power.py` (line 16) 
- `modules/pulse_width.py` (line 18)
- `modules/rig_log.py` (line 17)

**Recommendation**:
- Create a `modules/constants.py` file for shared constants
- Import constants from this central location

### 4. **Repetitive DataFrame Initialization Patterns** ⚠️ MEDIUM PRIORITY

**Issue**: Similar DataFrame initialization patterns repeated across modules:

```python
# Pattern repeated in multiple modules:
df = load_dataframe(FILE_NAME, pd.DataFrame({
    "Date": [],
    "Researcher": [],
    "Activity": [],
    "Description": [],
    "Category": []
}))
```

**Recommendation**:
- Create factory functions for common DataFrame schemas
- Use template-based initialization for standard data structures

### 5. **Common Header and Layout Patterns** ⚠️ LOW PRIORITY

**Issue**: Similar rendering patterns across modules:

```python
# Common pattern in render_*_tab functions:
def render_*_tab():
    create_header("Title")
    
    # Create two columns for layout
    col1, col2 = st.columns([3, 2])
    
    with col1:
        render_*_theory_and_procedure()
    
    with col2:
        render_*_visualization()
        render_*_tips()
```

**Recommendation**:
- Create a base layout template function
- Parameterize common layout patterns

### 6. **Duplicate Standard Library Imports** ⚠️ LOW PRIORITY

**Issue**: Same standard library imports across modules:

```python
# Repeated in most modules:
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os
from pathlib import Path
```

**Recommendation**:
- Create a `modules/common_imports.py` with frequently used imports
- Use consistent import organization

### 7. **Similar Error Handling and Validation Patterns** ⚠️ LOW PRIORITY

**Issue**: Similar patterns for data validation and error handling are implemented differently across modules.

**Recommendation**:
- Create common validation utility functions
- Standardize error handling approaches

## Refactoring Recommendations

### Phase 1: High Priority Changes

1. **Create `modules/shared_utils.py`**:
   ```python
   """Shared utility functions used across multiple modules."""
   
   def add_to_rig_log(activity, description, category="General"):
       """Centralized rig log entry function."""
       # Move implementation here
   
   def get_default_rig_log_df():
       """Return a default rig log DataFrame structure."""
       # Centralize DataFrame schema
   ```

2. **Create `modules/constants.py`**:
   ```python
   """Shared constants used across modules."""
   
   # File paths
   RIG_LOG_FILE = "rig_log.csv"
   LASER_POWER_FILE = "laser_power_measurements.csv"
   FLUORESCENCE_FILE = "fluorescence_measurements.csv"
   PULSE_WIDTH_FILE = "pulse_width_measurements.csv"
   
   # Common DataFrame columns
   RIG_LOG_COLUMNS = ["Date", "Researcher", "Activity", "Description", "Category"]
   ```

### Phase 2: Medium Priority Changes

3. **Optimize imports in `__init__.py`**:
   ```python
   # Create import groups for common patterns
   from modules.data_utils import *  # For data operations
   from modules.ui_components import *  # For UI components
   from modules.constants import *  # For shared constants
   from modules.shared_utils import *  # For shared utilities
   ```

4. **Create template functions for common patterns**:
   ```python
   def create_two_column_layout(left_content_func, right_content_func, ratio=[3, 2]):
       """Standard two-column layout template."""
       col1, col2 = st.columns(ratio)
       with col1:
           left_content_func()
       with col2:
           right_content_func()
   ```

### Phase 3: Low Priority Improvements

5. **Standardize module structure**
6. **Create common validation utilities**
7. **Implement consistent error handling**

## Expected Benefits

### Maintainability
- **Reduced bug propagation**: Fixes in shared functions benefit all modules
- **Easier updates**: Changes to common functionality require updates in only one place
- **Consistent behavior**: Shared functions ensure consistent behavior across modules

### Code Quality
- **Reduced lines of code**: Eliminate hundreds of lines of duplicate code
- **Better testing**: Shared functions can be unit tested once
- **Improved readability**: Modules focus on their specific functionality

### Development Velocity
- **Faster feature development**: New modules can leverage existing utilities
- **Easier onboarding**: New developers see consistent patterns
- **Reduced maintenance overhead**: Less code to maintain and update

## Implementation Priority

1. **Week 1**: Implement `shared_utils.py` and `constants.py` (HIGH priority items)
2. **Week 2**: Refactor imports and create template functions (MEDIUM priority)
3. **Week 3**: Address remaining duplication patterns (LOW priority)

## Risk Assessment

**Low Risk**: The proposed changes are primarily extracting existing code into shared utilities. This should not introduce new bugs if done carefully with proper testing.

**Mitigation**: Implement changes incrementally and test each module after refactoring to ensure functionality remains intact.

---

*Generated by code analysis on modules folder - Total files analyzed: 8*