import os

def parse_env_file(path):
    """Parses a standardized .env file into a python dictionary."""
    config = {}
    if not os.path.exists(path):
        return config
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            val = val.strip()
            # Strip outer single or double quotes
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            config[key.strip()] = val
    return config

def write_env_file(path, config):
    """Writes a standardised environment variables dictionary to a .env file."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Generated stable-diffusion.cpp profile\n\n")
        for k, v in config.items():
            # Add quotes if the value contains spaces or newlines
            if " " in str(v) or "\n" in str(v):
                f.write(f'{k}="{v}"\n')
            else:
                f.write(f"{k}={v}\n")
