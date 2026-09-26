import yaml

file_path = 'config/nav2_params.yaml'
try:
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)

    # Change the Behavior Tree loop duration from 10ms (100Hz) to 50ms (20Hz)
    if 'bt_navigator' in config:
        config['bt_navigator']['ros__parameters']['bt_loop_duration'] = 50
            
    with open(file_path, 'w') as f:
        yaml.dump(config, f)
    print("SUCCESS: Behavior Tree tick rate relaxed from 100Hz to 20Hz!")
except Exception as e:
    print(f"Error: {e}")
