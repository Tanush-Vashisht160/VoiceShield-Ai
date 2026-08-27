from config.settings import settings


def main():
    print("=" * 60)
    print("VOICE SECURITY FIREWALL")
    print("=" * 60)
    print(f"Application : {settings.app_name}")
    print(f"Environment : {settings.app_env}")
    print(f"Host        : {settings.host}")
    print(f"Port        : {settings.port}")
    print("=" * 60)
    print("System initialization successful.")
    print("=" * 60)


if __name__ == "__main__":
    main()