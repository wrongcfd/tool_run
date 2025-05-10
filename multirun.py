import os
import subprocess

resolutions = [256, 512]
timesteps = [0.000390625, 0.0001953125]

param_file = "input/params.yml"  # Path to your parameter file
exec_cmd = "./gpulbm"            # Your executable command
# log_prefix = "run" # Defined in the original code but not used; use if needed in log_file formatting

assert len(resolutions) == len(timesteps), "Number of resolutions and timesteps do not match"

def update_params_in_file_string_mode(filepath, params_to_update):
    """
    Reads, updates, and writes back YAML-like parameter files using pure string manipulation.
    This version has improved key matching to handle variable spacing around keys and colons.

    Args:
        filepath (str): The path to the parameter file.
        params_to_update (dict): A dictionary containing keys and new values to update.
                                 Example: {'APP_RESOLUTION': 128, 'APP_TIMESTEP': 0.001}

    Raises:
        IOError: If file reading or writing fails.

    Notes:
        - It now robustly finds keys like 'KEY      :' by stripping whitespace from the part before the colon.
        - Preserves leading whitespace (indentation) of original lines.
        - Modified/added lines are written as 'KEY: VALUE\n' (plus original indentation).
        - If a key does not exist in the file, it will be appended to the end.
        - Does not support complex YAML structures or preserving inline comments on modified lines.
    """
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
    except IOError:
        print "Info: File '{}' not found. It will be created with the new parameters.".format(filepath) # Python 2 print
        lines = []

    new_lines = []
    keys_to_update_list = params_to_update.keys() # List of keys like 'APP_RESOLUTION'
    updated_flags = {key: False for key in keys_to_update_list}

    for line in lines:
        original_leading_whitespace = line[:len(line) - len(line.lstrip())]
        content_part = line.lstrip() # Part of the line without leading whitespace

        colon_index = content_part.find(':')
        key_found_on_this_line = None

        if colon_index != -1:
            file_key_raw = content_part[:colon_index] # Part before the colon
            file_key_stripped = file_key_raw.strip()  # Remove spaces around the key name from file

            for key_to_check in keys_to_update_list:
                if file_key_stripped == key_to_check:
                    key_found_on_this_line = key_to_check
                    break
        
        if key_found_on_this_line:
            # Key matched, replace this line
            new_value = params_to_update[key_found_on_this_line]
            
            if isinstance(new_value, float):
                formatted_value = "{:.8f}".format(new_value) # Adjust precision as needed
                formatted_value = formatted_value.rstrip('0').rstrip('.')
                if formatted_value == "" or formatted_value == ".": 
                    formatted_value = "0"
                elif formatted_value == "-" or formatted_value == "-.":
                    formatted_value = "-0"
            else:
                formatted_value = str(new_value)
            
            # Construct the new line using the canonical key from params_to_update for consistent output
            new_lines.append(original_leading_whitespace + key_found_on_this_line + ": " + formatted_value + "\n")
            updated_flags[key_found_on_this_line] = True
        else:
            # No matching key to update on this line, or it's not a key-value line; preserve it
            new_lines.append(line)

    # Append any keys that were in params_to_update but not found and updated in the file
    for key_to_add in keys_to_update_list:
        if not updated_flags[key_to_add]:
            new_value = params_to_update[key_to_add]
            if isinstance(new_value, float):
                formatted_value = "{:.8f}".format(new_value) # Adjust precision as needed
                formatted_value = formatted_value.rstrip('0').rstrip('.')
                if formatted_value == "" or formatted_value == ".": 
                    formatted_value = "0"
                elif formatted_value == "-" or formatted_value == "-.":
                    formatted_value = "-0"
            else:
                formatted_value = str(new_value)
            
            print "Warning: Parameter '{}' was not found in file '{}'. It has been appended.".format(key_to_add, filepath) # Python 2 print
            # New keys are appended without leading whitespace (i.e., at the beginning of the new line)
            new_lines.append(key_to_add + ": " + formatted_value + "\n")

    with open(filepath, 'w') as f:
        for new_line_to_write in new_lines:
            f.write(new_line_to_write)

# --- Main program loop ---
for i, (res, dt) in enumerate(zip(resolutions, timesteps), start=1):
    print "[{}] Running with APP_RESOLUTION={}, APP_TIMESTEP={}".format(i, res, dt)

    params_to_set = {
        'APP_RESOLUTION': res,
        'APP_TIMESTEP': dt
    }
    
    try:
        update_params_in_file_string_mode(param_file, params_to_set)
    except IOError as e:
        print "Error: Failed to process parameter file '{}': {}".format(param_file, e) 
        print "Please check file permissions or if the path is correct." 
        break 

    log_file = "{}+gp.log".format(i)

    try:
        with open(log_file, "w") as out_file:
            process = subprocess.Popen([exec_cmd], stdout=out_file, stderr=subprocess.STDOUT)
        process.wait() 
    except OSError as e:
        print "Error: Failed to execute command '{}': {}".format(exec_cmd, e) 
        print "Please ensure '{}' is a valid executable and is in the correct path or system PATH.".format(exec_cmd) 
        # break 
    except Exception as e:
        print "An unknown error occurred while running command '{}': {}".format(exec_cmd, e) 
        # break 

print " Simulations for all parameter combinations are complete."