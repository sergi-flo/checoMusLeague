import os

def get_docker_secrets(secret):
    secret_path = f'/run/secrets/{secret}'
    existence = os.path.exists(secret_path)
    if existence:
        secret_value = open(secret_path).read().rstrip('\n')
        return secret_value
    else:
        print(secret)
        return KeyError(f'{secret}')


if __name__ == "__main__":
    get_docker_secrets("mysql-database")
