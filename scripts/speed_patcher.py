import yaml

file_path = 'config/nav2_params.yaml'
try:
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)

    # Boost Controller Speed and Acceleration
    if 'controller_server' in config:
        config['controller_server']['ros__parameters']['FollowPath']['max_vel_x'] = 5.0
        config['controller_server']['ros__parameters']['FollowPath']['max_accel_x'] = 5.0
        config['controller_server']['ros__parameters']['FollowPath']['max_vel_theta'] = 4.0

    # Boost Velocity Smoother limits
    if 'velocity_smoother' in config:
        config['velocity_smoother']['ros__parameters']['max_velocity'] = [5.0, 0.0, 4.0]
        config['velocity_smoother']['ros__parameters']['max_accel'] = [5.0, 0.0, 4.0]
        
    with open(file_path, 'w') as f:
        yaml.dump(config, f)
    print("SUCCESS: Nav2 parameters have been forced to 5.0 m/s!")
except Exception as e:
    print(f"Error: {e}")
