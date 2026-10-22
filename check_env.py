"""Read this lab's two settings from .env. No extra packages are needed."""

from pathlib import Path


def main():
    env_path = Path(__file__).resolve().with_name(".env")
    if not env_path.is_file():
        raise SystemExit("Missing .env. Create it beside check_env.py.")

    # This reader supports KEY=value and matching outer quotes.
    # Keep comments on separate lines. Each value must fit on one line.
    values = {}
    for number, raw_line in enumerate(env_path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        if not separator or not name.strip():
            raise SystemExit(f"Invalid setting on .env line {number}. Use KEY=value.")
        value = value.strip()
        if value.startswith(("\"", "'")):
            if len(value) < 2 or value[-1] != value[0]:
                raise SystemExit(f"Unclosed quote on .env line {number}.")
            value = value[1:-1]
        values[name.strip()] = value

    api_key = values.get("API_KEY", "")
    user_agent = values.get("SEC_USER_AGENT", "")
    if len(api_key) < 4:
        raise SystemExit("API_KEY must contain at least four characters in .env.")
    if not user_agent.strip():
        raise SystemExit("SEC_USER_AGENT is missing or empty in .env.")

    print(api_key[:4] + "...")
    print(user_agent)


if __name__ == "__main__":
    main()
