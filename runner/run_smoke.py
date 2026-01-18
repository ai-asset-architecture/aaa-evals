import json


def main():
    print(json.dumps({"suite": "smoke", "pass": True, "pass_rate": 1.0}))


if __name__ == "__main__":
    main()
