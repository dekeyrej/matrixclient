import json
import yaml

def json_to_yaml(json_str):
    """
    Convert a JSON string to a YAML string.

    Parameters:
    json_str (str): A string in JSON format.

    Returns:
    str: A string in YAML format.
    """
    # Parse the JSON string into a Python dictionary
    data = json.loads(json_str)
    
    # Convert the Python dictionary to a YAML string
    yaml_str = yaml.dump(data, sort_keys=False, default_flow_style=False)
    
    return yaml_str

def main(json_file_path, yaml_file_path):
    # Read the JSON string from the specified file
    with open(json_file_path, 'r') as json_file:
        json_str = json_file.read()

    # Convert JSON to YAML
    yaml_str = json_to_yaml(json_str)
    # Write the YAML string to the specified file
    with open(yaml_file_path, 'w') as yaml_file:
        yaml_file.write(yaml_str)

    # Print the resulting YAML string
    print(yaml_str)


if __name__ == "__main__":
    main('static/display_config.txt', 'static/display_config.yaml')